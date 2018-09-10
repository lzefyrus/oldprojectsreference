# -*- coding: utf-8 -*-

import datetime
import logging
import time
from uuid import uuid4

from tornado_json import schema
from tornado_json.exceptions import HTTPError
from tornado_json.gen import coroutine

from admin.api import LEVELS
from game.models import Challenge, Reward, User, Prize, UserRequest
from utils import APIHandler, Scranble, time_to_life, use_life, won_week, has_life

log = logging.getLogger(__name__)


class GameAPIHandler(APIHandler):
    __url_names__ = ["game"]

    def initialize(self):
        self.db = self.application.settings.get('engine')
        # self.redis = self.application.settings.get('redis')

    @schema.validate(
        output_schema={
            "type": "object",
            "properties": {
                "icons": {"type": "array"},
                "status": {"type": "string"},
                "message": {"type": "string"},
                "nextLife": {"type": "integer"},
                "lives": {"type": "integer"}
            }
        },
        output_example={
            "message": "",
            "icons": [
                {"code": "eb", "key": "ico1"},
                {"code": "P8", "key": "ico2"},
                {"code": "RB", "key": "ico3"},
                {"code": "nK", "key": "ico4"},
                {"code": "oz", "key": "ico5"},
                {"code": "Aq", "key": "ico6"},
                {"code": "N3", "key": "ico7"},
                {"code": "re", "key": "ico8"},
                {"code": "y5", "key": "ico9"},
                {"code": "p5", "key": "ico10"},
                {"code": "9K", "key": "ico11"},
                {"code": "0V", "key": "ico12"}
            ],
            "status": "success",
            "nextLife": 150,
            "lives": 3
        },
    )
    @coroutine
    def get(self, level):
        game_level = self.db.query(Challenge).filter(Challenge.game_level == level).index('active-index').first()
        if not game_level:
            raise HTTPError(status_code=404, log_message='Game Level {} not found!'.format(level))
        key = uuid4().hex
        self.session.set('level_key', key)
        content = Scranble(key=key, iconset=game_level.icons)
        lives = has_life(self, False)
        return {
            "message": "",
            "icons": content.encrypt_data(),
            "status": "success",
            "nextLife": time_to_life(self.session.get('last_dec', 0)),
            "lives": int(lives)
        }

    @schema.validate(
        input_schema={
            "type": "object",
            "properties": {
                "sequence": {"type": "string"}
            },
            "required": ['sequence']
        },
        input_example={
            "sequence": "a1|b2|c3"
        },
        output_schema={
            "type": "object",
            "properties": {
                "message": {"type": "string"},
                "status": {"type": "string"},
                "prize": {"type": "object"},
                "win": {"type": "boolean"},
                "lives": {"type": "integer"},
                "nextLife": {"type": "integer"},
            }
        },
        output_example={
            "message": "Not this time.",
            "win": False,
            "prize": {},
            "status": "success",
            "nextLife": 150,
            "lives": 1
        },
    )
    @coroutine
    def post(self, level):
        ret = {
            "message": "Not this time.",
            "win": False,
            "status": "success",
            "nextLife": time_to_life(self.session.get('last_dec', 0)),
            "lives": 0
        }
        user_life = 0

        try:
            user_life = has_life(self)
            if not user_life:
                raise Exception('No more Lives.')

            user_life = use_life(self)

            ret['nextLife'] = time_to_life(self.session.get('last_dec', 0))

            if "level_key" not in self.session.keys():
                raise Exception('You must start a new game before sending a new guess.')

            week = won_week(self, level=level, rr=False)
            if week is False:
                raise Exception('Already won this week. Try another level.')

            if user_life < 0:
                user_life = 0

            if user_life in [None, False, '']:
                user_life = 0

            ret['lives'] = user_life
            sequence = self.body.get('sequence')

            seq = Scranble(key=self.session.get('level_key', ''), iconset=sequence)
            test_sequence = seq.decrypt_data()

            if not test_sequence or test_sequence in []:
                raise Exception('Decoding sequence session error')
            self.save_request(self.session.get('id'), level, test_sequence)
            self.session.delete('level_key')

            utctoday = datetime.datetime.utcnow()
            brtoday = utctoday - datetime.timedelta(hours=3)

            thisweek = int(brtoday.isocalendar()[1])
            won = self.db.query(Reward).filter(Reward.game_level == level, Reward.user_id == None,
                                               Reward.week <= thisweek,
                                               Reward.sequence == '|'.join(test_sequence)).first()

            if not won:
                ret['lives'] = user_life if user_life > 0 else 0
                return ret
            won.user_id = self.session.get('id')
            won.updated_at = datetime.datetime.utcnow()
            won.sync(constraints=[Reward.user_id == None], raise_on_conflict=True)
            time.sleep(1 / 10)
            cd_won = self.db.query(Reward).filter(Reward.game_level == level, Reward.user_id == self.session.get('id'),
                                                  Reward.week <= thisweek,
                                                  Reward.sequence == '|'.join(test_sequence)).first()
            if cd_won and cd_won.user_id == self.session.get('id'):
                prize = self.db.get(Prize, game_level=level, id=cd_won.prize)

                prize_dict = {"name": prize.name,
                              "img": prize.img,
                              "ico": prize.ico,
                              "details": prize.details}

                user = self.db.get(User, id=self.session.get('id'), facebook_id=self.session.get('facebook_id'))

                tmp_win = {}
                if hasattr(user, 'win') and user.win is not None:
                    tmp_win = user.win

                tmp_key = 'w_{}_{}'.format(brtoday.isocalendar()[1], level)
                tmp_win[tmp_key] = {
                    'week': int(brtoday.isocalendar()[1]),
                    'now': datetime.datetime.utcnow().isoformat(),
                    'level': level,
                    'prize': prize_dict,
                    'reward': test_sequence}

                user.win = tmp_win
                user.is_dirty = True
                user.sync()

                return {"message": "Congratulations you won a prize",
                        "win": True,
                        "status": "success",
                        "prize": {'level': level,
                                  'prize': prize_dict},
                        "nextLife": time_to_life(self.session.get('last_dec', 0)),
                        "lives": user_life}

        except Exception as e:
            return {
                "message": e.__repr__(),
                "win": False,
                "status": "error",
                "prize": {},
                "nextLife": time_to_life(self.session.get('last_dec', 0)),
                "lives": user_life
            }

    def save_request(self, user, level, sequence):
        try:
            req = UserRequest()
            req.id = uuid4().hex
            req.user_id = user
            req.sequence = sequence if type(sequence) is str else '|'.join(sequence)
            req.game_level = level
            req.seq_key = self.session.get('')
            req.created_at = datetime.datetime.utcnow()
            self.db.sync(req)
            try:
                self.application.db_conn.get('ping').incr('play_count')
            except Exception as ee:
                log.warn('Request incr not completed: {}'.format(ee))
        except Exception as e:
            log.debug(e)


class ChallengeAPIHandler(GameAPIHandler):
    __url_names__ = ["challenge"]

    def initialize(self):
        self.db = self.application.settings.get('engine')

    @schema.validate(
        output_schema={
            "type": "object",
            "properties": {
                "levels": {"type": "array"},
                "status": {"type": "string"},
                "nextLife": {"type": "integer"},
                "lives": {"type": "integer"}
            }
        },
        output_example={
            "levels": [{"name": "easy", "locked": False, "soldOut": False, 'prize': {}},
                       {"name": "medium", "locked": False, "soldOut": True, 'prize': {}},
                       {"name": "hard", "locked": False, "soldOut": False, 'prize': {}},
                       {"name": "impossible", "locked": True, "soldOut": False,
                        'prize': {"name": "Boné",
                                  "img": "xpto.img",
                                  "ico": "xpto.ico",
                                  "details": []}
                        }],
            "status": "success",
            "nextLife": 1474044575,
            "lives": 3
        },
    )
    @coroutine
    def get(self):
        try:
            game_level = self.db.scan(Challenge).filter(Challenge.active == 1).all()
            levels = []
            for gl in game_level:
                wweek = won_week(self, gl.game_level, False, True)
                prize_dict = {}
                locked = False
                soldOut = yield self.total_prizes(gl.game_level)
                if wweek:
                    current = wweek[0]
                    locked = True
                    prize = self.db.get(Prize, game_level=gl.game_level, id=current.prize)
                    prize_dict = {"name": prize.name,
                                  "img": prize.img,
                                  "ico": prize.ico,
                                  "details": prize.details}
                levels.insert(int(gl.order),
                              {"name": gl.game_level, "locked": locked, "soldOut": soldOut, 'prize': prize_dict})
        except Exception as e:
            levels = e.__repr__()

        return {
            "levels": levels,
            "status": "success",
            "nextLife": time_to_life(self.session.get('last_dec', 0)),
            "lives": int(has_life(self, False))
        }

    @coroutine
    def total_prizes(self, level):
        try:
            nname = 'prize_{}'
            prizes = self.db_conn.get('ping').get(nname.format(level))
            log.debug('PRIZES: {}'.format(prizes))
            if prizes:
                return False if prizes in [None, False, '', 0, b'False', b'false'] else True
        except Exception as e:
            log.warn(e.__repr__())

        check = sum(LEVELS.get(level).get('per_week'))
        games = self.db.query(Reward).filter(Reward.game_level == level, Reward.user_id != None).count()
        soldOut = int(games) >= check
        log.debug('l: {} sold: {} - games: {} - check: {}'.format(level, soldOut, games, check))
        self.db_conn.get('ping').setex(nname.format(level), soldOut, 10)

        return soldOut


        # @coroutine
        # def post(self):
        #     raise HTTPError(status_code=400, log_message='not implemented', reason='not implemented')
