# -*- coding: utf-8 -*-

import datetime
import logging

from tornado_json import schema
from tornado_json.gen import coroutine

from referral.models import ReferralUser
from utils import APIHandler

log = logging.getLogger(__name__)


class BoxApiHandler(APIHandler):
    __url_names__ = ["boxgame"]

    def initialize(self):
        self.db = self.application.settings.get('engine')
        # self.redis = self.application.settings.get('redis')

    @schema.validate(
        output_schema={
            "type": "object",
            "properties": {
                "teddy": {"type": "object"},
                "pipocando": {"type": "object"},
                "status": {"type": "string"},
                "message": {"type": "string"},
            }
        },
        output_example={
            "message": "",
            "teddy": {"13": 1,
                      "14": 1,
                      "15": 2
                      },
            "pipocando": {"13": 1,
                          "14": 1,
                          "15": 2
                          },
            "status": "success",
        },
    )
    @coroutine
    def get(self):
        if not self.session.id == 'opiu123098dsa123':
            # return self.write_error(401)
            pass

        now = datetime.datetime.utcnow()
        last_hour = now - datetime.timedelta(hours=1)
        last_hour = last_hour.replace(second=0, microsecond=0, minute=0)
        flh = last_hour
        ret = {"status": "success",
               "message": ""}

        for u in ['pipocando', 'teddy']:
            tmp = {}
            last_hour = flh
            for i in range(0, 3):
                r_hour = last_hour - datetime.timedelta(hours=1)
                tmp[last_hour.strftime('%Y-%m-%d %H:%M')] = self.db.query(ReferralUser).filter(ReferralUser.refered_id == u,
                                                                                   ReferralUser.created_at <= last_hour,
                                                                                   ReferralUser.created_at > r_hour).count()
                last_hour = r_hour
            ret[u] = tmp

        return ret


def fixminute(minute):
    mm = str(minute)
    return int('{}{}'.format(mm[0], 0))
