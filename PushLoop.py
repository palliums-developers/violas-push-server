from threading import Thread
import logging
from time import sleep, time
import json
import hashlib

from MessagePushQueue import MessagePushQueue
from PGHandler import PGHandler
from FCMWrapper import FCMWrapper, TransferSenderMessage, TransferReceiverMessage, NotificationMessage, MultiSignMessage
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
        succ, deviceInfo = pgHandler.GetDeviceInfo(data.get("sender"))
        if not succ:
            self.queue.AddMessage(data)
            return
        logging.debug(f"Get sender device info: {deviceInfo}")

        if deviceInfo:
            logging.debug(f"Send notifiaction to sender: {data.get('sender')}")
            message = TransferSenderMessage(data, deviceInfo)
            messageId = hashlib.md5(f"{data.get('version')}:{message.GeneratorTitle()}:{message.GeneratorBody()}".encode()).hexdigest()

            pgHandler.AddMessageRecord(
                messageId,
                data.get("sender"),
                message.GeneratorTitle(),
                message.GeneratorBody(),
                json.dumps(message.GeneratorData())
            )
            response = fcm.SendMessage(message.MakeMessage())
            logging.debug(f"The response of send to sender: {response}")

        logging.debug(f"Prepare for send message to receiver!")

        if data.get("status") == "Executed":
            succ, deviceInfo = pgHandler.GetDeviceInfo(data.get("receiver"))
            if not succ or deviceInfo is None:
                return
            logging.debug(f"Get receiver device info: {deviceInfo}")

            logging.debug(f"Send notifiaction to receiver: {data.get('receiver')}")
            # logging.debug(f"data:{data}, deviceInfo:{deviceInfo}")
            message = TransferReceiverMessage(data, deviceInfo)
            # logging.debug(f"{data.content}, {data.get('receiver')}, {message.GeneratorTitle()}, {message.GeneratorBody()}, {json.dumps(message.GeneratorData())}")
            messageId = hashlib.md5(f"{data.get('version')}:{message.GeneratorTitle()}:{message.GeneratorBody()}".encode()).hexdigest()
            pgHandler.AddMessageRecord(
                messageId,
                data.get("receiver"),
                message.GeneratorTitle(),
                message.GeneratorBody(),
                json.dumps(message.GeneratorData())
            )
            response = fcm.SendMessage(message.MakeMessage())
            logging.debug(f"The response of send to receiver: {response} ")

        return

    def SendMultiSignMessage(self, data):
        pgHandler = PGHandler()
        succ, deviceInfo = pgHandler.GetDeviceInfo(data.get("address"))
        if not succ:
            self.queue.AddMessage(data)
            return
        logging.debug(f"Get device info: {deviceInfo}")

        if deviceInfo:
            logging.debug(f"Send multisign message to device: {data.get('address')}")
            message = MultiSignMessage(data, deviceInfo)

            fcm = FCMWrapper()
            response = fcm.SendMessage(message.MakeMessage())
            logging.debug(f"The response of send to receiver: {response}")

            messageId = hashlib.md5(f"{time()}:{message.GeneratorTitle()}:{message.GeneratorBody()}".encode()).hexdigest()
            pgHandler.AddMessageRecord(
                messageId,
                data.get("address"),
                message.GeneratorTitle(),
                message.GeneratorBody(),
                json.dumps(message.GeneratorData())
            )
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
            elif data.get("service") == "violas_06":
                self.SendMultiSignMessage(data)
            else:
                logging.error(f"Unknow data type!")
                continue

        logging.debug(f"Push loop thread end, thread name {self.getName()}")
