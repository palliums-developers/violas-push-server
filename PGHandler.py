import logging
import json

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.exc import OperationalError

from Singleton import Singleton
from Modules import *

class PGHandler(Singleton):
    def init(self, dbUrl):
        self.engine = create_engine(dbUrl)
        self.session = sessionmaker(bind = self.engine)

    def GetDeviceInfo(self, address):
        s = self.session()
        try:
            result = s.query(ViolasDeviceInfo).filter(ViolasDeviceInfo.address == address).order_by(ViolasDeviceInfo.id.desc()).first()
        except OperationalError:
            logging.error(f"ERROR: Database operation failed!")
            return False, None
        finally:
            s.close()

        if result is None:
            return True, None

        info = {
            "token": result.token,
            "fcm_token": result.fcm_token,
            "platform": result.platform,
            "language": result.language,
            "location": result.location
        }

        return True, info

    def AddMessageRecord(self, messageId, address, title, body, data):
        s = self.session()
        try:
            record = ViolasMessageRecord(
                message_id = "a_" + messageId,
                address = address,
                title = title,
                body = body,
                data = data,
                readed = 0
            )

            s.add(record)
            s.commit()
        except OperationalError:
            logging.error(f"ERROR: Database operation failed!")
            return False
        finally:
            s.close()

        return True

    def GetNotice(self, noticeId):
        s = self.session()

        try:
            result = s.query(ViolasNoticeRecord).filter(ViolasNoticeRecord.message_id == noticeId).first()
            deviceInfo = s.query(ViolasDeviceInfo)
        except OperationalError:
            logging.error(f"ERROR: Database operation failed!")
            return False, None
        finally:
            s.close()

        content = json.loads(result.content, )
        platform = json.loads(result.platform, )
        info = {
            "content": content,
            "platform": platform,
            "date": result.date
        }

        return True, info
