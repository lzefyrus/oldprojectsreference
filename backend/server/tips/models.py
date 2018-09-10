# -*- coding: utf-8 -*-

import logging
from datetime import datetime
from uuid import uuid4

from flywheel import Model, Field

log = logging.getLogger(__name__)

log.debug("##### MODEL DATA FOR REFERAL #####")


class Tips(Model):
    """ Discas dos jogos """

    game_level = Field(data_type=str, hash_key=True, nullable=False)
    tip = Field(data_type=str, default="")
    created_at = Field(data_type=datetime, range_key=True)
    updated_at = Field(data_type=datetime, index='updated-index', nullable=True)
    published_at = Field(data_type=datetime, index='publish-index')


def create_data(engine):
    uuid = lambda: uuid4().hex
    now = lambda: datetime.utcnow()
    tips = [{'game_level': 'easy',
             'created_at': now(),
             'published_at': now(),
             'tip': 'titulo 1'
             },
            {'game_level': 'medium',
             'created_at': now(),
             'published_at': now(),
             'tip': 'titulo 1'},
            {'game_level': 'hard',
             'created_at': now(),
             'published_at': now(),
             'tip': 'titulo 1'
             },
            {'game_level': 'impossible',
             'created_at': now(),
             'published_at': now(),
             'tip': 'titulo 1'
             }]

    for i in tips:
        tmpi = Tips()
        for k, w in i.items():
            setattr(tmpi, k, w)
        engine.sync(tmpi)


def create_schemas(engine):
    engine.register(Tips)
    engine.delete_schema()
    # engine.create_schema()
