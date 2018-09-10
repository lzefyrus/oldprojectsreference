__author__ = 'sandro.lourenco'
import logging

from tornado_json.gen import coroutine
from tornado.web import MissingArgumentError

from rest.utils import DoesNotExist
from rest.utils import json_formats
from rest import RestDBAPIHandler

slog = logging.getLogger('restdb')
alog = logging.getLogger('access')

TF = ['true', 'false', 'True', 'False']
EMPTY = ['', None, False, 0]


class KeyHandler(RestDBAPIHandler):
    """
    AuthData
    """

    __urls__ = [r"/key/(?P<base>[a-zA-Z0-9_]+)/?$"]

    @coroutine
    def get(self, base):
        """
        :param base:
        :return:
        """
        try:
            user_id = self.get_argument('user', default=None, strip=True)
            id_estrangeiro = self.get_argument('cpf', default=None, strip=True)
            product = self.get_argument('product', default=None, strip=True)
            partner = self.get_argument('partner', default=None, strip=True)
            key = self.get_argument('key', default=None, strip=True)
            parceiro_id = self.get_argument(
                'parceiro_id', default=None, strip=True)
            tabela = 'VIEW_SSO_USER_DATA'
            fields = (
                'chave', 'cliente_id', 'nome', 'email', 'data_suspensao', 'data_cancelamento', 'produto_id',
                'parceiro_id',
                'id_estrangeiro')
            sql = "select %s from %s "

            db = self.db.get(base)

            if key is not None:
                sql = sql % (','.join(fields), tabela) + ' where chave=%s'
                qpar = [key]
            elif partner is not None:
                sql = sql % (','.join(fields),
                             tabela) + ' where parceiro_id=%s and cliente_id=%s and data_cancelamento is Null and data_suspensao is Null'
                qpar = [partner, user_id]
            elif id_estrangeiro is not None and parceiro_id is not None:
                sql = sql % (','.join(fields),
                             tabela) + ' where parceiro_id=%s and id_estrangeiro=%s and data_cancelamento is Null and data_suspensao is Null'
                qpar = [parceiro_id, id_estrangeiro]
            elif id_estrangeiro is not None:
                sql = sql % (','.join(fields),
                             tabela) + ' where produto_id=%s and id_estrangeiro=%s and data_cancelamento is Null and data_suspensao is Null'
                qpar = [product, id_estrangeiro]
            elif product is not None and user_id is not None:
                sql = sql % (','.join(fields),
                             tabela) + ' where produto_id=%s and cliente_id=%s and data_cancelamento is Null and data_suspensao is Null'
                qpar = [product, user_id]
            else:
                raise MissingArgumentError('data')
            cur = yield db.fexecute(sql, qpar, table=tabela, cnames=fields, expires=60)

            if cur and cur.value in ['', False, 0, None]:
                raise DoesNotExist

            self.success(json_formats(dict(zip(fields, cur.value))), True)

        except (DoesNotExist, TypeError):
            self.fail('Client Id not found', code=404)
        except MissingArgumentError as e:
            self.fail(e.log_message, code=e.status_code)
        except Exception as e:
            slog.error(e)
            self.error('General Oauth Error', code=500)


class KeyClientHandler(RestDBAPIHandler):
    """
    AuthData
    """

    __urls__ = [r"/key/client/(?P<base>[a-zA-Z0-9_]+)/?$"]

    def get(self, base):
        """

        :param base:
        :return:
        """
        try:

            raise DoesNotExist

        except DoesNotExist:
            self.fail('Method unavailable', code=404)
        except MissingArgumentError as e:
            self.fail(e.log_message, code=e.status_code)
        except Exception as e:
            slog.error(e)
            self.error('General Oauth Error', code=500)


class KeyCountHandler(RestDBAPIHandler):
    """
    AuthData
    """

    __urls__ = [r"/key/count/(?P<base>[a-zA-Z0-9_]+)/?$"]

    def get(self, base):
        """

        :param base:
        :return:
        """
        try:

            raise DoesNotExist

        except DoesNotExist:
            self.fail('Method unavailable', code=404)
        except MissingArgumentError as e:
            self.fail(e.log_message, code=e.status_code)
        except Exception as e:
            slog.error(e)
            self.error('General Oauth Error', code=500)


class KeyFHandler(RestDBAPIHandler):
    """
    AuthData
    """

    __urls__ = [r"/fkey/(?P<base>[a-zA-Z0-9_]+)/?$"]

    def get(self, base):
        """

        :param base:
        :return:
        """
        try:

            raise DoesNotExist

        except DoesNotExist:
            self.fail('Method unavailable', code=404)
        except MissingArgumentError as e:
            self.fail(e.log_message, code=e.status_code)
        except Exception as e:
            slog.error(e)
            self.error('General Oauth Error', code=500)
