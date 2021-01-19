import datetime
from abc import abstractmethod

import firebase_admin
from firebase_admin import credentials
from firebase_admin import auth
from firebase_admin import messaging

# cred = credentials.Certificate("./fcm-test-project-93d7f-firebase-adminsdk-1hb7h-11daf4862e.json")
# default_app = firebase_admin.initialize_app(cred)

class BaseMessage:
    @abstractmethod
    def MakeMessage(self):
        pass

    @abstractmethod
    def GeneratorTitle(self):
        pass

    @abstractmethod
    def GeneratorBody(self):
        pass

    @abstractmethod
    def GeneratorData(self):
        pass

    def SetDeviceConfig(self, message, deviceType):
        if deviceType == "apple":
            message.apns = messaging.APNSConfig(
                payload=messaging.APNSPayload(
                    aps = messaging.Aps(
                        content_available = True,
                        badge = 1,
                        sound = "default"
                    )
                )
            )
        elif deviceType == "android":
            message.android = messaging.AndroidConfig(
                ttl = datetime.timedelta(seconds = 3600),
                priority = "normal"
            )
        elif deviceType == "web":
            message.webpush = messaging.WebpushConfig()
        else:
            message.apns = messaging.APNSConfig(
                payload=messaging.APNSPayload(
                    aps = messaging.Aps(
                        content_available = True,
                        badge = 1,
                        sound = "default"
                    )
                )
            )

            message.android = messaging.AndroidConfig(
                ttl = datetime.timedelta(seconds = 3600),
                priority = "normal"
            )

            message.webpush = messaging.WebpushConfig()

        return message

class TransferSenderMessage(BaseMessage):
    def __init__(self, txnInfo, deviceInfo):
        self.version = txnInfo.get("version")
        self.address = txnInfo.get("sender")
        self.amount = txnInfo.get("amount")
        self.currency = txnInfo.get("currency")
        self.status = 0 if txnInfo.get("status") == "Executed" else 1
        self.token = deviceInfo.get("token")
        self.language = deviceInfo.get("language").lower()
        self.deviceType = deviceInfo.get("device_type").lower()
        return

    def MakeMessage(self):
        message = messaging.Message(
            notification = messaging.Notification(
                title = self.GeneratorTitle(),
                body = self.GeneratorBody()
            ),
            data = self.GeneratorData(),
            token = self.token
        )

        message = self.SetDeviceConfig(message, self.deviceType)

        return message

    def GeneratorTitle(self):
        titleContent = {
            "en": [
                "transfer success!",
                "transfer failed!"
            ],
            "cn": [
                "转帐成功！",
                "转帐失败！"
            ]
        }

        return f"{self.currency}: {self.amount} {self.currency} {titleContent.get(self.language)[self.status]}"

    def GeneratorBody(self):
        bodyContent = {
            "en": "Receiving address:",
            "cn": "收款地址："
        }

        return f"{bodyContent.get(self.language)} {self.address}"

    def GeneratorData(self):
        data = {
            "service": "violas_01",
            "content": str(self.version)
        }

        return data

class TransferReceiverMessage(BaseMessage):
    def __init__(self, txnInfo, deviceInfo):
        self.version = txnInfo.get("version")
        self.address = txnInfo.get("receiver")
        self.amount = txnInfo.get("amount")
        self.currency = txnInfo.get("currency")
        self.status = 0 if txnInfo.get("status") == "Executed" else 1
        self.token = deviceInfo.get("token")
        self.language = deviceInfo.get("language").lower()
        self.deviceType = deviceInfo.get("device_type").lower()
        return 

    def MakeMessage(self):
        message = messaging.Message(
            notification = messaging.Notification(
                title = self.GeneratorTitle(),
                body = self.GeneratorBody()
            ),
            data = self.GeneratorData(),
            token = self.token
        )

        message = self.SetDeviceConfig(message, self.deviceType)

        return message

    def GeneratorTitle(self):
        titleContent = {
            "en": "successfully received!",
            "cn": "收款成功！"
        }

        return f"{self.currency}: {self.amount} {self.currency} {titleContent.get(self.language)}"

    def GeneratorBody(self, address, language):
        bodyContent = {
            "en": "Payment address:",
            "cn": "发款地址："
        }

        return f"{bodyContent.get(self.language)} {address}"

    def GeneratorData(self):
        data = {
            "service": "violas_01",
            "content": str(self.version)
        }

        return data

class FCMWrapper:
    def __init__(self, cert_path):
        self.cred = credentials.Certificate(cert_path)
        self.app = firebase_admin.initialize_app(self.cred)

    def SendMessage(self, message):
        response = messaging.send(message)
        return response

    def SendMessages(self, messages):
        for m in messages:
            response = messaging.send(m)

        return

    def SubscribeToTopic(self, topic, token):
        response = messaging.subscribe_to_topic([token], topic)

    def UnsubscribeFromTopic(self, topic, token):
        response = messaging.unsubscribe_from_topic([token], topic)
