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
        Thread.__init__(self)
        self.queue = MessagePushQueue()

    def run(self):
        logging.debug(f"Push loop thread start, thread name {self.getName()}.")

        aliveCount = 0
        while True:
            aliveCount += 1
            if aliveCount == 500:
                aliveCount = 0
                logging.debug("PushLoop thread is alive!")

            version = self.queue.PopMessage()
            if version is None:
                sleep(1 / 1000 * 500)
                continue

            pgHandler = PGHandler()
            succ, txnInfo = pgHandler.GetTransactionInfo(version)
            if not succ or txnInfo is None:
                self.queue.AddMessage(version)
                continue

            succ, deviceInfo = pgHandler.GetDeviceInfo(txnInfo.sender)
            if not succ:
                self.queue.AddMessage(version)
                continue

            if deviceInfo is not None:
                fcm = FCMWrapper(Common.CERT_PATH)

                message = TransferSenderMessage(txnInfo, deviceInfo)
                pgHandler.AddMessageRecord(version, txnInfo.get("sender"), message.GeneratorTitle(), message.GeneratorBody(), json.dumps(message.GeneratorData()))
                fcm.SendMessage(message)

            if txnInfo.status == "Executed":
                succ, deviceInfo = pgHandler.GetDeviceInfo(txnInfo.receiver)
                if not succ or deviceInfo is None:
                    continue

                message = TransferReceiverMessage(txnInfo, deviceInfo)
                pgHandler.AddMessageRecord(version, txnInfo.get("receiver"), message.GeneratorTitle(), message.GeneratorBody(), json.dumps(message.GeneratorData()))
                fcm.SendMessage(message)

        logging.debug(f"Push loop thread end, thread name {self.getName()}")
