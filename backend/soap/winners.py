# -*- coding: utf-8 -*-
import csv
import logging
from datetime import datetime
from io import StringIO

from flask import Flask, make_response
from flask_flywheel import Flywheel
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


class ReferralUser(Model):
    """ Vidas ganhas por por login do facebok """

    user_id = Field(data_type=str, nullable=False, range_key=True)
    refered_id = Field(data_type=str, hash_key=True)
    face_data = Field(data_type=dict, nullable=False)
    life = Field(data_type=int, default=0, index=True)
    created_at = Field(data_type=datetime, index='created_at', nullable=True)
    updated_at = Field(data_type=datetime, nullable=True)


class ReferralRequest(Model):
    """ Token exclusivo de compartilhamento """

    user_id = Field(data_type=str, range_key=True)
    id = Field(data_type=str, hash_key=True, nullable=False)
    created_at = Field(data_type=datetime, index='create-index')
    updated_at = Field(data_type=datetime, nullable=True)

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




@app.route('/win', methods=['GET'])
def get_data():
    user = db.engine.scan(User).filter(User.id != None).gen()
    si = StringIO()
    cw = csv.writer(si, delimiter=',', quotechar = '"')

    tmp = [
        ('id', 'fbid', 'name', 'cpf', 'email', 'prize')]
    for u in user:
        tmp.append((u.id,
                    u.facebook_id,
                    u.name,
                    u.cpf,
                    u.email,
                    u.mobile,
                    u.address,
                    u.cep,
                    u.city,
                    u.neighborhood,
                    u.numb,
                    u.compl,
                    [(i.get('level'), i.get('now')[:10]) for i in u.win.values()]))
    cw.writerows(tmp)
    output = make_response(si.getvalue())
    output.headers["Content-Disposition"] = "attachment; filename=export.csv"
    output.headers["Content-type"] = "text/csv"
    return output


@app.route('/elastic', methods=['GET'])
def get_data():
    user = db.engine.scan(User).filter(User.id != None).gen()

    names = ["created_at", "avatarbig", "avatarsmall", "email", "age_range_min", "age_range_max", "faceemail", "first_name", "gender", "last_name", "link", "locale", "fullname", "picture",
         "is_silhouette", "facebook_id", "firstAccess", "id", "is_admin", "is_dirty", "name", "referral", "updated_at",
         'cpf', 'email', 'mobile', 'address', 'cep', 'city', 'neighborhood', 'number', 'complemento', 'easy', 'medium', 'hard', 'impossible']


    for u in user:
        wins = dict([(i.get('level'), '|'.join(i.get('reward'))) for i in u.win.values()])
        yield dict(zip(names, [u.created_at,
                    u.avatar.get('big'),
                    u.avatar.get('small'),
                    u.facebook_data.get('age_range', {}).get('min', 0),
                    u.facebook_data.get('age_range', {}).get('max', 0),
                    u.facebook_data.get('email', ''),
                    u.facebook_data.get('first_name', ''),
                    u.facebook_data.get('gender', ''),
                    u.facebook_data.get('last_name', ''),
                    u.facebook_data.get('link˚', ''),
                    u.facebook_data.get('locale˚', ''),
                    u.facebook_data.get('name˚', ''),
                    u.facebook_data.get('picture˚', {}).get('url', ''),
                    u.facebook_data.get('is_silhouette˚', ''),
                    u.facebook_id,
                    u.firstAccess,
                    u.id,
                    u.is_admin,
                    u.is_dirty,
                    u.name,
                    u.referral,
                    u.updated_at,
                    u.cpf,
                    u.email,
                    u.mobile,
                    u.address,
                    u.cep,
                    u.city,
                    u.neighborhood,
                    u.numb,
                    u.compl,
                    wins.get('easy', ''),
                    wins.get('medium', ''),
                    wins.get('hard', ''),
                    wins.get('impossible', '')
                    ]))
    cw.writerows(tmp)
    output = make_response(si.getvalue())
    output.headers["Content-Disposition"] = "attachment; filename=elastic.csv"
    output.headers["Content-type"] = "text/csv"
    return output


@app.route('/win', methods=['GET'])
def get_data():
    user = db.engine.scan(User).filter(User.win != None).gen()
    si = StringIO()
    cw = csv.writer(si, delimiter=',', quotechar = '"')

    tmp = [
        ('id', 'fbid', 'name', 'cpf', 'email', 'mobile', 'address', 'cep', 'city', 'neighborhood', 'number', 'complemento', 'prize')]
    for u in user:
        tmp.append((u.id,
                    u.facebook_id,
                    u.name,
                    u.cpf,
                    u.email,
                    u.mobile,
                    u.address,
                    u.cep,
                    u.city,
                    u.neighborhood,
                    u.numb,
                    u.compl,
                    [(i.get('level'), i.get('now')[:10]) for i in u.win.values()]))
    cw.writerows(tmp)
    output = make_response(si.getvalue())
    output.headers["Content-Disposition"] = "attachment; filename=export.csv"
    output.headers["Content-type"] = "text/csv"
    return output

@app.route('/ref', methods=['GET'])
def get_allref():

    user = db.engine.scan(User).filter(User.id != None).gen()
    si = StringIO()
    cw = csv.writer(si)

    tmp = [('name', 'email', 'fb_app_id', 'gender', 'age_range', 'link')]
    for u in user:
        fbdata = u.facebook_data
        tmp.append((u.name,
                    u.email,
                    u.facebook_id,
                    fbdata.get('gender', ''),
                    fbdata.get('age_range', ''),
                    fbdata.get('link', '')
                    ))
    cw.writerows(tmp)
    output = make_response(si.getvalue())
    output.headers["Content-Disposition"] = "attachment; filename=next_all.csv"
    output.headers["Content-type"] = "text/csv"
    return output


@app.route('/all', methods=['GET'])
def get_alldata():
    user = db.engine.scan(User).filter(User.id != None).gen()
    si = StringIO()
    cw = csv.writer(si)

    tmp = [('name', 'email', 'fb_app_id', 'gender', 'age_range', 'link')]
    for u in user:
        fbdata = u.facebook_data
        tmp.append((u.name,
                    u.email,
                    u.facebook_id,
                    fbdata.get('gender', ''),
                    fbdata.get('age_range', ''),
                    fbdata.get('link', '')
                    ))
    cw.writerows(tmp)
    output = make_response(si.getvalue())
    output.headers["Content-Disposition"] = "attachment; filename=next_all.csv"
    output.headers["Content-type"] = "text/csv"
    return output


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8888)
