from sqlalchemy import Column, ForeignKey, Integer, String, DateTime, MetaData
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship

Base = declarative_base()


class DefaultBase(Base):
    __abstract__ = True
    metadata = MetaData()


class Config(DefaultBase):
    __tablename__ = 'config'
    id = Column(Integer, primary_key=True)
    key = Column(String(255), nullable=False)
    value = Column(String(255), nullable=False)


class Tunnel(DefaultBase):
    __tablename__ = 'tunnel'
    id = Column(Integer, primary_key=True)
    partner_id = Column(Integer, nullable=False)
    parent_id = Column(Integer, ForeignKey('tunnel.id'))
    parent = relationship("Tunnel", remote_side=[id])
    group_id = Column(Integer, nullable=True)
    key = Column(String(32), nullable=False)
    tps_min = Column(Integer, nullable=True)
    tps_max = Column(Integer, nullable=True)
    priority = Column(Integer, nullable=False)
    url = Column(String(250), nullable=True)


class User(DefaultBase):
    __tablename__ = 'user'
    id = Column(Integer, primary_key=True)
    key = Column(String(32), nullable=False)
    secret = Column(String(32), nullable=False)


class UserLa(DefaultBase):
    __tablename__ = 'user_la'
    id = Column(Integer, primary_key=True)
    user = Column('user_id', Integer, ForeignKey('user.id'), nullable=False)
    la = Column(Integer, nullable=False)


class UserTunnel(DefaultBase):
    __tablename__ = 'user_tunnel'
    id = Column(Integer, primary_key=True)
    user = Column('user_id', Integer, ForeignKey('user.id'), nullable=False)
    tunnel = Column('tunnel_id', Integer, ForeignKey('tunnel.id'), nullable=False)


class Partner(DefaultBase):
    __tablename__ = 'partner'
    id = Column(Integer, primary_key=True)
    name = Column(String(45), nullable=False)


class Request(DefaultBase):
    __tablename__ = 'request'
    id = Column(Integer, primary_key=True)
    url = Column(String)
    header = Column(String)
    body = Column(String)
    etl = Column(Integer, default=0)
    created_at = Column(DateTime, default=func.now())


class EtlTimV1Recharge(DefaultBase):
    __tablename__ = 'etl_tim_v1_recharge'
    id = Column(Integer, primary_key=True)
    event_id = Column(String)
    msisdn = Column(String)
    partner_id = Column(String)
    value = Column(String)
    date = Column(String)
    time = Column(String)
    tariff_id = Column(String)
    subsys = Column(String)
    created_at = Column(DateTime, default=func.now())


class Prebilling(DefaultBase):
    __tablename__ = 'prebilling'
    id = Column(Integer, primary_key=True)
    partner = Column('partner_id', Integer, ForeignKey('partner.id'), nullable=False)
    product = Column(String(50))
    periodicity = Column(Integer)
    name = Column(String(255))
