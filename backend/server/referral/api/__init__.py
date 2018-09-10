# -*- coding: utf-8 -*-

import logging

from tornado_json import schema
from tornado_json.gen import coroutine

from referral.models import ReferralUser
from utils import APIHandler, time_to_life

log = logging.getLogger(__name__)


class FriendsAPIHandler(APIHandler):
    __url_names__ = ["friends"]

    def initialize(self):
        self.db = self.application.settings.get('engine')

    @schema.validate(
        output_schema={
            "type": "object",
            "properties": {
                "friends": {"type": "array"},
                "status": {"type": "string"},
                "nextLife": {"type": "integer"},
            }
        },
        output_example={
            "friends": [{"name": "Ivo Rafael",
                         "picture": 'https://scontent.xx.fbcdn.net/v/t1.0-1/c0.16.50.50/p50x50/13083237_10205715595361172_4518714243773231990_n.jpg?oh=8269aeda56c5fbe430579cd080e62627&oe=58A81A92',
                         "life": 0},
                        {"name": "Celso Candido",
                         "picture": 'https://scontent.xx.fbcdn.net/v/t1.0-1/p50x50/166005_10153607416943883_8023769138677219084_n.jpg?oh=d2dd99c1819768704f53d04eb6af204e&oe=585FA3EE',
                         "life": 0}, ],
            "status": "success",
            "nextLife": 1150
        }
    )
    @coroutine
    def get(self):
        try:
            friends = self.db.query(ReferralUser).filter(ReferralUser.refered_id == self.session.get('id')).index(
                'created_at').limit(50).all()

            user_list = []
            for friend in friends:
                user_list.append({"name": friend.face_data.get('name'),
                                  "picture": friend.face_data.get('picture'),
                                  "life": friend.life})

            return {
                "friends": user_list,
                "status": "success",
                "nextLife": time_to_life(self.session.get('last_dec', 0)),
            }
        except Exception as e:
            log.info(e)
            return {
                "friends": [],
                "status": "error",
                "nextLife": time_to_life(self.session.get('last_dec', 0)),
            }
