# -*- coding: utf-8 -*-
import datetime
import calendar
import json
import logging
import time

import requests
from dynamo3 import DynamoDBConnection
from flywheel import Model, Field, Engine

ES_ENDPOINT = 'search-next-bsmgz6uzjomdsowhkrxqcjrtuu.sa-east-1.es.amazonaws.com'
HEADERS = {
    'content-type': "application/json",
    'cache-control': "no-cache"
}
AWS_SECRET_ACCESS_KEY = 'wbcSZsVAWspz/YxIrHH2Hk7DQRJlV8z5Jro8Tn3g'
AWS_ACCESS_KEY = 'AKIAI5NVJ5FZ5KC4K5KA'
FLYWHEEL_REGION = 'sa-east-1'

LASTITEMS = """{
  "query": {
    "bool": {
       "must": [{ "match": { "_type" : "%s"}}]
      
    }
  },
  "sort": {"@timestamp": {"order" : "desc", "mode" : "max"}},
  "size" : 1
}"""



print("Winners ")
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)
handler = logging.FileHandler('pwin.log')
handler.setLevel(logging.DEBUG)

# create a logging format
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
handler.setFormatter(formatter)

# add the handlers to the logger
logger.addHandler(handler)

logger.info("start")


class User(Model):
    """ Usuarios do game """

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
    created_at = Field(data_type=datetime.datetime)
    updated_at = Field(data_type=datetime.datetime, nullable=True)
    deleted_at = Field(data_type=datetime.datetime, nullable=True, index='create-index')
    referral = Field(data_type=str, default='')
    avatar = Field(data_type=dict, nullable=True)
    win = Field(data_type=dict, nullable=True)
    win_email = Field(data_type=list, nullable=True)
    is_dirty = Field(data_type=bool, default=False)
    is_admin = Field(data_type=int, default=0, index='admin-index')

dyn = DynamoDBConnection.connect(region=FLYWHEEL_REGION,
                                 access_key=AWS_ACCESS_KEY,
                                 secret_key=AWS_SECRET_ACCESS_KEY)
db = Engine(dynamo=dyn)

cont = {
    'easy': [],
    'medium': [],
    'hard': [],
    'impossible': [],
}

if __name__ == '__main__':
    context = db.scan(User).filter(User.mobile != None).gen()
    print("DONE SCAN")
    for u in context:
        try:
            if u.cpf is not None:
                for i in u.win.values():
                    print('*** {}'.format(i.get('level')))
                    print('*** {}'.format({'name': u.name,'picture': u.avatar.get('big', '')}))
                    cont[i.get('level')].append({'name': u.name,'picture': u.avatar.get('big', '')})
        except Exception as e:
            print(e)
            logger.info('## {} ##'.format(u.id))
            logger.error(e)
    logger.debug("ROUNF 2")
    for k, w in cont.items():
        logger.debug("ROUNF 3")
        with open('winners_{}_.json'.format(k), 'w', encoding='utf-8') as outfile:
            tmp = {"prize": k,
                   "winners": w}
            json.dump(tmp, outfile, ensure_ascii=False)
