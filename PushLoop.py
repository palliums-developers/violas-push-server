from threading import Thread
import logging
from time import sleep
import json
import hashlib

from MessagePushQueue import MessagePushQueue
from PGHandler import PGHandler
from FCMWrapper import FCMWrapper, TransferSenderMessage, TransferReceiverMessage, NotificationMessage
import Common

class PushLoop(Thread):
    def __init__(self):
        super().__init__()
        self.queue = MessagePushQueue()

    def SendNotification(self, data):
        pgHandler = PGHandler()
        succ, noticeInfo = pgHandler.GetNotice(data.get("message_id"))
        if not succ:
            self.queue.AddMessage(data)
            return

        if noticeInfo is None:
            return

        fcm = FCMWrapper()

        message = NotificationMessage(data, noticeInfo)

        for p in noticeInfo.get("platform"):
            for l in noticeInfo.get("content").keys():
                fcm.SendMessage(message.MakeMessage(p, l))

        return

    def SendTransferMessage(self, data):
        fcm = FCMWrapper()

        pgHandler = PGHandler()
        succ, txnInfo = pgHandler.GetTransactionInfo(data.get("version"))
        if not succ or txnInfo is None:
            self.queue.AddMessage(data)
            return
        logging.debug(f"Get transaction info: {txnInfo}!")

        succ, deviceInfo = pgHandler.GetDeviceInfo(txnInfo.get("sender"))
        if not succ:
            self.queue.AddMessage(data)
            return
        logging.debug(f"Get sender device info: {deviceInfo}")

        if deviceInfo is not None:
            logging.debug(f"Send notifiaction to sender: {txnInfo.get('sender')}")
            message = TransferSenderMessage(txnInfo, deviceInfo)
            messageId = hashlib.md5(f"{message.GeneratorTitle()}:{message.GeneratorBody()}".encode()).hexdigest()

            pgHandler.AddMessageRecord(
                messageId,
                txnInfo.get("sender"),
                message.GeneratorTitle(),
                message.GeneratorBody(),
                json.dumps(message.GeneratorData())
            )
            response = fcm.SendMessage(message.MakeMessage())
            logging.debug(f"The response of send to sender: {response}")

        logging.debug(f"Prepare for send message to receiver!")

        if txnInfo.get("status") == "Executed":
            succ, deviceInfo = pgHandler.GetDeviceInfo(txnInfo.get("receiver"))
            if not succ or deviceInfo is None:
                return
            logging.debug(f"Get receiver device info: {deviceInfo}")

            logging.debug(f"Send notifiaction to receiver: {txnInfo.get('receiver')}")
            # logging.debug(f"txnInfo:{txnInfo}, deviceInfo:{deviceInfo}")
            message = TransferReceiverMessage(txnInfo, deviceInfo)
            # logging.debug(f"{data.content}, {txnInfo.get('receiver')}, {message.GeneratorTitle()}, {message.GeneratorBody()}, {json.dumps(message.GeneratorData())}")
            messageId = hashlib.md5(f"{message.GeneratorTitle()}:{message.GeneratorBody()}".encode()).hexdigest()
            pgHandler.AddMessageRecord(
                messageId,
                txnInfo.get("receiver"),
                message.GeneratorTitle(),
                message.GeneratorBody(),
                json.dumps(message.GeneratorData())
            )
            response = fcm.SendMessage(message.MakeMessage())
            logging.debug(f"The response of send to receiver: {response} ")

        return

    def run(self):
        logging.debug(f"Push loop thread start, thread name {self.getName()}.")

        aliveCount = 0
        while True:
            aliveCount += 1
            if aliveCount == 500:
                aliveCount = 0
                logging.debug(f"PushLoop thread is alive, thread name {self.getName()}!")

            data = self.queue.PopMessage()
            if data is None:
                sleep(1 / 1000 * 500)
                continue

            if data.get("service") == "violas_00":
                self.SendNotification(data)
            elif data.get("service") == "violas_01":
                self.SendTransferMessage(data)
            else:
                logging.error(f"Unknow data type!")
                continue

        logging.debug(f"Push loop thread end, thread name {self.getName()}")
