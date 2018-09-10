import hashlib
import re
import logging
import requests
from urllib.parse import quote_plus
from tornado.httpclient import HTTPClient, HTTPRequest
from rest import utils

slog = logging.getLogger('restdb')


class VivoSyncService(object):

    stype = 'homol'
    settings = {}

    @property
    def clients(self):
        return self.settings['clients']

    def __init__(self, settings):
        slog.debug("&&&&& %s *****" % settings)
        self.stype = 'production' if settings['prddb'] is True else 'homol'
        self.settings = settings['config']['provisioner'][self.stype]['funambol']
        slog.debug("&&&&& %s *****" % self.stype)
        slog.debug("&&&&& %s *****" % self.settings)

    def check_login(self, id_estrangeiro):
        slog.debug("&&&&& %s *****" % id_estrangeiro)
        urlt = self.settings['host']
        slog.debug(urlt)
        old_id = id_estrangeiro
        url = urlt + id_estrangeiro
        slog.debug("&&&&& %s *****" % url)
        response = requests.get(url, timeout=5)
        slog.debug("## %s ##, %s" % (response.text, id_estrangeiro))
        if response.status_code is not 200:
            slog.debug("## %s ##, %s" % (response.text, id_estrangeiro))
            id_estrangeiro = utils.msisdn89(id_estrangeiro)
            url = urlt + id_estrangeiro
            response = requests.get(url, timeout=5)
            slog.debug("## %s ##, %s" % (response.text, id_estrangeiro))
            if response.status_code is not 200:
                return old_id
        return id_estrangeiro

class ClientService(object):

    @staticmethod
    def get_cliente_id_hash_md5(cliente_id):
        md5 = hashlib.md5()
        md5.update(repr(cliente_id).encode('utf-8'))
        return md5.hexdigest()

    @classmethod
    def update_provisioner(cls, extref, settings):
        url = cls._get_url_provisioner(extref, settings, 'fsecure')
        request = requests.post(url, timeout=10)
        slog.debug("Calling Provisionador. Request URL: {0}."
                   .format(url))
        return request

    @staticmethod
    def _get_url_provisioner(extref, settings, product, url_only=False):
        env = 'production' if settings['prddb'] is True else 'homol'
        provisioner_host = settings['config']['provisioner'][env][product]['host']
        if url_only:
            return provisioner_host

        url = "{0}/{1}?".format(provisioner_host, extref)
        parameters = "username={1}&email_addr={2}&first_name={3}&last_name={4}"\
            .format(extref, extref, quote_plus("{0}@fs.com.br".format(extref)), extref, extref)

        return url + parameters

    @staticmethod
    def is_secure(parceiro):
        try:
            p = re.compile(r'([a-zA-Z])', re.IGNORECASE)
            is_secure = True if ''.join(re.findall(p, parceiro)).lower() == 'fsecure' else False
            slog.debug("Is secure: {0}".format(is_secure))
            return is_secure
        except Exception as e:
            slog.error("Error on products API is_secure method. Partner: {0}. Error: {1}"
                       .format(parceiro, e))
            return False
