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

        if result is None:
            return True, None

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

        if result is None:
            return True, None

        info = {
            "sender": result.sender,
            "receiver": result.receiver,
            "date": result.confirmed_time,
            "amount": int(result.amount),
            "currency": result.currency,
            "gas": int(result.gas_used),
            "gas_currency": result.gas_currency,
            "type": result.transaction_type,
            "status": result.status
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
