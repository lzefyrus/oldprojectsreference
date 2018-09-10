__author__ = 'sandro.lourenco'
import logging

from tornado_json.gen import coroutine
from tornado.web import MissingArgumentError

from rest.utils import DoesNotExist, json_formats, msisdn89
from services.client import ClientService, VivoSyncService


slog = logging.getLogger('restdb')
alog = logging.getLogger('access')

TF = ['true', 'false', 'True', 'False']
EMPTY = ['', None, False, 0]

from rest import RestDBAPIHandler


class AuthHandler(RestDBAPIHandler):
    """
    AuthData
    """

    __urls__ = [r"/auth/(?P<base>[a-zA-Z0-9_]+)/?$", r"/auth/uui/(?P<base>[a-zA-Z0-9_]+)/?$"]
    # __url_names__ = ["auth"]

    @coroutine
    def get(self, base):
        """

        :param base:
        :return:
        """
        try:
            ref = self.get_argument('email', strip=True)
            if ref in ['', None, False, 0, []]:
                raise MissingArgumentError

            tabela = 'clientes'
            sql = "select %s from %s "

            if base in ['hero']:
                where = " where msisdn=%s or email=%s or cpf=%s or id_estrangeiro=%s"
            else:
                where = " where email=TRIM(%s) or id_estrangeiro=TRIM(%s)"

            uid = self.get_argument('user_id', default=None, strip=True)
            if uid not in EMPTY:
                where = " where id=%s"

            db = self.db.get(base)
            fields = ('id', 'nome', 'email', 'ativo', 'criado', 'id_estrangeiro')
            slog.debug(fields)
            slog.debug(ref)
            sql = sql % (','.join(fields), tabela) + where
            cur = yield db.fexecute(sql, (ref, ref, ref, ref), tabela, fields, 60)

            if cur and cur.value in ['', False, 0, None]:
                raise DoesNotExist

            self.success(dict(zip(fields, cur.value)), True)

        except (DoesNotExist, TypeError):
            self.fail('Client Id not found', code=404)
        except MissingArgumentError as e:
            self.fail(e.log_message, code=e.status_code)
        except Exception as e:
            slog.error(e)
            self.error('General Oauth Error', code=500)

    @coroutine
    def post(self, base):
        """
        get user data from server
        :param base:
        :return: json data
        """

        try:
            ref = self.get_argument('email', strip=True)
            if ref in ['', None, False, 0, []]:
                raise MissingArgumentError

            tabela = 'clientes'
            sql = "select %s from %s "

            where = " where msisdn=%s or email=%s or cpf=%s or id_estrangeiro=%s"

            fields = ('id', 'nome', 'email', 'ativo', 'criado', 'removido', 'alterado', 'senha', 'id_estrangeiro')

            uid = self.get_argument('user_id', default=None, strip=True)
            if uid not in EMPTY:
                where = " where id=%s"

            sql = sql % (','.join(fields), tabela) + where
            db = self.db.get(base)
            cur = yield db.fexecute(sql, (ref, ref, ref, ref), tabela, fields, 5)

            if cur and cur.value in ['', False, 0, None]:
                # if base == 'vivo':
                #     ref = msisdn89(ref)
                #     cur = yield db.fexecute(sql, (ref, ref, ref, ref), tabela, fields, 5)
                #     if cur and cur.value in ['', False, 0, None]:
                #         raise DoesNotExist
                # else:
                raise DoesNotExist

            self.success(json_formats(dict(zip(fields, cur.value))), True)

        except (DoesNotExist, TypeError):
            self.fail('UNAUTHORIZED', code=401)
        except MissingArgumentError as e:
            self.fail(e.log_message, code=e.status_code)
        except Exception as e:
            slog.error(e)
            self.error('General Oauth Error', code=500)


class ClientHandler(RestDBAPIHandler):
    """
    AuthData
    """

    __urls__ = [r"/client/(?P<base>[a-zA-Z0-9_]+)/?$"]

    @coroutine
    def get(self, base):
        """

        :param base:
        :return:
        """
        try:
            ref = self.get_argument('client_id', strip=True)
            # ref2 = self.get_argument('client_secret', strip=True)
            if ref in ['', None, False, 0, []]:
                raise MissingArgumentError

            db = self.db.get(base)
            tabela = 'produtos_oauth'
            sql = "select %s from %s"
            where = "  where client_id=%s"
            fields = ('produto_id', 'client_id', 'redirect_uris', 'scopes')
            sql = sql % (','.join(fields), tabela) + where

            cur = yield db.fexecute(sql, (ref), tabela, fields, 60)

            if cur and cur.value in ['', False, 0, None]:
                raise DoesNotExist

            self.success(json_formats(dict(zip(fields, cur.value))), True)

        except (DoesNotExist, TypeError):
            self.fail('Not found', code=404)
        except MissingArgumentError as e:
            self.fail(e.log_message, code=e.status_code)
        except Exception as e:
            slog.error(e)
            self.error('General Oauth Error', code=500)

    @coroutine
    def post(self, base):
        try:
            cid = self.get_argument('client_id', strip=True)
            cse = self.get_argument('client_secret', strip=True)
            db = self.db.get(base)
            tabela = 'produtos_oauth'
            sql = "select %s from %s"
            where = " where client_id=%s and client_secret=%s"
            fields = ('produto_id', 'client_id', 'redirect_uris', 'scopes')
            sql = sql % (','.join(fields), tabela) + where

            cur = yield db.fexecute(sql, (cid, cse), tabela, fields, 60)

            if cur and cur.value in ['', False, 0, None]:
                raise DoesNotExist

            self.success(json_formats(dict(zip(fields, cur.value))), True)

        except (DoesNotExist, TypeError):
            self.fail('Not found', code=404)
        except MissingArgumentError as e:
            self.fail(e.log_message, code=e.status_code)
        except Exception as e:
            slog.error(e)


class ClientDataHandler(RestDBAPIHandler):
    """
    AuthData
    """

    # __urls__ = [r"/clientedados/?", r"/clientedados?"]

    def get(self, base='vivo'):
        """

        :param base:
        :return:
        """
        try:
            self.success({}, True)
        except (DoesNotExist, TypeError):
            self.fail('Client Id not found', code=401)
        except Exception as e:
            slog.error(e)
            self.error('General Oauth Error', code=500)


class ClientKeyHandler(RestDBAPIHandler):
    __urls__ = [r"/user/key/(?P<base>[a-zA-Z0-9_]+)/?$"]
    @coroutine
    def get(self,base):
        try:
            db = self.db.get(base)
            chave_id = self.get_argument('chave_id', strip=True)
            sql = "select %s from %s"
            tabela = 'chaves'
            where = " where id = %s limit 1"
            fields = ['chave']
            settings = self.application.settings
            sql = sql % (','.join(fields), tabela) + where
            cur = yield db.fexecute(sql, (chave_id), tabela, fields, 5, True)
            self.success(dict(zip(fields,cur.value)), True)
        except (DoesNotExist, ValueError):
            self.fail('Not found', code=404)
        except MissingArgumentError as e:
            self.fail(e.log_message, code=e.status_code)
        except Exception as e:
            slog.error(e)
            slog.error(sql)
            self.error('General Oauth Error', code=500)

class ClientInfoHandler(RestDBAPIHandler):
    """
    AuthData
    """

    __urls__ = [r"/user/info/(?P<base>[a-zA-Z0-9_]+)/?$"]

    @coroutine
    def get(self, base):
        """

        :param base:
        :return:
        """
        try:
            client_id = "{}%".format(self.get_argument('client_id', strip=True))
            user_id = self.get_argument('user_id', strip=True)
            no_cache = self.get_argument('no_cache', None)
            db = self.db.get(base)
            extref = None
            sql = "select %s from %s"

            tabela = 'VIEW_SSO_USER_DATA'

            where = " where client_id like %s and cliente_id=%s and data_cancelamento is Null and data_suspensao is Null "
            #where = " where client_id like %s and cliente_id=%s "

            fields = [
                'cliente_id', 'id_estrangeiro', 'chave_id', 'produto_id', 'parceiro_id', 'client_id', 'cpf', 'nome',
                'email', 'chave', 'data_suspensao', 'data_cancelamento']

            settings = self.application.settings
            if base in ['vivo', 'tim', 'hero', 'gvt']:
                fields.append('extref')
                extref = None

            if base in ['vivo']:
                fields.append('msisdn')

            if base in ['hero']:
                where += " and is_active = 1 "

            sql = sql % (','.join(fields), tabela) + where
            if no_cache:
                cur = yield db.fexecute('{} {}'.format(sql, " limit 1"), (client_id, user_id), tabela, fields, 5, True)
            else:
                cur = yield db.fexecute(sql, (client_id, user_id), tabela, fields, 5)

            slog.debug(sql % (client_id, user_id))

            if cur and cur.value in ['', False, 0, None]:
                #if cur.value[10] not in ['', False, 0, None] and base in ['vivo','gvt']:
                    #import datetime
                    #date_present = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                    #data_suspensao = time.strptime(cur.value[10],"%Y-%m-%d %H:%M:%S")
                    #if data_suspensao < date_present:
                        #raise DoesNotExist
                #elif cur.value[11] not in ['', False, 0, None]:
                    #raise DoesNotExist

                funvivo = VivoSyncService(settings)
                slog.debug(funvivo)
                slog.debug(client_id)
                slog.debug(funvivo.clients)
                if base == 'vivo' and client_id.replace('%', '') in funvivo.clients:
                    cur = yield db.fexecute(sql, (funvivo.clients.split(' ')[-1], user_id), tabela, fields, 5)
                    if cur and cur.value in ['', False, 0, None, []]:
                        slog.debug("EMPTY ERROR")
                        raise DoesNotExist
                    extref = funvivo.check_login(str(cur.value[1]))
                else:
                    raise DoesNotExist

            jdata = dict(zip(fields, cur.value))
            if extref:
                jdata['extref'] = extref
            json = json_formats(jdata)

            if base == 'vivo':
                sql = "select p.%s from %s po"
                tabela = "produtos_oauth"
                where = " join produtos p on p.id = po.produto_id where client_id = %s"
                fields = ['parceiro']

                sql = sql % (','.join(fields), tabela) + where
                slog.debug(sql, fields)
                cur = yield db.fexecute(sql, (client_id.replace("%", "")), tabela, fields, 60 * 60 * 24)
                if cur and cur.value not in ['', False, 0, None]:
                    slog.debug("Cursor parceiro: {0}".format(cur.value))
                    partner_json = json_formats(dict(zip(fields, cur.value)))

                    if ClientService.is_secure(partner_json['parceiro']):
                        slog.debug("Analysing OneId rule...")
                        try:
                            extref = json['extref']
                            if extref in ['', False, 0, None]:
                                slog.debug("Analysing legacy accounts...")
                                sql2 = "select %s from %s"
                                tabela2 = "chaves"
                                where2 = " where id = %s AND DATE(data_compra) <= '2016-03-02'"
                                fields2 = ['data_compra']
                                sql2 = sql2 % (','.join(fields2), tabela2) + where2
                                slog.debug(sql2 % json['chave_id'])
                                cur2 = yield db.fexecute(sql2, (str(json['chave_id'])), tabela2, fields2, 60)
                                if not cur2 or (cur2 and cur2.value not in ['', False, 0, None]):
                                    raise KeyError
                                else:
                                    slog.debug("New accout, canelling OneId rule.")
                            else:
                                slog.debug("Extref already exists! Cancelling OneId rule.")
                        except KeyError:
                            slog.debug("Applying OneId rule...")
                            try:
                                extref = ClientService.get_cliente_id_hash_md5(json['cliente_id'])
                                slog.debug("Cliente_id: {0}. The new extref is: {1}".format(json['cliente_id'], extref))

                                # 1- Update Provisionador:
                                response = ClientService.update_provisioner(extref, settings)
                                slog.debug('Request sent to Provisionador. '
                                           'Response Code: {0}.'
                                           'Cliente_id: {1}.'
                                           'Extref: {2}'
                                           .format(response.status_code, json['cliente_id'], extref))

                                # 2- Update database:
                                sql = "UPDATE chaves SET extref = %s WHERE id = %s"
                                cur = yield db.execute(sql, (extref, json['chave_id']))
                                slog.info("Updating extref on database: {0}".format(sql))

                                # 3- Update return:
                                json['extref'] = extref
                            except Exception as e:
                                slog.error("Error at migrating cliente_id: {0} to extref, base: '{1}'. Error: {2}"
                                           .format(json['cliente_id'], 'vivo', e))

            self.success(json, True)

        except (DoesNotExist, ValueError):
            self.fail('Not found', code=404)
        except MissingArgumentError as e:
            self.fail(e.log_message, code=e.status_code)
        except Exception as e:
            slog.error(e)
            slog.error(sql)
            self.error('General Oauth Error', code=500)


class StatusHandler(RestDBAPIHandler):
    """
    AuthData
    """

    __urls__ = [r"/status/(?P<base>[a-zA-Z0-9_]+)/?$"]

    @coroutine
    def get(self, base='ctbc'):
        """

        :param base:
        :return:
        """
        try:
            db = self.db.get(base)
            sql = "select max(id) from produtos"
            tabela = 'produtos'
            fields = ['id']

            cur = yield db.fexecute(sql, None, tabela, fields, 1)
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

class ClientProductInfo(RestDBAPIHandler):
    __urls__ = [r"/client/product/info/(?P<base>[a-zA-Z0-9_]+)/?$"]

    @coroutine
    def get(self, base='vivo'):
        try:
            db = self.db.get(base)
            slog.debug("database=%s"%(base))
            msisdn = self.get_argument('msisdn', strip=True)
            if msisdn in EMPTY:
                raise MissingArgumentError
            start_date = self.get_argument('start', strip=True)
            if start_date in EMPTY:
                raise MissingArgumentError
            end_date = self.get_argument('end', strip=True)
            if end_date in EMPTY:
                raise MissingArgumentError
            sql = "select %s from %s"
            tabela = "VIEW_PESQUISA_PRODUTO_CLIENTE"
            where =" inner join canais_agregados on VIEW_PESQUISA_PRODUTO_CLIENTE.canal_compra = canais_agregados.canal_base where id_estrangeiro = %s and data_cancelamento_produto is null AND data_suspensao_produto is null"
            fields = [
            'cliente_id','msisdn','chave_id','canal_compra','canais_agregados.canal_relatorio','produto_id','nome_produto','valor_produto',
            "DATE_FORMAT(data_compra_produto,'%%Y-%%m-%%d %%h:%%i:%%s') AS data_compra_produto",
            "DATE_FORMAT(data_cancelamento_produto,'%%Y-%%m-%%d %%h:%%i:%%s') AS data_cancelamento_produto",
            "DATE_FORMAT(data_suspensao_produto,'%%Y-%%m-%%d %%h:%%i:%%s') AS data_suspensao_produto",'periodo_tarifacao',
            'canal_cancelamento','motivo_cancelamento','motivo_suspensao','nome_parceiro']
            fields2 = [
            'cliente_id','msisdn','chave_id','canal_compra','canal_relatorio','produto_id','nome_produto','valor_produto',
            "data_compra_produto","data_cancelamento_produto","data_suspensao_produto",'periodo_tarifacao',
            'canal_cancelamento','motivo_cancelamento','motivo_suspensao','nome_parceiro']
            settings = self.application.settings
            sql = sql % (','.join(fields), tabela) + where
            slog.debug("Busca produtos ativos")
            cur = yield db.fexecute(sql, (msisdn), tabela, fields, 5,True)
            temp_list = []
            if cur and cur.value not in EMPTY:
                slog.debug("montar os produtos ativos")
                if type(cur.value[0]) is not tuple and type(cur.value[0]) is not list:
                    slog.debug(type(cur.value[0]))
                    temp_dict = dict(zip(fields2,cur.value))
                    temp_list.append(temp_dict)
                else:
                    slog.debug(cur.value)
                    for value in cur.value:
                        slog.debug(value)
                        temp_dict = dict(zip(fields2,value))
                        temp_list.append(temp_dict)
            slog.debug("Query produtos cancelados")
            sql2 = "select %s from %s"
            tabela2 = "VIEW_PESQUISA_PRODUTO_CLIENTE"
            where2 = " inner join canais_agregados on VIEW_PESQUISA_PRODUTO_CLIENTE.canal_compra = canais_agregados.canal_base where id_estrangeiro = %s and (data_cancelamento_produto >= %s AND data_cancelamento_produto <= %s)"
            sql2 = sql2 % (','.join(fields), tabela2) + where2
            sql = sql2
            slog.debug("Busca produtos cancelados")
            cur2 = yield db.fexecute(sql2, (msisdn,start_date,end_date), tabela, fields, 5,True)
            if cur2 and cur2.value not in EMPTY:
                if type(cur2.value[0]) is not tuple and type(cur2.value[0]) is not list:
                    slog.debug(type(cur2.value[0]))
                    temp_dict = dict(zip(fields2,cur2.value))
                    temp_list.append(temp_dict)
                else:
                    for value in cur2.value:
                        temp_dict = dict(zip(fields2,value))
                        temp_list.append(temp_dict)
            self.success(temp_list,False)
        except (DoesNotExist, ValueError):
            self.fail('Not found', code=404)
        except MissingArgumentError as e:
            self.fail(e.log_message, code=e.status_code)
        except Exception as e:
            print(e)
            slog.error(e)
            slog.error(sql)
            self.error('General Oauth Error', code=500)


class ClienteProductHistory(RestDBAPIHandler):
    __urls__ = [r"/client/product/history/(?P<base>[a-zA-Z0-9_]+)/?$"]

    @coroutine
    def get(self, base='vivo'):
        try:
            #select * from VIEW_PESQUISA_PRODUTO_CLIENTE where msisdn = '11963907436' and produto_id = 26;
            db = self.db.get(base)
            slog.info("database=%s"%(base))
            settings = self.application.settings
            msisdn = self.get_argument('msisdn', strip=True)
            if msisdn in EMPTY:
                raise MissingArgumentError
            product_id = self.get_argument('product_id', strip=True)
            if product_id in EMPTY:
                raise MissingArgumentError
            start_date = self.get_argument('start', strip=True)
            if start_date in EMPTY:
                raise MissingArgumentError
            end_date = self.get_argument('end', strip=True)
            if end_date in EMPTY:
                raise MissingArgumentError
            fields = ['la']
            sql = "select distinct produtos_parceiros.%s from %s"
            tabela = "VIEW_PESQUISA_PRODUTO_CLIENTE"
            where =" inner join produtos_parceiros on VIEW_PESQUISA_PRODUTO_CLIENTE.produto_id  = produtos_parceiros.produto WHERE VIEW_PESQUISA_PRODUTO_CLIENTE.id_estrangeiro = %s AND produtos_parceiros.produto = %s LIMIT 1"
            fields2 = [
            'canal_compra','produto_id','nome_produto','valor_produto',
            "data_compra_produto",'nome_parceiro']
            sql = sql % (','.join(fields), tabela) + where
            cur = yield db.fexecute(sql, (msisdn,product_id), tabela, fields, 5,True)
            temp_list = []
            if cur and cur.value not in EMPTY:
                slog.debug(cur.value)
                slog.debug(cur.value[0])
                la = cur.value[0]
                tabela2 = "select * from (select comando,'' as url, DATE_FORMAT(criado,'%%Y-%%m-%%d %%h:%%i:%%s') AS criado, 'MO' as tipo from mo.comandos_recebidos where fone = '%s' and la = '%s' and criado >='%s' and criado <= '%s'"%(msisdn,la,start_date,end_date)
                union1 = " union select mensagem,url,DATE_FORMAT(enviado,'%%Y-%%m-%%d %%h:%%i:%%s') as criado, 'MT' as tipo from requests_movile where fone = '%s' and enviado>='%s' and enviado <='%s'"%(msisdn,start_date,end_date)
                union2 = " ) as x order by x.criado asc"
                sql2 = tabela2 + union1 + union2
                slog.debug(sql2)
                cur2 = yield db.execute(sql2)
                data = json_formats(cur2.fetchall())
                fields=['la','url','comando','criado','tipo']
                for d in data:
                    comando = d[0]
                    url = d[1]
                    criado = d[2]
                    tipo = d[3]
                    res = (la,url,comando,criado,tipo)
                    temp_list.append(dict(zip(fields,res)))
            self.success(temp_list,False)
        except (DoesNotExist, ValueError):
            self.fail('Not found', code=404)
        except MissingArgumentError as e:
            self.fail(e.log_message, code=e.status_code)
        except Exception as e:
            print(e)
            slog.error(e)
            slog.error(sql)
            self.error('General Oauth Error', code=500)

class BlacklistSDP(RestDBAPIHandler):

    __urls__ = [r"/client/blacklist/(?P<base>[a-zA-Z0-9_]+)/?$"]

    @coroutine
    def get(self,base='sdp'):
        try:
            db = self.db.get(base)
            slog.info("database=%s"%(base))
            settings = self.application.settings
            msisdn = self.get_argument('msisdn', strip=True)
            slog.info('teste BlacklistSDP')
            if msisdn in EMPTY:
                raise MissingArgumentError
            fields =['msisdn','idBlacklistHistory','la','modifiedDate','data_bloqueio','canal_bloqueio','data_desbloqueio','canal_desbloqueio']
            sql = "select msisdn,idBlacklistHistory, la,DATE_FORMAT(CONVERT_TZ(modifiedDate,'+00:00','-3:00'), '%Y%m%d%H%i%s') AS modifiedDate,"
            sql += "IF(action = 'locked', DATE_FORMAT(CONVERT_TZ(modifiedDate,'+00:00','-3:00'), '%d/%m/%Y %H:%i'), '-') AS data_bloqueio,"
            sql += "IF(action = 'locked', channel, '') AS canal_bloqueio,"
            sql += "IF(action = 'unlocked', DATE_FORMAT(CONVERT_TZ(modifiedDate,'+00:00','-3:00'), '%d/%m/%Y %H:%i'),'-') AS data_desbloqueio,"
            sql += "IF(action = 'unlocked', channel, '') AS canal_desbloqueio"
            sql += " FROM sdp.blacklist_history_action "
            where = " WHERE msisdn = '%s' ORDER BY modifiedDate DESC"%(msisdn)
            query = sql + where
            slog.info(query)
            cur = yield db.execute(query)
            list_blacklist = []
            data = json_formats(cur.fetchall())
            for d in data:
                if d not in ['', False, 0, None]:
                    #slog.debug(d)
                    list_blacklist.append(dict(zip(fields,d)))
            slog.debug('Retorno dos dados')
            self.success(list_blacklist,False)
        except (DoesNotExist, ValueError):
            self.fail('Not found', code=404)
        except MissingArgumentError as e:
            self.fail(e.log_message, code=e.status_code)
        except Exception as e:
            print(e)
            slog.error(e)
            slog.error(query)
            self.error('General Oauth Error', code=500)
