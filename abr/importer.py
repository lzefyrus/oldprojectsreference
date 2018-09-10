# -*- coding: utf-8 -*-
from bs4 import BeautifulSoup
import models
import requests
import sys
from utils import translateImage, translateArbOperator, checkMobile, insertOperators, translateOperator
import struct
import datetime
from io import BytesIO
import pprint
import time
import unidecode


import logging
import configobj


class AbrSite():

    """
    Main import for DDDs and Teleco default mobile operator numbers for each DDD available
    """

    DDD = "0 11 12 13 14 15 16 17 18 19 21 22 24 27 28 31 32 33 34 35 37 38 41 42 43 44 45 46 47 48 49 51 53 54 55 61 62 63 64 65 66 67 68 69 71" + \
          "73 74 75 77 79 81 82 83 84 85 86 87 88 89 91 92 93 94 95 96 97 98 99"
    DDD = DDD.split(' ')
    URL_STATES = "http://www.anatel.gov.br/hotsites/CodigosNacionaisLocalidade/TelefoneCelular-CodigosDeArea.htm"
    URL_OPERATORS = "http://www.teleco.com.br/carrega_numeros_operadora.asp"

    def getAreaCodes(self, run_all=True):
        """
        Main method for importing
        """
        if run_all:
            logging.info('Updating the States, operatos and DDD values to DB')
            states_text = requests.get(self.URL_STATES)
            if states_text.status_code != 200:

                exit()

            betext = BeautifulSoup(states_text.text)

            states = betext.findAll('div', class_='escritorios3')

            for s in states:
                id = s.attrs['id']
                if len(id) == 2:
                    ddds = s.findChildren('strong')
                    for d in ddds:
                        if '-' in d.text:
                            many = d.text.split('-')
                            for m in many:
                                ddd = models.Ddd.query.filter_by(
                                    id=int(m)).first()
                                if not ddd:
                                    ddd = models.Ddd(id=int(m), state=id)
                                    models.db.session.add(ddd)
                        else:
                            ddd = models.Ddd.query.filter_by(
                                id=int(d.text)).first()
                            if not ddd:
                                ddd = models.Ddd(id=int(d.text), state=id)
                                models.db.session.add(ddd)
            time.sleep(2)

        area_codes = models.Ddd.query.all()

        operators = models.Operator.query.all()

        for area in area_codes:
            content_text = requests.get(
                self.URL_OPERATORS, params=dict(dd=area.id))
            if content_text.status_code is not 200:
                print('error retrieving url for ddd %s' % area.id)

            content_operators = BeautifulSoup(content_text.text)
            heads = content_operators.select('thead tr th img')
            contents = content_operators.select('tbody tr')

            findex = -1

            for h in heads:
                findex = findex + 1
                logging.debug('index: %s' % findex)
                logging.debug(h.attrs['src'])
                operator = translateImage(h.attrs['src'])
                if operator:
                    for tb in contents:
                        td = tb.select('td')[findex].text.split('-')
                        logging.debug(td)
                        if len(td) >= 1 and td[0] != '':
                            start = end = td[0]
                            if len(td) == 2:
                                end = td[1]
                            cnl = models.Cnl(id=None,
                                             uf=area.state,
                                             cnl='',
                                             cnl_cod='',
                                             place='',
                                             province='',
                                             tarifation_cod='',
                                             prefix=area.id,
                                             operator=operator.name,
                                             operator_id=operator.id,
                                             initial_phone=int(start),
                                             final_phone=int(end),
                                             cnl_local_area_cod='',
                                             is_mobile=True,
                                             ddd=area.id,
                                             created_at=None)
                            models.db.session.add(cnl)
                            logging.debug(dict(id=None,
                                               uf=area.state,
                                               cnl='',
                                               cnl_cod='',
                                               place='',
                                               province='',
                                               tarifation_cod='',
                                               prefix=area.id,
                                               operator=operator.name,
                                               operator_id=operator.id,
                                               initial_phone=int(start),
                                               final_phone=int(end),
                                               cnl_local_area_cod='',
                                               is_mobile=True,
                                               ddd=area.id,
                                               created_at=None))
                    models.db.session.commit()


class Record(object):

    """
    simple mock object 
    """
    pass


class FileParseAbr():

    """
    Parsers the file and adds to the current phone data deltas or full file
    """

    def __init__(self, file):
        """
        sets the data and open the file for parsing

        :param str file: file path to be processed
        :return: None
        """

        logging.info('Starting fileparse')

        try:
            number_of_lines = self.bufcount(file)
            logging.info('%s has %s lines' % (file, number_of_lines))
            self.file_for_read = open(file, encoding='UTF-8')
            self.lazy = dict()
            self.readLines()
        except Exception as e:
            logging.error('File Error: %s' % e)
            exit()

    # functions for converting input fields to usable data

    def bufcount(self, filename):
        """
        open the file 1M at a time
        """
        f = open(filename)
        lines = 0
        buf_size = 1024 * 1024
        read_f = f.read
        buf = read_f(buf_size)
        while buf:
            lines += buf.count('\n')
            buf = read_f(buf_size)

        return lines

    def readLines(self):
        """
        line reader and spliter for csv file
        """
        line = self.file_for_read.readline()
        logging.debug(line)
        sline = line.split(';')
        number = 1
        if len(sline) == 2:
            self.date_mark = sline
            number = number + 1
            try:
                print(line)
                self.header = models.Header(generated=self.parseDate(sline[0]),
                                            number_of_items=int(sline[1]))
                models.db.session.add(self.header)
                line = self.file_for_read.readline()
                logging.debug(line)
            except ValueError:
                logging.error('Fatal error, no header found')
                return
        # self.processFile(line, number)

    # def processFile(self, line, number):
        while line:
            try:
                sline = line.split(';')

                logging.debug(sline)

                if sline[1] == '0':

                    update = True

                    phone = models.Phone.query.filter_by(id=int(sline[2])).first()
                    logging.debug(phone)
                    if not phone:
                        logging.debug('phone not found: {}'.format(int(sline[2])))
                        phone = models.Phone()
                        update = False
                        phone.created_at = datetime.datetime.now()
                        phone.id = int(sline[2])

                    self.lazy, oop = translateArbOperator(self.lazy, sline[5])
                    logging.debug('Operator id: {}'.format(oop))
                    phone.operator = oop
                    phone.portability_id = sline[0]
                    phone.portability_type = sline[4]
                    phone.action = sline[1]
                    phone.new_spid = sline[5]
                    phone.eot = sline[6]
                    # phone.is_mobile = checkMobile(sline[2])
                    phone.is_mobile = False
                    phone.activation_time = self.parseDate(sline[7])
                    phone.start_time = self.parseDate(sline[8])
                    phone.updated_at = datetime.datetime.now()

                    if not update:
                        models.db.session.add(phone)

                    models.db.session.commit()

            except Exception as e:
                logging.error('Record error line: %s\n %s ' % (number, e))
                models.db.session.rollback()
            finally:
                line = self.file_for_read.readline()
                number = number + 1

    def parseDate(self, dateStr):
        """
        parses the date from file

        :param str dateStr: umparsed date
        :return: datetime obj
        :rtype: datetime
        """
        try:
            return datetime.datetime.strptime(dateStr[:14], '%Y%m%d%H%M%S')
        except ValueError:
            return datetime.datetime.now()


class FileParseCnl():

    """
    Parse CNL information by operator
    """

    def __init__(self, file, is_delta=True, is_mobile=False):
        """
            :param str file: path of the file to be parsed
            :param bool is_delta: type of file
            :param bool is_mobile: sets the parser for CNL Mobile file model
        """
        logging.info('Starting fileparse cnl')

        try:
            self.file_for_read = open(file, encoding='cp1252')
            self.file_for_read.seek(0)
            self.is_delta = is_delta
            if not is_mobile:
                models.Cnl.query.delete()
            self.is_mobile = is_mobile

            # functions for converting input fields to usable data
            self.cnv_text = lambda s: s.rstrip()
            self.cnv_int = lambda s: int(s)
            self.cnv_date_dmy = lambda s: datetime.datetime.strptime(
                s, "%d%m%Y")  # ddmmyyyy

            # field specs (field name, start pos (1-relative), len, converter
            # func)
            if not is_mobile:
                self.fieldspecs = [
                    ('uf', 0, 2, self.cnv_text),
                    ('scnl', 2, 4, self.cnv_text),
                    ('ccnl', 6, 5, self.cnv_int),
                    ('place', 11, 50, self.cnv_text),
                    ('city', 61, 50, self.cnv_text),
                    ('codtax', 111, 2, self.cnv_int),
                    ('prefix', 118, 5, self.cnv_int),
                    ('operator', 123, 30, self.cnv_text),
                    ('start', 153, 4, self.cnv_int),
                    ('end', 157, 4, self.cnv_int),
                    # ('lat', 161, 8, self.cnv_int),
                    # ('hem', 169, 5, self.cnv_text),
                    # ('log', 173, 8, self.cnv_int),
                    # ('loccnl', 182, 4, self.cnv_text),
                ]
            else:
                self.fieldspecs = [
                    ('codtax', 0, 2, self.cnv_int),
                    ('prefix', 2, 5, self.cnv_int),
                    ('operator', 7, 30, self.cnv_text),
                    ('start', 37, 4, self.cnv_int),
                    ('end', 41, 4, self.cnv_int),
                ]
            self.operators = dict()

            self.run()
        except Exception as e:
            logging.error('File Not Found: %s' % e)

    def readLines(self):
        """
        :return:yelded line
        """
        line = self.file_for_read.readline()
        while line:
            yield line
            line = self.file_for_read.readline()

    def processFile(self, line):
        """
        makes the parse and adds the data on the database

        :param str line: yelded line
        :return: None
        """

        # self.fieldspecs.sort(key=lambda x: x[1])  # just in case

        # build the format for struct.unpack
        unpack_len = 0
        unpack_fmt = ""
        for fieldspec in self.fieldspecs:
            start = fieldspec[1] - 1
            end = start + fieldspec[2]
            if start > unpack_len:
                unpack_fmt += str(start - unpack_len) + "x"
            unpack_fmt += str(end - start) + "s"
            unpack_len = end
        field_indices = range(len(self.fieldspecs))
        unpacker = struct.Struct(unpack_fmt).unpack_from

        # The guts of this loop would of course be hidden away in a function/method
        # and could be made less ugly
        ll = unidecode.unidecode(line) + ' '
        raw_fields = unpacker(ll.encode('UTF-8'))
        r = Record()
        try:
            for x in field_indices:
                setattr(
                    r, self.fieldspecs[x][0], self.fieldspecs[x][3](raw_fields[x]))
            logging.debug(r.__dict__)
            self.operators, operator = translateOperator(
                self.operators, r.operator.decode())
            if self.is_mobile:
                cnl = models.Cnl(id=None,
                                 uf='',
                                 cnl='',
                                 cnl_cod='',
                                 place='',
                                 province='',
                                 tarifation_cod='',
                                 prefix=r.codtax,
                                 operator=operator.name,
                                 operator_id=operator.id,
                                 initial_phone=int(
                                     '%s%s' % (r.prefix, "{0:04d}".format(int(r.start)))),
                                 final_phone=int(
                                     '%s%s' % (r.prefix, "{0:04d}".format(int(r.end)))),
                                 cnl_local_area_cod='',
                                 is_mobile=True,
                                 ddd=int(r.codtax))
            else:
                cnl = models.Cnl(id=None,
                                 uf=r.uf.decode(),
                                 cnl=r.ccnl,
                                 cnl_cod=r.scnl.decode(),
                                 place=r.place.decode(),
                                 province=r.city.decode(),
                                 tarifation_cod=r.codtax,
                                 prefix=r.codtax,
                                 operator=operator.name,
                                 operator_id=operator.id,
                                 initial_phone=int(
                                     '%s%s' % (r.prefix, "{0:04d}".format(int(r.start)))),
                                 final_phone=int(
                                     '%s%s' % (r.prefix, "{0:04d}".format(int(r.end)))),
                                 cnl_local_area_cod=r.codtax,
                                 is_mobile=False,
                                 ddd=int(r.codtax))
            models.db.session.add(cnl)
        except Exception as e:
            logging.error(line)
            logging.error(e)

        # models.db.session.commit()

    def run(self):
        """
        simple run script
        """
        file = self.readLines()
        for f in file:
            self.processFile(f)
        models.db.session.commit()

if __name__ == '__main__':
    now = time.strftime('%Y%m%d')

    logging.basicConfig(level=logging.INFO,
                        format='[ %(levelname)s ] %(asctime)s - %(name)s - %(message)s',
                        datefmt='%m-%d %H:%M',
                        filename='log/abr%s.txt' % now)
    config = configobj.ConfigObj('config.ini')

    # FileParseCnl(config['cnl']['path'])
    FileParseCnl(config['cnl']['pathmobile'], True, True)
    # AbrSite().getAreaCodes(run_all=int(config['extra']['run_all']))
    # insertOperators()
    # FileParseAbr(config['abr']['delta_path'])
    # FileParseAbr(config['abr']['full_path'])
