# -*- coding: utf-8 -*-

import datetime
import logging
from datetime import datetime

from tornado_json import schema
from tornado_json.exceptions import HTTPError
from tornado_json.gen import coroutine

from tips.models import Tips
from utils import APIHandler, time_to_life

log = logging.getLogger(__name__)


class TipsAPIHandler(APIHandler):
    __url_names__ = ["tips"]

    def initialize(self):
        self.db = self.application.settings.get('engine')

    @schema.validate(
        output_schema={
            "type": "object",
            "properties": {
                "tips": {"type": "array"},
                "status": {"type": "string"},
                "nextLife": {"type": "integer"},
            }
        },
        output_example={'tips': [
            "titulo 1", "titulo 2",
        ],
            "status": "success",
            "nextLife": '312132'}
    )
    @coroutine
    def get(self, level):
        try:
            tips = self.db.query(Tips).filter(Tips.game_level == level,
                                              Tips.published_at <= datetime.utcnow()).index('publish-index').all(
                desc=True)
            if not tips:
                raise HTTPError(status_code=404, log_message='Tips for {} not found!'.format(level))

            tiplist = []

            for tip in tips:
                tiplist.append(tip.tip)

            log.debug(tiplist)

            return {
                "tips": tiplist,
                "status": "success",
                "nextLife": time_to_life(self.session.get('last_dec', 0)),
            }
        except Exception as e:
            return {
                "tips": [],
                "status": "error",
                "nextLife": time_to_life(self.session.get('last_dec', 0)),
            }
