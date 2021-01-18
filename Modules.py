from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import Column, SmallInteger, Integer, BigInteger, String, Numeric, Boolean, Text, Index

Base = declarative_base()


class ViolasTransaction(Base):
    __tablename__ = "transactions"

    id = Column(BigInteger, primary_key = True, autoincrement = True)
    sequence_number = Column(Integer, nullable = True)
    sender = Column(String(64), nullable = True)
    receiver = Column(String(64), nullable = True)
    currency = Column(String(16), nullable = True)
    gas_currency = Column(String(16), nullable = True)
    amount = Column(Numeric, nullable = True)
    gas_used = Column(Numeric, nullable = True)
    gas_unit_price = Column(Numeric, nullable = True)
    max_gas_amount = Column(Numeric, nullable = True)
    expiration_time = Column(Integer, nullable = True)
    transaction_type = Column(String(64), nullable = True)
    data = Column(Text(), nullable = True)
    public_key = Column(Text(), nullable = True)
    script_hash = Column(String(64), nullable = True)
    signature = Column(Text(), nullable = True)
    signature_scheme = Column(String(32), nullable = True)
    status = Column(SmallInteger, nullable = True)
    event = Column(Text(), nullable = True)
    confirmed_time = Column(Integer, nullable = True)

class ViolasDeviceInfo(Base):
    __tablename__ = "device_info"

    id = Column(BigInteger, primary_key = True, autoincrement = True)
    address = Column(String(64), nullable = False)
    device_type = Column(String(16), nullable = False)
    token = Column(Text, nullable = False)
    language = Column(String(32), nullable = False)
    location = Column(String(32), nullable = True)

class ViolasMessageRecord(Base):
    __tablename__ = "message_record"

    id = Column(BigInteger, primary_key = True, autoincrement = True)
    version = Column(BigInteger, nullable = False)
    sender = Column(String(64), nullable = False)
    title = Column(Text, nullable = False)
    body = Column(Text, nullable = False)
    data = Column(Text, nullable = False)
    readed = Column(SmallInteger, nullable = False) # 0: unread; 1: readed
