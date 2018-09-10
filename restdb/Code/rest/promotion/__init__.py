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

class PromotionHandler(RestDBAPIHandler):
    """
    Busca produtos de um cliente na sorte7 ativos e inativos
    """
    __urls__ = [r"/promotion/(?P<base>[a-zA-Z0-9_]+)?$"]

    @coroutine
    def get(self, base):
        """
        :param base:
        :return: promotions from a given partner
        """
        try:
            db = self.db.get(base)
            slog.info("database=%s"%(base))
            ref = self.get_argument('telefone', strip=True)
            start_date = self.get_argument('start', strip=True)
            if start_date in EMPTY:
                raise MissingArgumentError
            end_date = self.get_argument('end', strip=True)
            if end_date in EMPTY:
                raise MissingArgumentError
            tabela = 'subscribers'
            fields = ['label_sms','id_canal',
            "name",'bnum_source',
            'din','anum','bill_cnt_ok', 'tipo_camp',
            'bill_last','bill_next',"status",
            'protocol_id',"source_out","din_out"]
            sql = "select c.label_sms,s_o.id_canal, ca.name,s_o.bnum_source, s_o.din,s_o.anum,s_o.bill_cnt_ok, cp.tipo_camp,DATE_FORMAT(s_o.bill_last,'%Y-%m-%d %h:%i:%s') as bill_last, DATE_FORMAT(s_o.bill_next,'%Y-%m-%d %h:%i:%s') as bill_next, '1' as  status,s_o.protocol_id, '' as source_out, '' as din_out"
            sql1 = " from subscribers s_o inner join carrier ca on s_o.carrier = ca.id_carrier inner join cc_canal c on  s_o.id_canal = c.id inner join cm_campanha cp on s_o.id_camp = cp.id"
            where = " where anum = %s "%(ref)
            union1 = " UNION select c.label_sms,s_o.id_canal, ca.name,s_o.bnum_source,DATE_FORMAT(s_o.din,'%Y-%m-%d %h:%i:%s') as din,s_o.anum,s_o.bill_cnt_ok, cp.tipo_camp,DATE_FORMAT(s_o.bill_last,'%Y-%m-%d %h:%i:%s') as bill_last, DATE_FORMAT(s_o.bill_next,'%Y-%m-%d %h:%i:%s') as bill_next, '0' as  status, s_o.protocol_id, source_out as source_out,DATE_FORMAT(s_o.din_out,'%Y-%m-%d %h:%i:%s') as din_out "
            sql3 = " from subscribers_out s_o inner join carrier ca on s_o.carrier = ca.id_carrier inner join cc_canal c on  s_o.id_canal = c.id inner join cm_campanha cp on s_o.id_camp = cp.id"
            where2 = " where anum = %s and (s_o.din_out >= '%s' and s_o.din_out <= '%s')"%(ref,start_date,end_date)
            tmp1 = sql+sql1+where+union1+sql3+where2
            sql = "select * from (%s)as A"%(tmp1)
            slog.info(sql)
            cur = yield db.execute(sql)
            list_brasiltec = []
            data = json_formats(cur.fetchall())
            for d in data:
                if d not in ['', False, 0, None]:
                    slog.debug(d)
                    list_brasiltec.append(dict(zip(fields,d)))
            slog.info('Busca pelas compras avulsas')
            sql2 = "select 'Teste de Personalidade' as label_sms,'0' as id_canal,carrier.name as name, bnum as bnum_source"
            sql2 = sql2+",DATE_FORMAT(din,'%Y-%m-%d %h:%i:%s') as din,anum, '0' as bill_cnt_ok,"
            sql2 = sql2+"'SMS' as tipo_camp,DATE_FORMAT(din,'%Y-%m-%d %h:%i:%s')   as bill_last , DATE_FORMAT('2000-01-01 00:00:00','%Y-%m-%d %h:%i:%s') as bill_next,'3' as status, '' as protocol_id"
            sql2 = sql2+",'MO' as source_out,DATE_FORMAT('2000-01-01 00:00:00','%Y-%m-%d %h:%i:%s') as din_out from msgs_single inner join carrier on msgs_single.carrier = carrier.id_carrier"
            where3 = " where anum = '%s'  and (din >= '%s' and din <= '%s') and text_code = '_PAGA_N_ASSIN_BILLOU'  and source !=  '0'  "%(ref,start_date,end_date)
            sql2 = sql2+where3
            slog.info(sql2)
            cur = yield db.execute(sql2)
            data = json_formats(cur.fetchall())
            for d in data:
                if d not in ['', False, 0, None]:
                    slog.debug(d)
                    list_brasiltec.append(dict(zip(fields,d)))
            slog.debug('Retorno dos dados')
            self.success(list_brasiltec,False)
        except (DoesNotExist, ValueError):
            self.fail('Not found', code=404)
        except MissingArgumentError as e:
            slog.error(e)
            self.fail(e.log_message, code=e.status_code)
        except Exception as e:
            print(e)
            slog.error(e)
            slog.error(sql)
            self.error('General Oauth Error', code=500)

class PromotionHistoryHandler(RestDBAPIHandler):
    """
    Busca o historico de MT e MO de um cliente na sorte7
    """

    __urls__ = [r"/promotion/history/(?P<base>[a-zA-Z0-9_]+)/?$"]

    @coroutine
    def get(self,base = 'vivo'):
        try:
            db = self.db.get(base)
            slog.info("database=%s"%(base))
            telefone = self.get_argument('telefone', strip=True)
            if telefone in EMPTY:
                raise MissingArgumentError
            la = self.get_argument('la', strip=True)
            if la in EMPTY:
                raise MissingArgumentError
            start_date = self.get_argument('start', strip=True)
            if start_date in EMPTY:
                raise MissingArgumentError
            end_date = self.get_argument('end', strip=True)
            if end_date in EMPTY:
                raise MissingArgumentError
            fields = ['din','type','text','bnum']
            select_fields = ["DATE_FORMAT(din,'%Y-%m-%d %h:%i:%s') as din",'type','text','bnum']
            tabela = 'msgs_single'
            sql = "select %s from %s"
            where = " where anum = %s and bnum= %s  and source !=  '0' and msgs_single.text not like '[FAKE]%%' and (din >= '%s' and din <= '%s') "%(telefone,la,start_date,end_date)
            sql = sql % (','.join(select_fields), tabela) + where
            slog.info(sql)
            #cur = yield db.fexecute(sql, (telefone,la,start_date,end_date), tabela, fields, 300)
            cur = yield db.execute(sql)
            list_brasiltec = []
            data = json_formats(cur.fetchall())
            for d in data:
                if d not in ['', False, 0, None]:
                    slog.debug(d)
                    list_brasiltec.append(dict(zip(fields,d)))
            self.success(list_brasiltec,False)
        except (DoesNotExist, ValueError):
            self.fail('Not found', code=404)
        except MissingArgumentError as e:
            slog.error(e)
            self.fail(e.log_message, code=e.status_code)
        except Exception as e:
            print(e)
            slog.error(e)
            slog.error(sql)
            self.error('General Oauth Error', code=500)
