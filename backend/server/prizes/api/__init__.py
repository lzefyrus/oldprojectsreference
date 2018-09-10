# -*- coding: utf-8 -*-

import logging

from tornado.escape import json_decode, json_encode
from tornado_json import schema
from tornado_json.gen import coroutine

from admin.api import LEVELS, PRIZES
from game.models import Reward, Prize
from utils import OpenApiHandler as APIHandler

log = logging.getLogger(__name__)

xstr = lambda s: s or ""

FEEDCACHE = 'feed_cache'


class PrizesAPIHandler(APIHandler):
    __url_names__ = ["prizes"]

    def initialize(self):
        self.db = self.application.settings.get('engine')

    @schema.validate(

        output_schema={
            "type": "object",
            "properties": {
                "totals": {"type": "object"},
                "prizes": {"type": "array"}
            }
        },
        output_example={
            "totals": {
                "prizes": {
                    "total": 100,
                    "delivered": 10
                },
                "users": 10,
                "tries": 100
            },
            "prizes": [
                {
                    "key": "prize-0",
                    "total": 500,
                    "delivered": 10
                }, {
                    "key": "prize-1",
                    "total": 500,
                    "delivered": 10
                },
                {
                    "key": "prize-2",
                    "total": 500,
                    "delivered": 10
                }, {
                    "key": "prize-3",
                    "total": 500,
                    "delivered": 10
                }
            ],
            "lastPrize": "icone"
        }
    )
    @coroutine
    def get(self):
        # redis cache

        feed = self.db_conn.get('ping').get(FEEDCACHE)

        if feed:
            log.info(feed.replace(b"'", b'"'))
            return json_decode(feed.replace(b"'", b'"').decode())
        data = {}
        total_dict = {}
        feed_list = []
        total_used = 0
        total = 0
        try:
            for i in PRIZES:
                qtd = self.db.query(Reward).filter(Reward.game_level == i.get('game_level'), Reward.user_id != None,
                                                   Reward.prize == i.get('id')).count()
                pw = sum(LEVELS.get(i.get('game_level')).get('per_week'))
                total += pw
                total_used += qtd
                feed_list.append({
                    "key": i.get('id'),
                    "name": i.get('name'),
                    'level': i.get('game_level'),
                    'ico': i.get('ico'),
                    "total": pw,
                    "delivered": qtd if qtd else 0
                })

            total_users = int(self.application.db_conn.get('ping').get('user_count')) or 0
            total_tries = int(self.application.db_conn.get('ping').get('play_count')) or 0

            total_dict['prizes'] = {'total': total,
                                    'delivered': total_used}
            total_dict['users'] = total_users
            total_dict['tries'] = total_tries

            data['totals'] = total_dict
            data['prizes'] = feed_list
            data['lastPrize'] = self.getLast()
            log.debug(data)

            self.db_conn.get('ping').setex(FEEDCACHE, json_encode(data), 60 * 2)
            return data
        except Exception as e:
            raise Exception(e)

    def getLast(self):
        updated = None
        prize = None
        level = None
        for i in ['easy', 'medium', 'hard', 'impossible']:
            tmp = self.db.query(Reward).filter(Reward.game_level == i, Reward.user_id != None).index(
                'created-index').first(desc=True)
            if tmp:
                if updated is None:
                    updated = tmp.updated_at
                if updated <= tmp.updated_at:
                    updated = tmp.updated_at
                    prize = tmp.prize
                    level = i
        if prize:
            pp = self.db.get(Prize, id=prize, game_level=level)
            if pp:
                return pp.ico
        return ''
