import json
import datetime
from time import time
from abc import abstractmethod
import logging

import firebase_admin
from firebase_admin import credentials
from firebase_admin import auth
from firebase_admin import messaging

from PGHandler import PGHandler

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

    def SetPlatformConfig(self, message, platform):
        if platform == "apple":
            message.apns = messaging.APNSConfig(
                payload=messaging.APNSPayload(
                    aps = messaging.Aps(
                        content_available = True,
                        badge = 1,
                        sound = "default"
                    )
                )
            )
        elif platform == "android":
            message.android = messaging.AndroidConfig(
                ttl = datetime.timedelta(seconds = 3600),
                priority = "normal"
            )
        elif platform == "web":
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

class NotificationMessage(BaseMessage):
    def __init__(self, data, info):
        self.service = data.get("service")
        self.notifiId = data.get("message_id")
        self.content = info.get("content")
        self.date = info.get("date")

    def MakeMessage(self, platform, language):
        message = messaging.Message(
            notification = messaging.Notification(
                title = self.GeneratorTitle(language),
                body = self.GeneratorBody(language)
            ),
            data = self.GeneratorData(),
            topic = f"notification_{language}_{platform}"
        )

        message = self.SetPlatformConfig(message, "all")

        return message

    def GeneratorTitle(self, language):
        return self.content.get(language).get("title")

    def GeneratorBody(self, language):
        return self.content.get(language).get("summary")

    def GeneratorData(self):
        data = {
            "service": self.service,
            "content": self.notifiId,
            "date": str(self.date)
        }

        return data

class TransferSenderMessage(BaseMessage):
    def __init__(self, txnInfo, deviceInfo):
        self.version = txnInfo.get("version")
        self.address = txnInfo.get("receiver")
        self.amount = txnInfo.get("amount")
        self.currency = txnInfo.get("currency")
        self.status = txnInfo.get("status")
        self.txnType = txnInfo.get("type")
        self.token = deviceInfo.get("fcm_token")
        self.language = deviceInfo.get("language").lower()
        self.platform = deviceInfo.get("platform").lower()

    def MakeMessage(self):
        message = messaging.Message(
            notification = messaging.Notification(
                title = self.GeneratorTitle(),
                body = self.GeneratorBody()
            ),
            data = self.GeneratorData(),
            token = self.token
        )

        message = self.SetPlatformConfig(message, self.platform)

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
        status = 0 if self.status == "Executed" else 1
        return f"{self.currency}: {self.amount / 1000000} {self.currency} {titleContent.get(self.language)[status]}"

    def GeneratorBody(self):
        bodyContent = {
            "en": "Receiving address:",
            "cn": "收款地址："
        }

        return f"{bodyContent.get(self.language)} {self.address}"

    def GeneratorData(self):
        data = {
            "service": "violas_01",
            "version": str(self.version),
            "date": str(int(time())),
            "type": self.txnType,
            "status": self.status
        }

        return data

class TransferReceiverMessage(BaseMessage):
    def __init__(self, txnInfo, deviceInfo):
        self.version = txnInfo.get("version")
        self.address = txnInfo.get("sender")
        self.amount = txnInfo.get("amount")
        self.currency = txnInfo.get("currency")
        self.status = txnInfo.get("status")
        self.txnType = txnInfo.get("type")
        self.token = deviceInfo.get("fcm_token")
        self.language = deviceInfo.get("language").lower()
        self.platform = deviceInfo.get("platform").lower()

    def MakeMessage(self):
        message = messaging.Message(
            notification = messaging.Notification(
                title = self.GeneratorTitle(),
                body = self.GeneratorBody()
            ),
            data = self.GeneratorData(),
            token = self.token
        )

        message = self.SetPlatformConfig(message, self.platform)

        return message

    def GeneratorTitle(self):
        titleContent = {
            "en": "successfully received!",
            "cn": "收款成功！"
        }

        return f"{self.currency}: {self.amount / 1000000} {self.currency} {titleContent.get(self.language)}"

    def GeneratorBody(self):
        bodyContent = {
            "en": "Payment address:",
            "cn": "付款地址："
        }

        return f"{bodyContent.get(self.language)} {self.address}"

    def GeneratorData(self):
        data = {
            "service": "violas_01",
            "version": str(self.version),
            "date": str(int(time())),
            "type": self.txnType,
            "status": self.status
        }

        return data

class MultiSignMessage(BaseMessage):
    def __init__(self, data, deviceInfo):
        self.sender = data.get("sender")
        self.address = data.get("address")
        self.token = data.get("token")
        self.signdata = data.get("signdata")
        self.fcmToken = deviceInfo.get("fcm_token")
        self.language = deviceInfo.get("language").lower()
        self.platform = deviceInfo.get("platform").lower()

    def MakeMessage(self):
        message = messaging.Message(
            notification = messaging.Notification(
                title = self.GeneratorTitle(),
                body = self.GeneratorBody()
            ),
            data = self.GeneratorData(),
            token = self.fcmToken
        )

        message = self.SetPlatformConfig(message, self.platform)

        return message

    def GeneratorTitle(self):
        titleContent = {
            "en": "Get multi sign message.",
            "cn": "收到多签消息。"
        }

        return f"{titleContent.get(self.language)}"

    def GeneratorBody(self):
        bodyContent = {
            "en": "Get multi sign message from",
            "cn": "收到多签信息，发送者"
        }

        return f"{bodyContent.get(self.language)} {self.sender}"

    def GeneratorData(self):
        data = {
            "service": "violas_06",
            "sign_data": self.fcmToken,
            "token": self.token
        }

        return data

class FCMWrapper:
    def init(self, cert_path):
        self.cred = credentials.Certificate(cert_path)
        self.app = firebase_admin.initialize_app(self.cred)

    def SendMessage(self, message):
        try:
            response = messaging.send(message)
        except Exception as e:
            logging.error(f"Send message failed, get exception: {e}")
            return None
        return response

    def SendMessages(self, messages):
        for m in messages:
            response = messaging.send(m)

        return

    def SubscribeToTopic(self, topic, token):
        response = messaging.subscribe_to_topic([token], topic)

    def UnsubscribeFromTopic(self, topic, token):
        response = messaging.unsubscribe_from_topic([token], topic)
