from threading import Thread
import logging
from time import sleep
import json

from MessagePushQueue import MessagePushQueue
from PGHandler import PGHandler
from FCMWrapper import FCMWrapper, TransferSenderMessage, TransferReceiverMessage
import Common

class PushLoop(Thread):
    def __init__(self):
        super().__init__()
        self.queue = MessagePushQueue()

    def run(self):
        logging.debug(f"Push loop thread start, thread name {self.getName()}.")

        aliveCount = 0
        while True:
            aliveCount += 1
            if aliveCount == 500:
                aliveCount = 0
                logging.debug(f"PushLoop thread is alive, thread name {self.getName()}!")

            version = self.queue.PopMessage()
            if version is None:
                sleep(1 / 1000 * 500)
                continue

            fcm = FCMWrapper()
            pgHandler = PGHandler()
            succ, txnInfo = pgHandler.GetTransactionInfo(version)
            if not succ or txnInfo is None:
                self.queue.AddMessage(version)
                continue

            logging.debug(f"Prepare for send message to sender!")
            succ, deviceInfo = pgHandler.GetDeviceInfo(txnInfo.get("sender"))
            if not succ:
                self.queue.AddMessage(version)
                continue

            if deviceInfo is not None:
                logging.debug(f"Send notifiaction to sender: {txnInfo.get('sender')}")
                message = TransferSenderMessage(txnInfo, deviceInfo)
                pgHandler.AddMessageRecord(version, txnInfo.get("sender"), message.GeneratorTitle(), message.GeneratorBody(), json.dumps(message.GeneratorData()))
                response = fcm.SendMessage(message.MakeMessage())
                logging.debug(f"The response of send to sender: {response}")

            logging.debug(f"Prepare for send message to receiver!")
            if txnInfo.get("status") == "Executed":
                succ, deviceInfo = pgHandler.GetDeviceInfo(txnInfo.get("receiver"))
                if not succ or deviceInfo is None:
                    continue

                logging.debug(f"Send notifiaction to receiver: {txnInfo.get('receiver')}")
                logging.debug(f"txnInfo:{txnInfo}, deviceInfo:{deviceInfo}")
                message = TransferReceiverMessage(txnInfo, deviceInfo)
                logging.debug(f"{version}, {txnInfo.get('receiver')}, {message.GeneratorTitle()}, {message.GeneratorBody()}, {json.dumps(message.GeneratorData())}")
                pgHandler.AddMessageRecord(version, txnInfo.get("receiver"), message.GeneratorTitle(), message.GeneratorBody(), json.dumps(message.GeneratorData()))
                response = fcm.SendMessage(message.MakeMessage())
                logging.debug(f"The response of send to receiver: {response} ")

        logging.debug(f"Push loop thread end, thread name {self.getName()}")
