# -*- coding: utf-8 -*-
import uuid
import datetime

from flask import Flask
from flask.ext.sqlalchemy import SQLAlchemy
import configobj
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import or_

config = configobj.ConfigObj('config.ini')
crateconf = config['crate']

shards = crateconf['shards']
replicas = crateconf['replicas']

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = '%s%s:%s' % (crateconf['protocol'], crateconf['host'], crateconf['port'])

db = SQLAlchemy(app)


class CnlTmp(db.Model):
    """CNL information //sistemas.anatel.gov.br/areaarea/N_Download/Tela.asp"""
    __tablename__ = 'cnltmp'
    __table_args__ = {'crate_number_of_replicas': replicas,
                      'crate_number_of_shards': shards}

    id = db.Column(db.String, default=lambda: str(uuid.uuid4()), primary_key=True)
    uf = db.Column(db.String(2))
    cnl = db.Column(db.String(4))
    cnl_cod = db.Column(db.String(5))
    place = db.Column(db.String(50))
    province = db.Column(db.String(50))
    tarifation_cod = db.Column(db.String(5))
    prefix = db.Column(db.String(5))
    operator = db.Column(db.String)
    initial_phone = db.Column(db.Integer())
    final_phone = db.Column(db.Integer())
    geoposition = db.Column(db.String, default=[])
    cnl_local_area_cod = db.Column(db.String(4))
    ddd = db.Column(db.Integer)
    operator_id = db.Column(db.String)
    # Foreign key from Operator table
    is_mobile = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime(), default=lambda: datetime.datetime.now())


class Cnl(db.Model):
    """CNL information //sistemas.anatel.gov.br/areaarea/N_Download/Tela.asp"""
    __tablename__ = 'cnl'
    __table_args__ = {'crate_number_of_replicas': replicas,
                      'crate_number_of_shards': shards}

    id = db.Column(db.String, default=lambda: str(uuid.uuid4()), primary_key=True)
    uf = db.Column(db.String(2))
    cnl = db.Column(db.String(4))
    cnl_cod = db.Column(db.String(5))
    place = db.Column(db.String(50))
    province = db.Column(db.String(50))
    tarifation_cod = db.Column(db.String(5))
    prefix = db.Column(db.String(5))
    operator = db.Column(db.String)
    initial_phone = db.Column(db.Integer())
    final_phone = db.Column(db.Integer())
    geoposition = db.Column(db.String, default=[])
    cnl_local_area_cod = db.Column(db.String(4))
    ddd = db.Column(db.Integer)
    operator_id = db.Column(db.String)
    # Foreign key from Operator table
    is_mobile = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime(), default=lambda: datetime.datetime.now())


class Operator(db.Model):
    """Brasilian phone operators"""
    __tablename__ = 'operator'
    __table_args__ = {'crate_number_of_replicas': replicas,
                      'crate_number_of_shards': shards}
    id = db.Column(db.String, default=lambda: str(uuid.uuid4()), primary_key=True)
    name = db.Column(db.String(50))
    img_translate = db.Column(db.String(15))


class Ddd(db.Model):
    """ddd listing and geographoc states"""
    __tablename__ = 'ddd'
    __table_args__ = {'crate_number_of_replicas': replicas,
                      'crate_number_of_shards': shards}
    id = db.Column(db.Integer(), primary_key=True)
    state = db.Column(db.String(2))


class Phone(db.Model):
    """transfered and already searched phones"""
    __tablename__ = 'phone'
    __table_args__ = {'crate_number_of_replicas': replicas,
                      'crate_number_of_shards': shards}
    id = db.Column(db.Integer(), primary_key=True)
    operator = db.Column(db.String)
    # Foreign key from Operator table
    portability_id = db.Column(db.Integer)
    portability_type = db.Column(db.Integer)
    action = db.Column(db.Integer)
    new_spid = db.Column(db.Integer)
    eot = db.Column(db.String(5))
    is_mobile = db.Column(db.Boolean, default=True)
    activation_time = db.Column(db.DateTime)
    start_time = db.Column(db.DateTime)
    created_at = db.Column(db.DateTime)
    updated_at = db.Column(db.DateTime)


class Header(db.Model):
    """
    file name update convension
    """

    __tablename__ = 'header'
    __table_args__ = {'crate_number_of_replicas': replicas,
                      'crate_number_of_shards': shards}
    id = db.Column(db.String, default=lambda: str(uuid.uuid4()), primary_key=True)
    generated = db.Column(db.DateTime())
    number_of_items = db.Column(db.Integer)


class TranslateOperator(db.Model):
    """
    abr site translation for normatized operators 
    """
    __tablename__ = 'translateoperator'
    __table_args__ = {'crate_number_of_replicas': replicas,
                      'crate_number_of_shards': shards}
    id = db.Column(db.String, primary_key=True)
    name = db.Column(db.String)
    rn1 = db.Column(db.String)
    operator = db.Column(db.String)
    # Foreign key from Operator table
    created_at = db.Column(db.DateTime(), default=datetime.datetime.now())


# def create_tables(engine, conn):
#
#     if not engine.dialect.has_table(conn, table_name=cnl):
#         Cnl.metadata.create
