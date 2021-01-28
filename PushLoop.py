from threading import Thread
import logging
from time import sleep
import json

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
        succ, info = pgHandler.GetNotification(data.get("content"))
        if not succ:
            self.queue.AddMessage(data)
            return

        if info is None:
            return

        fcm = FCMWrapper()

        message = NotificationMessage(data, info)

        fcm.SendMessage(message.MakeMessage())

        return

    def SendTransferMessage(self, data):
        fcm = FCMWrapper()

        # txnInfo = '''{"version": 7735110, "sender": "e8da60ef0f4cf18c324527f48b06c7e9", "receiver": "6c1dd50f35f120061babc2814cf9378b", "date": 1611027076, "amount": 1000000, "currency": "VLS", "gas": 511, "gas_currency": "VLS", "type": "PEER_TO_PEER_WITH_METADATA", "status": "Executed"}'''
        # txnInfo = json.loads(txnInfo)

        # deviceInfo = '''{"token": "dIB2qMGm803WqI9WQrx1Yi:APA91bFOqVH10ERscLSTJRQ6Pf8rtQsoNiSBv6pcjTMvgJ6zd8k90WQZTX9qKcL3ZM6AIQmp0JfpF-OvYfuDA7_B1hKj8C_QXtum_qq7soht0s5w5dj8IfSVXoYT037K-BbY5dccyD7-", "device_type": "apple", "language": "en"}'''
        # deviceInfo = json.loads(deviceInfo)

        # message = TransferReceiverMessage(txnInfo, deviceInfo)

        # response = fcm.SendMessage(message.MakeMessage())
        # print(response)

        # continue

        pgHandler = PGHandler()
        succ, txnInfo = pgHandler.GetTransactionInfo(data.content)
        if not succ or txnInfo is None:
            self.queue.AddMessage(data)
            return

        logging.debug(f"Prepare for send message to sender!")
        succ, deviceInfo = pgHandler.GetDeviceInfo(txnInfo.get("sender"))
        if not succ:
            self.queue.AddMessage(data)
            return

        if deviceInfo is not None:
            logging.debug(f"Send notifiaction to sender: {txnInfo.get('sender')}")
            message = TransferSenderMessage(txnInfo, deviceInfo)
            pgHandler.AddMessageRecord(data.content, txnInfo.get("sender"), message.GeneratorTitle(), message.GeneratorBody(), json.dumps(message.GeneratorData()))
            response = fcm.SendMessage(message.MakeMessage())
            logging.debug(f"The response of send to sender: {response}")

        logging.debug(f"Prepare for send message to receiver!")
        if txnInfo.get("status") == "Executed":
            succ, deviceInfo = pgHandler.GetDeviceInfo(txnInfo.get("receiver"))
            if not succ or deviceInfo is None:
                return

            logging.debug(f"Send notifiaction to receiver: {txnInfo.get('receiver')}")
            # logging.debug(f"txnInfo:{txnInfo}, deviceInfo:{deviceInfo}")
            message = TransferReceiverMessage(txnInfo, deviceInfo)
            # logging.debug(f"{data.content}, {txnInfo.get('receiver')}, {message.GeneratorTitle()}, {message.GeneratorBody()}, {json.dumps(message.GeneratorData())}")
            pgHandler.AddMessageRecord(data.content,
                                       txnInfo.get("receiver"),
                                       message.GeneratorTitle(),
                                       message.GeneratorBody(),
                                       json.dumps(message.GeneratorData()))
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

            if data.get("service") == "service_00":
                self.SendNotification(data)
            elif data.get("service") == "service_01":
                self.SendTransferMessage(data)
            else:
                logging.error(f"Unknow data type!")
                continue

        logging.debug(f"Push loop thread end, thread name {self.getName()}")
