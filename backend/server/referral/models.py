# -*- coding: utf-8 -*-

import logging
from datetime import datetime

from flywheel import Model, Field

log = logging.getLogger(__name__)


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


def create_schemas(engine):
    engine.register(ReferralUser, ReferralRequest)
    engine.create_schema()

    # campnext.game5@gmail.com
    # next@game
    # http://api.next.me/referral/56cdc52587864f7c9927784ae4b70b50
