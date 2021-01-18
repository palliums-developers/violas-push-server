import logging

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.exc import OperationalError

from Singleton import Singleton
from Modules import ViolasDeviceInfo, ViolasMessageRecord, ViolasTransaction

class PGHandler(Singleton):
    def init(self, dbUrl):
        self.engine = create_engine(dbUrl)
        self.session = sessionmaker(bind = self.engine)

    def GetDeviceInfo(self, address):
        s = self.session()
        try:
            result = s.query(ViolasDeviceInfo).filter(ViolasDeviceInfo.address == address).first()
        except OperationalError:
            logging.error(f"ERROR: Database operation failed!")
            return False, None
        finally:
            s.close()

        info = {
            "token": result.token,
            "device_type": result.device_type,
            "language": result.language,
            "location": result.location
        }

        return True, info

    def GetTransactionInfo(self, version):
        s = self.session()
        try:
            result = s.query(ViolasTransaction).filter(ViolasTransaction.id == version + 1).first()
        except OperationalError:
            logging.error(f"ERROR: Database operation failed!")
            return False, None
        finally:
            s.close()

        info = {
            "sender": info.sender,
            "receiver": info.receiver,
            "date": info.confirmed_time,
            "amount": info.amount,
            "currency": info.currency,
            "gas": info.gas_used,
            "gas_currency": info.gas_currency,
            "type": info.transaction_type,
            "status": info.status
        }

        return True, info

    def AddMessageRecord(self, version, address, title, body, data):
        s = self.session()
        try:
            record = ViolasMessageRecord(
                version = version,
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
