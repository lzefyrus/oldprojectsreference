# -*- encoding: utf-8 -*-

import requests
import uuid
from application.src.exceptions import MethodNotImplemented
from application.src.celeryapp import CeleryApp, Configs
from application import settings

# Celery App
celery = CeleryApp.get_instance()

# Log Hash
LOG_HASH_MT = settings.LOG_HASHES["application"]["mt"]


class MtService(object):
    """
    Generic MT service.
    """

    @staticmethod
    def get_configs(configs):
        raise MethodNotImplemented("Method 'get_configs' must be implemented")

    @staticmethod
    def send(configs, msisdn, la, text, callback=None):
        raise MethodNotImplemented("Method 'send' must be implemented")


class MtTim(MtService):
    """
    MT service for Tim.
    """

    carrier = "tim"

    @staticmethod
    def get_configs(configs):
        """
        Returns useful configs.
        :param configs:
        :return:
        """
        return {
            "user": configs['tim/fit/user']['value'],
            "password": configs['tim/fit/password']['value'],
            "host": configs['tim/fit/host']['value'],
            "mt_url": configs['tim/fit/mt/url']['value'],
        }

    @staticmethod
    @celery.task(base=Configs)
    def send(configs, msisdn, la, text, callback=None):
        """
        Sends MT.
        :return:
        """
        text = text.replace(' ', '+')
        uri = "{0}/{1}".format(configs['host'], configs['mt_url'])

        try:
            url = "{0}&msisdn={1}&msg={2}&la={3}&pass={4}&user={5}&priority="\
                .format(uri, msisdn, text, la, configs['password'], configs['user'])

            response = requests.get(url=url, timeout=10)

            MtTim.send.log.info("MT request sent. "
                                "Request URL: {0}. "
                                "Response code: {1}. "
                                "Response body: {2}. "
                                "Operation Hash: {3}."
                                .format(url, response.status_code, response.text, LOG_HASH_MT))
            return response

        except Exception as e:
            MtTim.send.log.error("Could not send MT. "
                                 "Request URL: {0}. "
                                 "Msisdn: {1}. "
                                 "LA: {2}. "
                                 "Text: {3}. "
                                 "Error: {4}. "
                                 "Operation Hash: {5}."
                                 .format(uri, msisdn, la, text, e, LOG_HASH_MT))


class MtOi(MtService):
    """
    MT service for Oi.
    """

    carrier = "oi"

    @staticmethod
    def get_configs(configs):
        """
        Returns useful configs.
        :param configs:
        :return:
        """
        return {
            "host": configs['oi/host']['value'],
            "mt_url": configs['oi/mt/url']['value'],
        }

    @staticmethod
    @celery.task(base=Configs, name="application.oi.mt")
    def send(configs, msisdn, la, text, callback=None):
        """
        Sends MT.
        :return:
        """
        uri = "{0}/{1}".format(configs['host'], configs['mt_url'])

        try:
            url = "{0}?la={1}&msisdn={2}&text={3}&uid={4}".format(uri, la, msisdn, text, uuid.uuid4().hex)

            headers = {
                "tunnel-key": "5ab592fdd5364b8e831f50de14901b35",
                "user-key": "oi-backend",
                "user-secret": "a0fadee67cb447bc9bbd7a568178cc99"
            }

            response = requests.get(url=url, headers=headers, timeout=3)

            MtOi.send.log.info("MT request sent. "
                               "Request URL: {0}. "
                               "Response code: {1}. "
                               "Response body: {2}. "
                               "Operation Hash: {3}."
                               .format(url, response.status_code, response.text, LOG_HASH_MT))
            return response

        except Exception as e:
            MtOi.send.log.error("Could not send MT. "
                                "Request URL: {0}. "
                                "Msisdn: {1}. "
                                "LA: {2}. "
                                "Text: {3}. "
                                "Error: {4}. "
                                "Operation Hash: {5}."
                                .format(uri, msisdn, la, text, e, LOG_HASH_MT))


class MtVivo(MtService):
    """
    MT service for Vivo.
    """

    carrier = "vivo"

    @staticmethod
    def get_configs(configs):
        """
        Returns useful configs.
        :param configs:
        :return:
        """
        return {
            "user": configs['vivo/user']['value'],
            "password": configs['vivo/password']['value'],
            "host": configs['vivo/host']['value'],
            "mt_url": configs['vivo/mt/url']['value'],
        }

    @staticmethod
    @celery.task(base=Configs, name="application.vivo.mt")
    def send(configs, msisdn, la, text, callback=None):
        """
        Sends MT.
        :return:
        """
        uri = "{0}/{1}".format(configs['host'], configs['mt_url'])

        try:
            url = "{0}?msisdn={1}&mensagem={2}&la={3}&codigo={4}&binary={5}&usuario={6}&senha={7}"\
                .format(uri, msisdn, text, la, uuid.uuid4().hex, "false",  configs['user'], configs['password'])

            response = requests.post(url=url, timeout=10)

            MtVivo.send.log.info("MT request sent. "
                                 "Request URL: {0}. "
                                 "Response code: {1}. "
                                 "Response body: {2}. "
                                 "Operation Hash: {3}."
                                 .format(url, response.status_code, response.text, LOG_HASH_MT))
            return response

        except Exception as e:
            MtVivo.send.log.error("Could not send MT. "
                                  "Request URL: {0}. "
                                  "Msisdn: {1}. "
                                  "LA: {2}. "
                                  "Text: {3}. "
                                  "Error: {4}. "
                                  "Operation Hash: {5}."
                                  .format(uri, msisdn, la, text, e, LOG_HASH_MT))


class MtNextel(MtService):
    """
    MT service for Nextel.
    """

    carrier = "oi"

    @staticmethod
    def get_configs(configs):
        """
        Returns useful configs.
        :param configs:
        :return:
        """
        return {
            "host": configs['nextel/host']['value'],
            "mt_url": configs['nextel/mt/url']['value'],
            "channel": configs['nextel/mt/channel']['value'],
        }

    @staticmethod
    @celery.task(base=Configs, name="application.nextel.mt")
    def send(configs, msisdn, la, text, callback=None):
        """
        Sends MT.
        :return:
        """
        uri = "{0}/{1}".format(configs['host'], configs['mt_url'])

        try:
            url = "{0}?la={1}&msisdn={2}&text={3}&uid={4}".format(uri, la, msisdn, text, uuid.uuid4().hex)

            headers = {
                "tunnel-key": "c8796590b179d40d98aaab2192546jvd",
                "user-key": "nextel-backend",
                "user-secret": "12edasdeedwfdsftg7bc9bbd7a5213re",
                "Content-Type": "application/json"
            }

            body = {
                "channel_id": configs['channel'],
                "message": text,
                "msisdns": msisdn,
                "la": la
            }

            response = requests.post(url=url, headers=headers, json=body, timeout=3)

            MtOi.send.log.info("MT request sent. "
                               "Request URL: {0}. "
                               "Response code: {1}. "
                               "Response body: {2}. "
                               "Operation Hash: {3}."
                               .format(url, response.status_code, response.text, LOG_HASH_MT))
            return response

        except Exception as e:
            MtOi.send.log.error("Could not send MT. "
                                "Request URL: {0}. "
                                "Msisdn: {1}. "
                                "LA: {2}. "
                                "Text: {3}. "
                                "Error: {4}. "
                                "Operation Hash: {5}."
                                .format(uri, msisdn, la, text, e, LOG_HASH_MT))


class MtAlgar(MtService):
    """
    MT service for Algar.
    """

    carrier = "oi"

    @staticmethod
    def get_configs(configs):
        """
        Returns useful configs.
        :param configs:
        :return:
        """
        return {
            "host": configs['algar/host']['value'],
            "mt_url": configs['algar/mt/url']['value'],
            "channel": configs['algar/mt/channel']['value'],
        }

    @staticmethod
    @celery.task(base=Configs, name="application.algar.mt")
    def send(configs, msisdn, la, text, callback=None):
        """
        Sends MT.
        :return:
        """
        uri = "{0}/{1}".format(configs['host'], configs['mt_url'])

        try:
            url = "{0}?la={1}&msisdn={2}&text={3}&uid={4}".format(uri, la, msisdn, text, uuid.uuid4().hex)

            headers = {
                "tunnel-key": "cae8390b179d40d98aaab21928ebcf75",
                "user-key": "algar-backend",
                "user-secret": "e9c636cf9d0e404fb615c361ca3660ea",
                "Content-Type": "application/json"
            }

            body = {
                "channel_id": configs['channel'],
                "message": text,
                "msisdns": msisdn,
                "la": la
            }

            response = requests.post(url=url, headers=headers, json=body, timeout=3)

            MtOi.send.log.info("MT request sent. "
                               "Request URL: {0}. "
                               "Response code: {1}. "
                               "Response body: {2}. "
                               "Operation Hash: {3}."
                               .format(url, response.status_code, response.text, LOG_HASH_MT))
            return response

        except Exception as e:
            MtOi.send.log.error("Could not send MT. "
                                "Request URL: {0}. "
                                "Msisdn: {1}. "
                                "LA: {2}. "
                                "Text: {3}. "
                                "Error: {4}. "
                                "Operation Hash: {5}."
                                .format(uri, msisdn, la, text, e, LOG_HASH_MT))
