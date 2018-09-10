__author__ = 'sandro.lourenco'
import logging

from tornado.web import MissingArgumentError
from tornado_json.gen import coroutine

from rest.utils import DoesNotExist
from rest.utils import json_formats

slog = logging.getLogger('restdb')
alog = logging.getLogger('access')

TF = ['true', 'false', 'True', 'False']
EMPTY = ['', None, False, 0]

from rest import RestDBAPIHandler


class ProductHandler(RestDBAPIHandler):
    """
    AuthData
    """

    __urls__ = [r"/products/(?P<base>[a-zA-Z0-9_]+)/?$"]

    @coroutine
    def get(self, base='ctbc'):
        """

        :param base:
        :return: product ids from a given partner
        """
        try:
            client_id = self.get_argument('client_id', strip=True)
            db = self.db.get(base)
            sql = "select p.%s from %s po"
            tabela = 'produtos_oauth'
            where = " join produtos p on p.id = po.produto_id where client_id = %s"
            fields = ['parceiro']

            sql = sql % (','.join(fields), tabela) + where
            slog.debug(sql, client_id)
            cur = yield db.fexecute(sql, (client_id), tabela, fields, 60 * 60 * 24)

            if cur and cur.value in ['', False, 0, None]:
                raise DoesNotExist

            self.success(json_formats(dict(zip(fields, cur.value))), True)

        except (DoesNotExist, ValueError):
            self.fail('Not found', code=404)
        except MissingArgumentError as e:
            self.fail(e.log_message, code=e.status_code)
        except Exception as e:
            slog.error(e)
            slog.error(sql)
            self.error('General Oauth Error', code=500)


class ProductInfo(RestDBAPIHandler):
    __urls__ = [r"/product/info/(?P<base>[a-zA-Z0-9_]+)/?$"]

    @coroutine
    def get(self, base):
        """

        :param base:
        :return:
        """
        try:
            user_id = self.get_argument('user_id', strip=True)
            db = self.db.get(base)
            extref = None
            sql = "select %s from %s"
            tabela = 'VIEW_APLICATIVO_AGREGADOR'
            where = " where id_cliente = %s"
            fields = (
            'id_cliente', 'id_produto', 'nome', 'nome_amigavel', 'tipo_produto', 'id_estrangeiro', 'valor', 'STATUS',
            'parceiro', 'descricao_pacote', 'download_link')

            settings = self.application.settings
            sql = sql % (','.join(fields), tabela) + where
            cur = yield db.fexecute(sql, (user_id), tabela, fields, 300)
            # slog.debug(sql % (client_id, user_id))
            # jdata = [dict(zip(fields, x) for x in cur.value)]
            # json = json_formats(jdata)
            self.success(cur.value, False)

        except (DoesNotExist, ValueError):
            self.fail('Not found', code=404)
        except MissingArgumentError as e:
            self.fail(e.log_message, code=e.status_code)
        except Exception as e:
            slog.error(e)
            slog.error(sql)
            self.error('General Oauth Error', code=500)


class OauthProductConfig(RestDBAPIHandler):
    __urls__ = [r"/oauth/config"]

    @coroutine
    def get(self):
        """
        :return:
        """
        try:
            base = self.get_argument('base', None)
            no_cache = self.get_argument('no_cache', None)
            db = self.db
            if base:
                db = {base: self.db.get(base)}

            sql = "select %s from %s"
            tabela = 'produtos_oauth'
            where = ' where is_active = %s'
            fields = ('produto_id', 'plataforma', 'client_id', 'client_secret', 'is_active', 'default_pass', 'config')
            sql = sql % (','.join(fields), tabela) + where

            result = {}
            for k, w in db.items():
                try:
                    if no_cache:
                        slog.error('no_cache TRUE==========')
                        cur = yield w.fexecute(sql, ('1'), tabela, fields, 1, True)
                    else:
                        slog.error('no_cache FALSE==========')
                        cur = yield w.fexecute(sql, ('1'), tabela, fields, 300)

                    tmpv = []
                    for i in cur.value:
                        tmpv.append(dict(zip(fields, i)))

                    result[k] = tmpv
                except Exception as e:
                    slog.error('Configuration error - {}'.format(e))

            self.success(result, False)

        except (DoesNotExist, ValueError):
            self.fail('Not found', code=404)
        except MissingArgumentError as e:
            self.fail(e.log_message, code=e.status_code)
        except Exception as e:
            slog.error(e)
            slog.error(k)
            slog.error(sql)
            self.error('General Oauth Error', code=500)
