# -*- coding: utf-8 -*-

import logging
from datetime import datetime, timedelta
from itertools import permutations
from random import sample
from time import sleep
from uuid import uuid4

from tornado_json import schema

from game.models import create_schemas as gschema, User, Life
from referral.models import create_schemas as rschema, ReferralRequest
from tips.models import create_schemas as tschema, Tips
from utils import APIHandler

log = logging.getLogger(__name__)
from game.models import Reward, Prize, Challenge

uuid = lambda: uuid4().hex
now = lambda: datetime.utcnow()

TIPS = {
    'easy': [
        "É falta de educação usar à mesa.",
        "Não dá pra pôr do avesso.",
        "Se você tem cabeção, vai usar no último botão.",
        "Não é uma boa usar na montanha russa.",
        "Pro look é bom, né?",
        "Tem gente que não tira o selinho da aba.",
        "A mula sem cabeça não pode usar.",
        "Não importa o seu peso, o tamanho é igual.",
        "Tem gente que tem até coleção.",
        "O melhor esquema pra se proteger do sol.",
        "Tem um buraco para passar o cabelo.",
        "As professoras não deixavam usar na classe.",
        "Jogadores de pôquer usam para disfarçar reações.",
        "Pra frente ou pra trás, você quem faz o estilo.",
        "Ele ajuda o look, mas estraga o penteado.",
        "A melhor saída para um cabelo bagunçado.",
        "É um bom começo pra um disfarce.",
        "Foi criado pra evitar o sol, mas ficou mesmo pelo estilo.",
        "Ele é usado tanto por homens quanto por mulheres.",
        "Veste a cabeça de várias gerações.",
        "Skatista adora usar na cabeça.",
        "Tem gente que usa com a aba reta.",
        "Todo jogador de beisebol usa na cabeça.",
        "Os famosos usam com óculos escuros para não serem reconhecidos.",
        "Mário usa um vermelho e Luigi um verde ",
        "Rola usar a aba reta ou curvada.",
        "Os pilotos de F1 usam quando não estão de capacete.",
        "Tem gente que chama de bombeta.",
        "Esqueceu o guarda-sol? Coloca ele na cabeça e já era.",
        "É bom pra proteger a careca.",
        "Vai na cabeça e existe em diferentes estilos e tecidos.",
        "Ele se ajusta ao tamanho da sua cabeça."
    ],
    'hard': [
        "O que? Não ouvi direito.",
        "Os maiores têm espuma.",
        "Os mais tops tem isolamento acústico pra abafar o som externo.",
        "Não rola usar mais de duas pessoas ao mesmo tempo.",
        "Enrosca fácil.",
        "Dizem que faz mal dormir com ele no ouvido.",
        "Tem sempre alguém no metrô usando um.",
        "Não gera poluição sonora.",
        "Sem ele, não rola áudio guia no museu.",
        "Alguns são sem fio.",
        "A galera usa pra escutar o jogo quando tá no estádio.",
        "O sinal perfeito para: “não quero falar com ninguém”.",
        "Esconde suas músicas facinho.",
        "Combina com música, filme e até um joguinho.",
        "Vai dentro ou fora de sua orelha;",
        "O pessoal usa pra escutar música no trabalho.",
        "Não exagera senão zoa os tímpanos.",
        "Rola ouvir o que quiser nele.",
        "O DJ sempre tá com um no pescoço.",
        "Você coloca um em cada orelha.",
        "Música para seus ouvidos.",
        "Todo mundo usa para ver filme no avião.",
        "O esquema perfeito pra escutar música alta sem atrapalhar ninguém.",
        "Um bom jeito de fingir que não está escutando.",
        "Vem junto com o celular.",
        "É bom pra você levar sua música pra qualquer lugar.",
        "Bom pra colocar uma trilha sonora no caminho pro trabalho.",
        "Não pode usar enquanto dirige.",
        "Toca música, mas ninguém usa em festa.",
        "Se você estiver usando para uma ligação, vai parecer que está falando sozinho.",
        "Tem sempre aquele cara no ônibus que esquece.",
        "Produz um som particular."
    ],
    'medium': [
        "Antes, ela só funcionava na tomada.",
        "Sempre que tá ligada, ela vibra.",
        "Tem equalizador pro som.",
        "Tem algumas que você controla pelo celular.",
        "Tunts. Tunts. Tunts.",
        "Amplifica as ondas sonoras.",
        "Aqui o grave quer dizer que é bom.",
        "Pra animar o som do churras.",
        "Tem muitos furinhos.",
        "Não é eco, mas propaga o som.",
        "Quando não tem fio ela funciona por bluetooth.",
        "A potência dela é medida em Watts.",
        "Carrega na tomada ou no USB.",
        "Dizem que quando ela tá na potência máxima pode até estourar vidros.",
        "Nessa caixa você não guarda nada.",
        "Em todo show tem.",
        "Melhor esquema pra acordar a vizinhança.",
        "Melhor que o som do seu celular.",
        "Vai bombar o som na festa.",
        "Ela é pequena, mas o som é monstro.",
        "DJ, som na___ !",
        "Som alto pra galera curtir em qualquer lugar.",
        "Essa não é de papelão.É de som.",
        "O home theater é feito com elas.",
        "Tem alto-falante.",
        "Sem ela o microfone não funciona.",
        "Na rave, a galera dança do lado dela.",
        "Antes todo computador vinha com duas.",
        "Tem uma galera que curte colocar várias atrás do carro.",
        "Não dá pra fazer festa sem uma.",
        "Se tiver no caminhão, pode virar trio elétrico.",
        "Aqui o tamanho pode não ser documento: as pequenas também são bem potentes."
    ],
    'impossible': [
        "Você pode andar sozinho ou levar alguém de carona.",
        "Você precisa de equilíbrio pra andar numa dessas.",
        "Dizem que foi inventada pelo Leonardo da Vinci.",
        "A primeira foi chamada de “cavalinho de pau”.",
        "Tem corrente, mas não rola usar no pescoço.",
        "O nome indica o número de rodas que ela tem.",
        "Algumas são elétricas.",
        "É bom pra queimar calorias.",
        "Muita gente guarda com cadeado.",
        "Não precisa de carteira para dirigir.",
        "Antes tinha uma roda maior do que a outra.",
        "É o meio de transporte mais usado no mundo.",
        "Tem estilo de gol com o seu nome.",
        "Você tem que se manter em movimento pra não cair dela.",
        "Algumas são dobráveis.",
        "Em alguns países é obrigatório usar capacete quando você anda nela.",
        "Tem cesta e aro, mas não é quadra de basquete.",
        "Se for subir ladeira, melhor ter uma elétrica.",
        "A galera do triatlo tem que correr com uma dessas.",
        "Você começou com quatro rodas e agora usa só duas.",
        "Um ET famoso voou numa dessas.",
        "Com ela, você chega aos lugares sem pegar trânsito.",
        "Tem gente que chama de magrela.",
        "Algumas têm buzina.",
        "Depois que você aprende, nunca esquece.",
        "Em alguns lugares tem uma faixa só pra ela.",
        "Não é carro, mas tem marchas.",
        "O transporte mais ecológico.",
        "Tem quem arrisque andar sem as mãos",
        "A da academia não sai do lugar.",
        "A das antigas tinha campainha e cestinha.",
        "É um meio de transporte que ajuda a entrar em forma."
    ]
}

PRIZES = [{'id': 'premio_bone',
           'name': 'Boné ',
           'game_level': 'easy',
           'ico': 'cap',
           'img': "https://next.me/assets/cap.jpg",
           'details': ['Snapback cinco gomos', '100% algodão', 'regulador traseiro feito em plástico reciclado.'],
           'created_at': now()},
          {'id': 'premio_caixa',
           'name': 'Caixa de som',
           'game_level': 'medium',
           'ico': 'speaker',
           'img': "https://next.me/assets/speaker.jpg",
           'details': ['Á prova d’água', 'Microfone embutido', '4,5 hrs de bateria'],
           'created_at': now()},
          {'id': 'premio_fone',
           'name': 'Headphone',
           'game_level': 'hard',
           'ico': 'headset',
           'img': "https://next.me/assets/headphone.jpg",
           'details': ['Bluetooth 4.1', 'Microfone interno', 'Ergonômico'],
           'created_at': now()},
          {'id': 'premio_bike',
           'name': 'Bicicleta Elétrica Dobrável',
           'game_level': 'impossible',
           'ico': 'bike',
           'img': "https://next.me/assets/bike.jpg",
           'details': ['Rodas aro 20”', 'Bateria de lítio 36V – 10 AH', 'Motor 250W'],
           'created_at': now()}
          ]


LEVELS = {
    "easy": {
        "per_week": [250, 350, 200, 170, 30],
        "valid": 4,
        'prizes': [
            {"prize": 'premio_bone',
             "icons": [
                 {"code": "1", "key": "cow", "invalid": True},
                 {"code": "2", "key": "note", "invalid": True},
                 {"code": "3", "key": "camera"},
                 {"code": "4", "key": "spray"},
                 {"code": "5", "key": "lamp"},
                 {"code": "6", "key": "skate"},
                 {"code": "7", "key": "sun"},
                 {"code": "8", "key": "helm"},
                 {"code": "9", "key": "tenis"},
                 {"code": "10", "key": "coco"},
                 {"code": "11", "key": "sunglass"},
                 {"code": "12", "key": "fone"}]
             }
        ]
    },
    "medium": {
        "per_week": [13, 18, 10, 8, 1],
        "valid": 5,
        'prizes': [
            {"prize": 'premio_caixa',
             "icons": [
                 {"code": "1", "key": "note"},
                 {"code": "2", "key": "hand"},
                 {"code": "3", "key": "phone"},
                 {"code": "4", "key": "globo"},
                 {"code": "5", "key": "guitar"},
                 {"code": "6", "key": "disco"},
                 {"code": "7", "key": "ring", "invalid": True},
                 {"code": "8", "key": "joystick", "invalid": True},
                 {"code": "9", "key": "moto", "invalid": True},
                 {"code": "10", "key": "spray", "invalid": True},
                 {"code": "11", "key": "megafone"},
                 {"code": "12", "key": "lamp", "invalid": True}]
             }
        ]
    },
    "hard": {
        "per_week": [13, 18, 10, 8, 1],
        "valid": 6,
        'prizes': [
            {"prize": 'premio_fone',
             "icons": [
                 {"code": "1", "key": "note"},
                 {"code": "2", "key": "hand"},
                 {"code": "3", "key": "phone"},
                 {"code": "4", "key": "globo"},
                 {"code": "5", "key": "guitar"},
                 {"code": "6", "key": "disco"},
                 {"code": "7", "key": "flag", "invalid": True},
                 {"code": "8", "key": "joystick", "invalid": True},
                 {"code": "9", "key": "ghost", "invalid": True},
                 {"code": "10", "key": "spray", "invalid": True},
                 {"code": "11", "key": "megafone"},
                 {"code": "12", "key": "lamp", "invalid": True}]
             }
        ]
    },
    "impossible": {
        "per_week": [1, 2, 1, 1],
        "valid": 7,
        'prizes': [
            {"prize": 'premio_bike',
             "icons": [
                 {"code": "1", "key": "bible", "invalid": True},
                 {"code": "2", "key": "lamp", "invalid": True},
                 {"code": "3", "key": "raio"},
                 {"code": "4", "key": "squeeze"},
                 {"code": "5", "key": "push"},
                 {"code": "6", "key": "sino"},
                 {"code": "7", "key": "lock"},
                 {"code": "8", "key": "helm"},
                 {"code": "9", "key": "chavetool"},
                 {"code": "10", "key": "ring", "invalid": True},
                 {"code": "11", "key": "tv", "invalid": True},
                 {"code": "12", "key": "car", "invalid": True}]
             }
        ]
    }
}


def isAdmin(user):
    if not user.admin:
        raise Exception('401 ;)')


class BrunaHandler(APIHandler):
    __urls__ = [r"/admin/bruna/"]

    def initialize(self):
        self.db = self.application.settings.get('engine')
        isAdmin(self.db.get(User, id=self.session.get('id'), facebook_id=self.session.get('facebook_id')))

    def post(self):
        # user = self.db.scan(User).all()
        rewards = self.db.scan(Reward).all()
        # userreq = self.db.scan(UserRequest).all()

        rr = []

        for r in rewards:
            rr.append({
                'level': r.game_level,
                'sequence': r.sequence,
                'week': r.week,
                'winner': r.user_id
            })

        self.write({'rewards': rr})


class AdminHandler(APIHandler):
    __urls__ = [r"/admin/api/"]

    def initialize(self):
        self.db = self.application.settings.get('engine')
        isAdmin(self.db.get(User, id=self.session.get('id'), facebook_id=self.session.get('facebook_id')))

    def post(self):
        pass


class RewardsHandler(APIHandler):
    __urls__ = [r"/admin/api/rewards/"]

    def post(self):
        reward = self.db.query(Reward).filter(Reward.game_level == 'easy').first()
        if reward:
            raise Exception('Rewards already created.')

        challenge = self.db.query(Challenge).filter(Challenge.game_level == 'easy').first()
        if not challenge:
            raise Exception('Challenge {} not found'.format('easy'))
        prize = self.db.query(Prize).filter(Challenge.game_level == 'easy').first()
        if not prize:
            raise Exception('Prizes for level {} not found'.format('easy'))


class TipsHandler(APIHandler):
    __urls__ = [r"/admin/api/tips/"]

    @schema.validate(
        output_schema={
            "type": "object",
            "properties": {
                "status": {"type": "string"},
                "message": {"type": "string"}
            }
        },
        output_example={
            "message": "",
            "status": "success",
        },
    )
    def post(self):
        uuid = lambda: uuid4().hex
        now = lambda d, x: d + timedelta(days=x)
        utcnow = datetime.utcnow()
        try:
            for k, w in TIPS.items():
                temp = {'game_level': k,
                        'created_at': '',
                        'published_at': now(utcnow, 0),
                        'tip': ''
                        }
                dd = 0
                for tip in w:
                    temp['tip'] = tip
                    temp['created_at'] = datetime.utcnow()
                    temp['published_at'] = now(utcnow, dd)
                    self.db.save(Tips(**temp))
                    dd += 1
                    log.debug(temp)
                    sleep(0.1)
            return {
                "message": "",
                "status": "success",
            }
        except Exception as e:
            return {
                "message": e,
                "status": "error",
            }


class SchemasHandler(APIHandler):
    __urls__ = [r"/admin/api/schemas/"]

    def initialize(self):
        self.db = self.application.settings.get('engine')
        isAdmin(self.db.get(User, id=self.session.get('id'), facebook_id=self.session.get('facebook_id')))

    @schema.validate(
        output_schema={
            "type": "object",
            "properties": {
                "status": {"type": "string"},
                "message": {"type": "string"}
            }
        },
        output_example={
            "message": "",
            "status": "success",
        },
    )
    def post(self):
        """
        Deletes and create all schemas
        :return: Boll
        """
        try:
            gschema(self.db)
            tschema(self.db)
            rschema(self.db)
            self.db.delete_schema()
            self.db.create_schema()

            return {
                "message": "",
                "status": "success",
            }
        except Exception as e:
            return {
                "message": e,
                "status": "error",
            }


class PrizeHandler(APIHandler):
    __urls__ = [r"/admin/api/prizes/"]

    def initialize(self):
        self.db = self.application.settings.get('engine')
        isAdmin(self.db.get(User, id=self.session.get('id'), facebook_id=self.session.get('facebook_id')))

    @schema.validate(
        output_schema={
            "type": "object",
            "properties": {
                "status": {"type": "string"},
                "message": {"type": "string"}
            }
        },
        output_example={
            "message": "",
            "status": "success",
        },
    )
    def post(self):
        """
        Create base data for challenges
        :return: Boll
        """
        # try:
        create_prizes(self.db)
        return {
            "message": "",
            "status": "success",
        }

class Clear(APIHandler):
    __urls__ = [r"/admin/api/clear/"]

    def initialize(self):
        self.db = self.application.settings.get('engine')
        isAdmin(self.db.get(User, id=self.session.get('id'), facebook_id=self.session.get('facebook_id')))

    def delete(self):
        rew = self.db.scan(Reward).filter(Reward.user_id >= 0).all()
        for r in rew:
            log.info('Deleting: {}'.format(r.user_id))
            r.updated_at = None
            r.user_id = None
            r.sync()


class RewardHandler(APIHandler):
    __urls__ = [r"/admin/api/reward/"]

    def initialize(self):
        self.db = self.application.settings.get('engine')
        isAdmin(self.db.get(User, id=self.session.get('id'), facebook_id=self.session.get('facebook_id')))

    @schema.validate(
        output_schema={
            "type": "object",
            "properties": {
                "status": {"type": "string"},
                "message": {"type": "string"}
            }
        },
        output_example={
            "message": "",
            "status": "success",
        },
    )
    def post(self):
        """
        Create base data for challenges
        :return: Boll
        """
        # try:
        week = int((datetime.utcnow() - timedelta(days=2)).isocalendar()[1])
        create_rewards(self.db, week)
        return {
            "message": "",
            "status": "success",
        }


class ChallengeHandler(APIHandler):
    __urls__ = [r"/admin/api/challenge/"]

    def initialize(self):
        self.db = self.application.settings.get('engine')
        isAdmin(self.db.get(User, id=self.session.get('id'), facebook_id=self.session.get('facebook_id')))

    @schema.validate(
        output_schema={
            "type": "object",
            "properties": {
                "status": {"type": "string"},
                "message": {"type": "string"}
            }
        },
        output_example={
            "message": "",
            "status": "success",
        },
    )
    def post(self):
        """
        Create base data for challenges
        :return: Boll
        """
        # try:
        create_challenges(self.db)
        return {
            "message": "",
            "status": "success",
        }


class BoxHandler(APIHandler):
    __urls__ = [r"/admin/api/box/"]

    def initialize(self):
        self.db = self.application.settings.get('engine')
        isAdmin(self.db.get(User, id=self.session.get('id'), facebook_id=self.session.get('facebook_id')))

    @schema.validate(
        output_schema={
            "type": "object",
            "properties": {
                "status": {"type": "string"},
                "message": {"type": "string"}
            }
        },
        output_example={
            "message": "",
            "status": "success",
        },
    )
    def post(self):
        """
        Create fake users for boxes
        :return: Boll
        """
        nn = datetime.utcnow()

        for u in ['teddy', 'pipocando']:
            local_user = User()
            local_user.id = u
            local_user.facebook_id = len(u)
            local_user.facebook_token = '098123098123'
            local_user.facebook_data = {'name': u}
            local_user.email = '{}@next.com'.format(u)
            local_user.name = u.capitalize()
            local_user.referral = u
            local_user.avatar = {'big': 'a', 'small': 'b'}
            local_user.created_at = nn
            self.db.sync(local_user)

            user_life = Life()
            user_life.user_id = local_user.id
            user_life.created_at = datetime.utcnow()
            self.db.sync(user_life)

            referral = ReferralRequest()
            referral.user_id = local_user.id
            referral.id = u
            referral.created_at = nn
            self.db.sync(referral)

        return {
            "message": "",
            "status": "success",
        }


def create_challenges(engine):
    uuid = lambda: uuid4().hex
    now = lambda: datetime.utcnow()
    inserts = []
    order = {'easy': 0,
             'medium': 1,
             'hard': 2,
             'impossible': 3,
             }
    mock = {'id': uuid(),
            'game_level': 'easy',
            'icons': {'icons': []},
            "active": 1,
            'order': 0,
            'created_at': now()
            }
    for level, data in LEVELS.items():
        for prize in data.get('prizes'):
            mock['id'] = uuid()
            mock['game_level'] = level
            mock['icons']['icons'] = prize.get('icons', [])
            mock['order'] = order.get(level, 0)
            log.debug(mock)
            inserts.append(Challenge(**mock))
            break

        engine.sync(inserts)


def create_prizes(engine):
    for i in PRIZES:
        tmpi = Prize()
        for k, w in i.items():
            log.debug('{} : {}'.format(k, w))
            setattr(tmpi, k, w)
        log.debug(tmpi)
        engine.sync(tmpi)


def create_rewards(engine, start_week):
    guid = lambda: uuid4().hex
    now = datetime.utcnow()
    for level, data in LEVELS.items():
        per_week = data.get('per_week')
        seqs = None
        valid = []
        for prize in data.get('prizes'):
            valid_ids = [i.get('code') for i in prize.get('icons') if 'invalid' not in i.keys()]
            if level == 'medium' and seqs is not None:
                seqs = list(set(seqs) - set(valid))
            else:
                seqs = list(permutations(valid_ids, data.get('valid')))

            valid = sample(seqs, sum(per_week))
            start = 0
            base = {
                "game_level": str(level),
                "prize": prize.get('prize'),
                "created_at": now}

            for i in range(len(data['per_week'])):
                base['week'] = start_week + i
                ins = []
                size = 0
                log.info('start: {} size: {}'.format(start, int(start + per_week[i])))
                try:
                    if per_week[i] > 0:
                        for s in valid[start:int(start + per_week[i])]:
                            base['sequence'] = '|'.join(s)
                            base['id'] = guid()
                            log.debug(base)
                            ins.append(Reward(**base))
                            size += 1
                            if int(size % 100) == 0:
                                log.debug(base)
                                engine.save(ins)
                                ins = []
                        start += per_week[i]
                        extra = 0

                        if len(ins) > 0:
                            engine.save(ins)
                except Exception as e:
                    for s in valid[start:int(start + per_week[i] - 1)]:
                        base['sequence'] = '|'.join(s)
                        base['id'] = guid()
                        log.debug(base)
                        ins.append(Reward(**base))
                        size += 1
                        if int(size % 100) == 0:
                            log.debug(base)
                            engine.save(ins)
                            ins = []
                    start += per_week[i]
                    extra = 0
        if level == 'easy':
            sleep(10)
    return True
