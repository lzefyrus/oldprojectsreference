# -*- coding: utf-8 -*-

import datetime
import logging
import re

import requests
from lxml.html import fromstring
from tornado_json import schema
from tornado_json.gen import coroutine

from game.models import User
from utils import APIHandler, time_to_life, has_life

log = logging.getLogger(__name__)

xstr = lambda s: s or ""

xint = lambda s: s or 0

USER_OUT_SCHEMA = {
    "type": "object",
    "properties": {
        "address": {"type": "string"},
        "city": {"type": "string"},
        "email": {"type": "string"},
        "lives": {"type": "integer"},
        "id": {"type": "integer"},
        "cpf": {"type": "string"},
        "mobile": {"type": "string"},
        "cep": {"type": "string"},
        "numb": {"type": "string"},
        "name": {"type": "string"},
        "missing": {"type": "object"},
        "neighborhood": {"type": "string"},
        "complete": {"type": "string"},
        "nextLife": {"type": "integer"},
        "firstAccess": {"type": "boolean"},
        "state": {"type": "string"},
        "status": {"type": "string"},
        "avatar": {"type": "object"},
        "shareUrl": {"type": "string"}
    }
}

USER_OUT_EXAMPLE = {
    "address": "rua das couves 32",
    "city": "sao paulo",
    "email": "asd@asd.com",
    "lives": 3,
    "cpf": '32165498721',
    "id": 32165498721,
    "missing": {
        "gamelevel": "easy"
    },
    "mobile": '11991919191',
    "cep": '4578890',
    "numb": '12',
    "neighborhood": "Jardim Europa",
    "complete": "fundos",
    "name": "Next Gamer 1",
    "firstAccess": False,
    "nextLife": 1150,
    "state": "sp",
    "status": "success",
    "avatar": {"small": "http://facebook/smallpic",
               "big": "http://facebook/bigpic"},
    "shareUrl": "http://api.next.me/ojads90812h09812asdpaspiwq1"
}


class UserAPIHandler(APIHandler):
    __url_names__ = ["user"]

    def initialize(self):
        self.db = self.application.settings.get('engine')

    @schema.validate(

        output_schema=USER_OUT_SCHEMA,
        output_example=USER_OUT_EXAMPLE,
    )
    @coroutine
    def get(self):
        user = self.db.get(User, id=self.session.get(
            'id'), facebook_id=self.session.get('facebook_id'))
        lives = has_life(self, False)
        missing_week = {}
        tmp = ''
        if user.is_dirty is True and user.win is not None:
            for k, w in user.win.items():
                if w.get('now', '') >= tmp:
                    missing_week = w.copy()
                    missing_week['week'] = int(missing_week['week'])
                    tmp = missing_week['now']
        data = {"status": "success",
                "nextLife": time_to_life(self.session.get('last_dec', 0)),
                "email": xstr(user.email),
                "state": xstr(user.state),
                "id": user.facebook_id,
                "city": xstr(user.city),
                "address": xstr(user.address),
                "cpf": xstr(user.cpf),
                "missing": missing_week,
                "name": xstr(user.name),
                "neighborhood": xstr(user.neighborhood),
                "complete": xstr(user.compl),
                "numb": xstr(user.numb),
                "mobile": str(int(user.mobile)) if user.mobile is not None else '',
                "cep": xstr(user.cep),
                "firstAccess": bool(user.firstAccess),
                "shareUrl": xstr('{}/referral/{}'.format(self.application.settings.get('instance', {}).get('api', ''),
                                                         user.referral)),
                "lives": int(lives),
                "avatar": xstr(user.avatar)}
        return data

    @schema.validate(input_schema={
        "type": "object",
        "properties": {
            "mobile": {"oneOf": [
                {"type": "integer", "minLength": 10},
                {"type": "string", "minLength": 10}
            ]},
            "state": {"type": "string", "minLength": 2, "maxLength": 2},
            "city": {"type": "string", "minLength": 2},
            "address": {"type": "string", "minLength": 5},
            "cep": {"type": "string", "minLength": 5},
            "numb": {"type": "string", "minLength": 1},
            "complete": {"oneOf": [
                {"type": "string", "minLength": 1},
                {"type": "string", "maxLength": 0}
            ]},
            "neighborhood": {"type": "string", "minLength": 2},
            "cpf": {"type": "string", "minLength": 8},
            "email": {"type": "string", "minLength": 6, "format": "email"},
            "optin": {"oneOf": [
                {"type": "boolean"},
                {"type": "string"}
            ]},
        },
        "required": ["state", "city", "address", "email", "optin"]
    },
        input_example={
            "state": "SP",
            "city": "Sao Paulo",
            "cpf": '32165498721',
            "address": "Rua das couves",
            "email": "rga@rga.com.br",
            "optin": True,
            "mobile": '11991919191',
            "cep": '32165',
            "numb": '25',
            "complete": "fundos",
            "neighborhood": "bairro X",

        },
        output_schema=USER_OUT_SCHEMA,
        output_example=USER_OUT_EXAMPLE
    )
    @coroutine
    def post(self):
        sendMail = False
        prize = None
        log.warning(self.body)
        user = self.db.get(User,
                           id=self.session.get('id'),
                           facebook_id=self.session.get('facebook_id'))
        user.address = self.body['address']
        user.state = self.body['state']
        user.cpf = self.body['cpf'] or ''
        user.email = self.body['email']
        user.city = self.body['city']
        user.name = self.body['name']
        user.neighborhood = self.body['neighborhood']
        if self.body['complete'] not in ['', None, 0]:
            user.compl = self.body['complete']
        user.numb = str(self.body['numb'])
        user.mobile = str(self.body['mobile'])
        user.cep = self.body['cep']
        user.updated_at = datetime.datetime.utcnow()
        tmpwinlist = user.win_email or []
        tmpwin = user.win
        if user.is_dirty is True and user.win is not None:
            for k, w in tmpwin.items():
                if k not in tmpwinlist:
                    tmpwinlist.append(k)
                    sendMail = True
                    prize = w
        log.info(tmpwinlist)
        user.win_email = tmpwinlist
        user.is_dirty = False
        self.db.sync(user)
        try:
            log.info(user.win)
        except:
            log.info(str(user.win))
        lives = has_life(self, False)
        data = {"status": "success",
                "nextLife": time_to_life(self.session.get('last_dec', 0)),
                "email": xstr(user.email),
                "id": user.facebook_id,
                "state": xstr(user.state),
                "city": xstr(user.city),
                "address": xstr(user.address),
                "cpf": xstr(user.cpf),
                "missing": {},
                "name": xstr(user.name),
                "neighborhood": xstr(user.neighborhood),
                "complete": xstr(user.compl),
                "numb": xstr(user.numb),
                "mobile": str(int(user.mobile)) if user.mobile is not None else '',
                "cep": xstr(user.cep),
                "firstAccess": bool(user.firstAccess),
                "shareUrl": xstr('{}/referral/{}'.format(self.application.settings.get('instance', {}).get('api', ''),
                                                         user.referral)),
                "lives": int(lives),
                "avatar": xstr(user.avatar)}

        if sendMail is True and prize is not None:
            yield self.send_mail(user, prize)

        return data

    @coroutine
    def send_mail(self, user, prize):
        try:
            mail = self.application.settings.get('mailer')
            dets = prize.get('prize', {}).get('details')

            if len(dets) == 2:
                dets.append('')

            cmpl = ', {}'.format(user.compl) if user.compl else ''
            addess = '{}, {}{} - {}-{} - {}'.format(user.address, user.numb, cmpl,
                                                    user.city, user.state.upper(), user.cep)
            path = '{}/assets'.format(
                self.application.settings.get('instance', {}).get('front'))
            mail.send(to=user.email,
                      format='html',
                      subject="Parabéns, você achou a combinação certa!",
                      body=self.render_string(
                          "template-prize.html",
                          prizeTitle=prize.get('prize').get('name'),
                          prizeImg=prize.get('prize').get('img'),
                          path=path,
                          prizeDetail1=dets[0],
                          prizeDetail2=dets[1],
                          prizeDetail3=dets[2],
                          prizeSendAddress=addess))
        except Exception as e:
            log.warn(e)
            log.warn('WINNER MAIL not sent to user {} and email {}. \n traceback: {}'.format(
                user.name, user.email, e))

    @schema.validate(output_schema=USER_OUT_SCHEMA,
                     output_example=USER_OUT_EXAMPLE, )
    @coroutine
    def put(self):
        user = self.db.get(User, id=self.session.get(
            'id'), facebook_id=self.session.get('facebook_id'))
        user.firstAccess = 0
        user.updated_at = datetime.datetime.utcnow()
        self.db.sync(user)
        lives = has_life(self, False)
        data = {"status": "success",
                "nextLife": time_to_life(self.session.get('last_dec', 0)),
                "email": xstr(user.email),
                "state": xstr(user.state),
                "city": xstr(user.city),
                "id": user.facebook_id,
                "address": xstr(user.address),
                "cpf": xstr(user.cpf),
                "missing": {},
                "name": xstr(user.name),
                "neighborhood": xstr(user.neighborhood),
                "complete": xstr(user.compl),
                "numb": xstr(user.numb),
                "mobile": str(user.mobile) if user.mobile is not None else '',
                "cep": xstr(user.cep),
                "firstAccess": bool(user.firstAccess),
                "shareUrl": xstr('{}/referral/{}'.format(self.application.settings.get('instance', {}).get('api', ''),
                                                         user.referral)),
                "lives": int(lives),
                "avatar": xstr(user.avatar)}
        return data


class PingAPIHandler(APIHandler):
    __url_names__ = ["ping"]

    def initialize(self):
        pass

    @schema.validate(

        output_schema={
            "type": "object",
            "properties": {
                "extraLives": {"type": "boolean"},
                "nextLife": {"type": "integer"},
                "message": {"type": "string"},
                "status": {"type": "string"},
            }
        },
        output_example={
            "extraLives": False,
            "message": "",
            "nextLife": 1150,
            "status": "success",
        },
    )
    @coroutine
    def get(self):
        ret = {
            "extraLives": False,
            "message": "",
            "nextLife": 1150,
            "status": "success",
        }

        ping = self.db_conn.get('ping').get(self.session.get("id"))
        if ping:
            self.db_conn.get('ping').delete(self.session.get("id"))
            ret['extraLives'] = True
        ret['nextLife'] = time_to_life(self.session.get('last_dec', 0))

        return ret


class CepAPIHandler(APIHandler):
    __url_names__ = ["cep"]

    def initialize(self):
        pass

    @schema.validate(

        output_schema={
            "type": "object",
            "properties": {
                "address": {"type": "string"},
                "neighborhood": {"type": "string"},
                "city": {"type": "string"},
                "state": {"type": "string"},
            }
        },
        output_example={
            "address": "adsadsdas",
            "neighborhood": "adsadsdas",
            "city": "adsadsdas",
            "state": "adsadsdas",
        },
    )
    @coroutine
    def get(self, cep):

        res = self.viacep(cep)
        if res:
            return res

        itens = self._get_infos_(cep)
        result = []

        found = False
        now = datetime.datetime.now()

        for item in itens:
            data = {}

            for label, value in zip(item[0::2], item[1::2]):

                label = label.lower().strip(' :')
                value = re.sub('\s+', ' ', value.strip())

                if 'localidade' in label:
                    cidade, estado = value.split('/', 1)
                    data['city'] = cidade.strip()
                    data['state'] = estado.split('-')[0].strip()
                elif 'logradouro' in label and ' - ' in value:
                    logradouro, complemento = value.split(' - ', 1)
                    data['address'] = logradouro.strip()
                    # data['complemento'] = complemento.strip(' -')
                elif label == 'logradouro':
                    data['address'] = value.strip()
                    # data['complemento'] = complemento.strip(' -')
                elif label == u'endereço':
                    # Use sempre a key `endereco`. O `endereço` existe para não
                    # quebrar clientes existentes. #92
                    data['address'] = data[label] = value
                elif label == u'bairro':
                    data['neighborhood'] = value
                else:
                    if label == 'cep' and value == cep:
                        found = True
                    data[label] = value

                result.append(data)

        if not found:
            return {
                "address": "",
                "neighborhood": "",
                "city": "",
                "state": "",
            }
        return result[0]

    def viacep(self, cep):
        vcep = requests.get(
            'https://viacep.com.br/ws/{}/json/unicode/'.format(cep))
        try:
            vcep.raise_for_status()
            cc = vcep.json()
        except requests.exceptions.HTTPError as ex:
            log.exception('Erro no site dos Correios')
            return None

        return {
            "address": cc.get('logradouro'),
            "neighborhood": cc.get('bairro'),
            "city": cc.get('localidade'),
            "state": cc.get('uf'),
        }

    def _request(self, cep):
        self.url = 'http://m.correios.com.br/movel/buscaCepConfirma.do'
        response = requests.post(self.url, data={
            'cepEntrada': cep,
            'tipoCep': '',
            'cepTemp': '',
            'metodo': 'buscarCep'
        }, timeout=10)
        try:
            response.raise_for_status()
        except requests.exceptions.HTTPError as ex:
            log.exception('Erro no site dos Correios')
            raise ex
        return response.text

    def _get_infos_(self, cep):
        response = self._request(cep)
        html = fromstring(response)
        registro_csspattern = '.caixacampobranco, .caixacampoazul'
        registros = html.cssselect(registro_csspattern)

        resultado = []
        for item in registros:
            item_csspattern = '.resposta, .respostadestaque'
            resultado.append([a.text for a in item.cssselect(item_csspattern)])

        return resultado
