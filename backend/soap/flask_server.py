# -*- coding: utf-8 -*-
from flask import Flask, Response, request
from gen import SERVICE
from soapfish.flask_ import flask_dispatcher
import logging
import random
from datetime import datetime
from uuid import uuid4
from flask_flywheel import Flywheel
from dynamo3 import DynamoDBConnection
from flywheel import Model, Field

log = logging.getLogger(__name__)

log.debug("##### MODEL DATA #####")


class User(Model):
    """ Usuários do game """

    id = Field(data_type=str, range_key=True)
    name = Field(data_type=str, nullable=False)
    email = Field(data_type=str, nullable=False, index='email-index')
    facebook_id = Field(data_type=int, nullable=False, hash_key=True)
    facebook_token = Field(data_type=str, nullable=True)
    facebook_data = Field(data_type=dict, nullable=True)
    cpf = Field(data_type=str, nullable=True)
    mobile = Field(data_type=str, nullable=True)
    cep = Field(data_type=str, nullable=True)
    state = Field(data_type=str, nullable=True)
    city = Field(data_type=str, nullable=True)
    optin = Field(data_type=str, nullable=True)
    neighborhood = Field(data_type=str, nullable=True)
    address = Field(data_type=str, nullable=True)
    numb = Field(data_type=str, nullable=True)
    compl = Field(data_type=str, nullable=True)
    media_data = Field(data_type=str, nullable=True)
    firstAccess = Field(data_type=int, default=1)
    created_at = Field(data_type=datetime)
    updated_at = Field(data_type=datetime, nullable=True)
    deleted_at = Field(data_type=datetime, nullable=True, index='create-index')
    referral = Field(data_type=str, default='')
    avatar = Field(data_type=dict, nullable=True)
    win = Field(data_type=dict, nullable=True)
    win_email = Field(data_type=list, nullable=True)
    is_dirty = Field(data_type=bool, default=False)
    is_admin = Field(data_type=int, default=0, index='admin-index')


ws_ops = flask_dispatcher(SERVICE)
app = Flask(__name__)
app.config.from_pyfile("config_prd.cfg")
db = Flywheel(app)

TEMPLATE = '''<?xml version="1.0" encoding="UTF-8"?>
<UsersArray>
  <users>
    <name>{name}</name>
    <email>{email}</email>
    <mobile>{mobile}</mobile>
    <address>{address}</address>
    <cep>{cep}</cep>
    <city>{city}</city>
    <neighborhood>{neighborhood}</neighborhood>
    <numb>{numb}</numb>
  </users>
</UsersArray>
'''

@app.route('/user/GetUserData', methods=['POST'])
def get_data():
    id = request.form['id']
    if id:
        user = db.engine.query(User).filter(facebook_id = int(id)).first()
        if user:
            return Response(TEMPLATE.format(name=user.name,
                                            email=user.email,
                                            mobile=user.mobile,
                                            address=user.address,
                                            cep=user.cep,
                                            city=user.city,
                                            neighborhood=user.neighborhood,
                                            numb=user.numb), mimetype='text/xml')
    return Response(TEMPLATE, mimetype='text/xml')
    

app.add_url_rule('/user', 'user', ws_ops, methods=['GET', 'POST'])






if __name__ == '__main__':
    app.run(host= '0.0.0.0', port=5000)