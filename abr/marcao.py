#!-*- conding: utf8 -*-
#from crate import client
from queue import Queue
from threading import Thread
import threading
import time
import requests
import pprint
from urllib3 import HTTPConnectionPool
import json
import datetime
from datetime import datetime



class Check(object):

    """
        docstring for LNGen
    """

    def __init__(self):
        self.q = Queue()
        self.start = time.time()
        self.operator = {'error': 0}
        self.pool = requests.Session()

    def add(self):
        while True:
            i = self.q.get()
            self.record += 1
            a = json.loads(i.replace(' 0', ' '))
            i = str(a.get('id'))
            try:
                r = self.pool.get('http://127.0.0.1:8889/search/' + i)

                j = r.json()
                print(j)
                op = j.get('operadora')

                if op not in self.operator.keys():
                    self.operator[op] = 0

                self.operator[op] = self.operator[op] + 1

            #
            except Exception as e:
                self.operator['error'] = self.operator['error'] + 1
                print(e)
                print(i)

    def gen(self, file, threads=10):
        self.operator = {'error': 0}
        st = time.time()
        self.record = 1
        if 'VIVO' in file:
            self.op = 'vivo'
        else:
            self.op = 'tim'
        ff = open('./{}'.format(file), 'r')
        for i in range(int(threads)):
            t = Thread(target=self.add)
            t.daemon = True
            t.start()

        total = 0

        for i in ff.readlines():
            total += 1
            self.q.put(i.rstrip('\n'))
            if total >= 100:
                break
        self.q.join()
        #self.cursor.close()
        #self.cc.close()
        print(time.time() - st)
        print(file)
        self.response(file)
        pprint.pprint(self.operator, indent=4)
        return True

    def response(self, file):
        ff = open('{}-{}.txt'.format(file, time.strftime('%Y%m%d')), 'w')
        ff.writelines(pprint.pformat(self.operator, indent=4))



# Verifica se retonou registros
if __name__ == '__main__':
    l = Check()
    c = l.gen('VIVO_SANDRO', 25)



