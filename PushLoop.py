from threading import Thread
import logging
from time import sleep

from MessagePushQueue import MessagePushQueue
from PGHandler import PGHandler
from FCMWrapper import FCMWrapper, TransferSenderMessage, TransferReceiverMessage
import Common

class PushLoop(Thread):
    def __init__(self):
        super().__init__()
        self.queue = MessagePushQueue()

    def run(self):
        logging.debug(f"Push loop thread start.")

        while True:
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

            if deviceInfo is None:
                continue

            message = TransferSenderMessage(txnInfo, deviceInfo)
            fcm = FCMWrapper(Common.CERT_PATH)
            fcm.SendMessage(message)

            if txnInfo.status == "Executed":
                succ, deviceInfo = pgHandler.GetDeviceInfo(txnInfo.receiver)
                if not succ or deviceInfo is None:
                    continue

                message = TransferReceiverMessage(txnInfo, deviceInfo)
                fcm.SendMessage(message)
