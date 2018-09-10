# -*- coding: utf-8 -*-

import logging
import random
from datetime import datetime
from uuid import uuid4

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


class UserRequest(Model):
    """ Tentativas de acertos """

    id = Field(data_type=str, range_key=True)
    user_id = Field(data_type=str, hash_key=True, nullable=False)
    sequence = Field(data_type=str, index='sequence-index')
    game_level = Field(data_type=str, index='level-index')
    created_at = Field(data_type=datetime, index='create-index')


class Challenge(Model):
    """ Desafios possíveis """

    id = Field(data_type=str, range_key=True)
    game_level = Field(data_type=str, hash_key=True, nullable=False)
    order = Field(data_type=int, index='order-index')
    icons = Field(data_type=dict, nullable=False)
    active = Field(data_type=int, default=0, index='active-index')
    created_at = Field(data_type=datetime, default=datetime.utcnow())
    updated_at = Field(data_type=datetime, nullable=True)


class Reward(Model):
    """ Premios """

    id = Field(data_type=str)
    sequence = Field(data_type=str, nullable=False, range_key=True)
    game_level = Field(data_type=str, nullable=False, hash_key=True)
    week = Field(data_type=int, nullable=False, index='week-index')
    prize = Field(data_type=str, nullable=False, index='reward-index')
    user_id = Field(data_type=str, nullable=True, index='user-index')
    signup = Field(data_type=datetime, nullable=True)
    created_at = Field(data_type=datetime, index='created-index')
    updated_at = Field(data_type=datetime, nullable=True, index='updated-index')


class Prize(Model):
    id = Field(data_type=str, range_key=True)
    game_level = Field(data_type=str, hash_key=True)
    name = Field(data_type=str, nullable=True)
    img = Field(data_type=str, nullable=True)
    ico = Field(data_type=str, nullable=True)
    details = Field(data_type=list, nullable=True)
    created_at = Field(data_type=datetime, index='created-index')
    updated_at = Field(data_type=datetime, index='updated-index', nullable=True)


class Life(Model):
    """ Vidas dos usuários """

    rr = Field(data_type=str, hash_key=True, default='life')
    user_id = Field(data_type=str, range_key=True, nullable=False)
    life_qtd = Field(data_type=int, index='life-index', default=3)
    created_at = Field(data_type=datetime, index='created-index')
    updated_at = Field(data_type=datetime, index='updated-index', nullable=True)
    last_dec = Field(data_type=datetime, index='last_dec', nullable=True)


def create_schemas(engine):
    engine.register(User, UserRequest, Challenge, Reward, Life, Prize)
    # engine.delete_schema()
    # engine.create_schema()


def create_data(engine):
    uuid = lambda: uuid4().hex
    now = lambda: datetime.utcnow()

    prize = [{'id': str(uuid()),
              'name': 'premio 1',
              'game_level': 'easy',
              'img': "https://67.media.tumblr.com/0b24856a940f06f90d46add91e9f8294/tumblr_inline_nhrgjlwFez1t183w3.png",
              'details': ['detalhe 1', 'detalhe 1 1', 'detalhe 1 1 1'],
              'created_at': now()},
             {'id': str(uuid()),
              'name': 'premio 2',
              'game_level': 'medium',
              'img': "https://67.media.tumblr.com/0b24856a940f06f90d46add91e9f8294/tumblr_inline_nhrgjlwFez1t183w3.png",
              'details': ['detalhe 2', 'detalhe 2', 'detalhe 2'],
              'created_at': now()},
             {'id': str(uuid()),
              'name': 'premio 3',
              'game_level': 'hard',
              'img': "https://67.media.tumblr.com/0b24856a940f06f90d46add91e9f8294/tumblr_inline_nhrgjlwFez1t183w3.png",
              'details': ['detalhe 3', 'detalhe 3', 'detalhe 3'],
              'created_at': now()},
             {'id': str(uuid()),
              'name': 'premio 1',
              'game_level': 'impossible',
              'img': "https://67.media.tumblr.com/0b24856a940f06f90d46add91e9f8294/tumblr_inline_nhrgjlwFez1t183w3.png",
              'details': ['detalhe 4', 'detalhe 4', 'detalhe 4'],
              'created_at': now()}]
    reward = []
    reward = [{'id': uuid(),
               'game_level': 'easy',
               'sequence': rand_sequence(reward),
               'prize': prize[0]['id'],
               'week': 5,
               'created_at': datetime.utcnow()},
              {'id': uuid(),
               'game_level': 'medium',
               'sequence': rand_sequence(reward, 6),
               'prize': prize[1]['id'],
               'week': 5,
               'created_at': datetime.utcnow()},
              {'id': uuid(),
               'game_level': 'hard',
               'sequence': rand_sequence(reward, 9),
               'prize': prize[2]['id'],
               'week': 5,
               'created_at': datetime.utcnow()},
              {'id': uuid(),
               'game_level': 'impossible',
               'sequence': rand_sequence(reward, 11),
               'prize': prize[3]['id'],
               'week': 5,
               'created_at': datetime.utcnow()}]
    icons = {'icons': [{'code': '1', 'key': 'ico1'},
                       {'code': '2', 'key': 'ico2'},
                       {'code': '3', 'key': 'ico3'},
                       {'code': '4', 'key': 'ico4'},
                       {'code': '5', 'key': 'ico5'},
                       {'code': '6', 'key': 'ico6'},
                       {'code': '7', 'key': 'ico7'},
                       {'code': '8', 'key': 'ico8'},
                       {'code': '9', 'key': 'ico9'},
                       {'code': '10', 'key': 'ico10'},
                       {'code': '11', 'key': 'ico11'},
                       {'code': '12', 'key': 'ico12'}]}

    challenge = [{'id': uuid(),
                  'game_level': 'easy',
                  'icons': icons.copy(),
                  "active": 1,
                  'order': 0,
                  'created_at': now()
                  },
                 {'id': uuid(),
                  'game_level': 'medium',
                  'icons': icons.copy(),
                  'order': 1,
                  "active": 1,
                  'created_at': now()
                  },
                 {'id': uuid(),
                  'game_level': 'hard',
                  'icons': icons.copy(),
                  'order': 2,
                  "active": 1,
                  'created_at': now()
                  },
                 {'id': uuid(),
                  'game_level': 'impossible',
                  'icons': icons.copy(),
                  'order': 3,
                  "active": 1,
                  'created_at': now()
                  }]

    log.debug(prize)
    for i in prize:
        tmpi = Prize()
        for k, w in i.items():
            log.debug('{} : {}'.format(k, w))
            setattr(tmpi, k, w)
        log.debug(tmpi)
        engine.sync(tmpi)

    log.debug(reward)
    for i in reward:
        tmpi = Reward()
        for k, w in i.items():
            setattr(tmpi, k, w)
        engine.sync(tmpi)

    log.debug(challenge)
    for i in challenge:
        tmpi = Challenge()
        for k, w in i.items():
            setattr(tmpi, k, w)
        engine.sync(tmpi)


def rand_sequence(reward, items=4, max_items=12):
    seq = []
    for i in range(0, items):
        while True:
            item = random.randint(0, max_items)
            if str(item) not in seq:
                seq.append(str(item))
                break

    return '|'.join(seq)
