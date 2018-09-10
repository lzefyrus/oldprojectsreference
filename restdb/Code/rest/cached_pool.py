from __future__ import absolute_import, division, print_function

from collections import deque
import pickle
import json
import hashlib
import logging

from tornado.ioloop import IOLoop
from tornado.gen import coroutine, Return
import tornado
from tornado_mysql.pools import Pool

from rest import utils

slog = logging.getLogger('restdb')


class CacheMissException(Exception):
    pass


class ExpiredKeyException(Exception):
    pass


class RedisPool(Pool):
    """Connection pool like Golang's database/sql.DB.

    This connection pool is based on autocommit mode.
    You can execute query without knowing connection.

    When transaction is necessary, you can checkout transaction object.
    """

    def __init__(self,
                 connect_kwargs,
                 max_idle_connections=1,
                 max_recycle_sec=3600,
                 max_open_connections=0,
                 io_loop=None,
                 redisobj=None,
                 ):
        """
        :param dict connect_kwargs: kwargs for tornado_mysql.connect()
        :param int max_idle_connections: Max number of keeping connections.
        :param int max_recycle_sec: How long connections are recycled.
        :param int max_open_connections:
            Max number of opened connections. 0 means no limit.
        """
        connect_kwargs['autocommit'] = True
        self.io_loop = io_loop or IOLoop.current()
        self.connect_kwargs = connect_kwargs
        self.max_idle = max_idle_connections
        self.max_open = max_open_connections
        self.max_recycle_sec = max_recycle_sec
        self.redisobj = redisobj
        self.rconn = None
        self.connection = redisobj
        self.prefix = 'sopa123'
        self.limit = 100

        self._opened_conns = 0
        self._free_conn = deque()
        self._waitings = deque()

        # return self.connection

    def make_key(self, key):
        return "ZRCache-{0}:{1}".format(self.prefix, key)

    def namespace_key(self, namespace):
        return self.make_key(namespace + ':*')

    def get_set_name(self):
        return "ZRCache-{0}-keys".format(self.prefix)

    @coroutine
    def store(self, key, value, expire=None):
        """
        Method stores a value after checking for space constraints and
        freeing up space if required.
        :param key: key by which to reference datum being stored in Redis
        :param value: actual value being stored under this key
        :param expire: time-to-live (ttl) for this datum
        """
        key = to_unicode(key)
        # value = to_unicode(value)
        set_name = self.get_set_name()

        while self.connection.scard(set_name) >= self.limit:
            del_key = self.connection.spop(set_name)
            self.connection.delete(self.make_key(del_key))

        pipe = self.connection.pipeline()
        if expire is None:
            expire = self.expire

        if expire <= 0:
            pipe.set(self.make_key(key), value)
        else:
            pipe.setex(self.make_key(key), expire, value)

        pipe.sadd(set_name, key)
        pipe.execute()

    def expire_all_in_set(self):
        """
        Method expires all keys in the namespace of this object.
        At times there is  a need to invalidate cache in bulk, because a
        single change may result in all data returned by a decorated function
        to be altered.
        Method returns a tuple where first value is total number of keys in
        the set of this object's namespace and second value is a number of
        keys successfully expired.
        :return: int, int
        """
        all_members = self.keys()

        with self.connection.pipeline() as pipe:
            pipe.delete(*all_members)
            pipe.execute()

        return len(self), len(all_members)

    def expire_namespace(self, namespace):
        """
        Method expires all keys in the namespace of this object.
        At times there is  a need to invalidate cache in bulk, because a
        single change may result in all data returned by a decorated function
        to be altered.
        Method returns a tuple where first value is total number of keys in
        the set of this object's namespace and second value is a number of
        keys successfully expired.
        :return: int, int
        """
        namespace = self.namespace_key(namespace)
        all_members = list(self.connection.keys(namespace))
        with self.connection.pipeline() as pipe:
            pipe.delete(*all_members)
            pipe.execute()

        return len(self), len(all_members)

    def isexpired(self, key):
        """
        Method determines whether a given key is already expired. If not expired,
        we expect to get back current ttl for the given key.
        :param key: key being looked-up in Redis
        :return: bool (True) if expired, or int representing current time-to-live (ttl) value
        """
        ttl = self.connection.pttl("ZRCache-{0}".format(key))
        if ttl == -1:
            return True
        if not ttl is None:
            return ttl
        else:
            return self.connection.pttl("{0}:{1}".format(self.prefix, key))

    @coroutine
    def store_pickle(self, key, value, expires=1):
        try:
            data = None
            if value.rowcount == 1:
                data = value.fetchone()
            elif value.rowcount > 1:
                data = value.fetchall()
        except Exception as e:
            raise CacheMissException(e)
        self.store(key, pickle.dumps(data), expire=expires)

    @coroutine
    def store_json(self, key, value, expires=1):
        try:
            data = None
            if value.rowcount == 1:
                data = value.fetchone()
            elif value.rowcount > 1:
                data = value.fetchall()
        except Exception as e:
            raise CacheMissException(e)
        # slog.debug(utils.json_formats(data))
        self.store(key, json.dumps(utils.json_formats(data)), expire=expires)

    def get(self, key):
        key = to_unicode(key)
        if key:  # No need to validate membership, which is an O(1) operation, but seems we can do without.
            value = self.connection.get(self.make_key(key))
            if value is None:  # expired key
                if not key in self:  # If key does not exist at all, it is a straight miss.
                    raise CacheMissException

                self.connection.srem(self.get_set_name(), key)
                raise ExpiredKeyException
            else:
                return value

    def mget(self, keys):
        """
        Method returns a dict of key/values for found keys.
        :param keys: array of keys to look up in Redis
        :return: dict of found key/values
        """
        if keys:
            cache_keys = [self.make_key(to_unicode(key)) for key in keys]
            values = self.connection.mget(cache_keys)

            if None in values:
                pipe = self.connection.pipeline()
                for cache_key, value in zip(cache_keys, values):
                    if value is None:  # non-existant or expired key
                        pipe.srem(self.get_set_name(), cache_key)
                pipe.execute()

            return {k: v for (k, v) in zip(keys, values) if v is not None}

    def get_json(self, key):
        return json.loads(self.get(key).decode())

    def get_pickle(self, key):
        return pickle.loads(self.get(key))

    def mget_json(self, keys):
        """
        Method returns a dict of key/values for found keys with each value
        parsed from JSON format.
        :param keys: array of keys to look up in Redis
        :return: dict of found key/values with values parsed from JSON format
        """
        d = self.mget(keys)
        if d:
            for key in d.keys():
                d[key] = json.loads(d[key]) if d[key] else None
            return d

    def invalidate(self, key):
        """
        Method removes (invalidates) an item from the cache.
        :param key: key to remove from Redis
        """
        key = to_unicode(key)
        pipe = self.connection.pipeline()
        pipe.srem(self.get_set_name(), key)
        pipe.delete(self.make_key(key))
        pipe.execute()

    def __contains__(self, key):
        return self.connection.sismember(self.get_set_name(), key)

    def __iter__(self):
        if not self.connection:
            return iter([])
        return iter(
            ["{0}:{1}".format(self.prefix, x)
             for x in self.connection.smembers(self.get_set_name())
             ])

    def __len__(self):
        return self.connection.scard(self.get_set_name())

    def keys(self):
        return self.connection.smembers(self.get_set_name())

    def flush(self):
        keys = list(self.keys())
        keys.append(self.get_set_name())
        with self.connection.pipeline() as pipe:
            pipe.delete(*keys)
            pipe.execute()

    def flush_namespace(self, namespace):
        namespace = self.namespace_key(namespace)
        setname = self.get_set_name()
        keys = list(self.connection.keys(namespace))
        with self.connection.pipeline() as pipe:
            pipe.delete(*keys)
            pipe.srem(setname, *keys)
            pipe.execute()

    def get_hash(self, args):
        if self.hashkeys:
            key = hashlib.md5(args).hexdigest()
        else:
            key = pickle.dumps(args)
        return key

    def db_parameter_key(self, params, table, cnames):
        return '{0}:{1}:{2}:{3}'.format(self.connect_kwargs.get('db'), table, ''.join(cnames),
                                        '|'.join([i for i in params if i not in [None, ' '] and ',' not in i]))

    def flush_key(self, key):
        pipe = self.connection.pipeline()
        pipe.delete(self.make_key(key))
        pipe.execute()

    @coroutine
    def fexecute(self, query, params=None, table='all', cnames=[], expires=5, clear_cache=False):
        """Execute query in pool.

        Returns future yielding closed cursor.
        You can get rows, lastrowid, etc from the cursor.

        :return: Future of cursor
        :rtype: Future
        """
        key = self.db_parameter_key(params, table, cnames)

        try:
            data = self.get_json(key)
            slog.debug('*** CACHE *** %s', key)
            return Return(data)
        except tornado.gen.BadYieldError:
            slog.debug('*** CACHE *** %s', key)
            raise Return(self.get_json(key))
        except (ExpiredKeyException, CacheMissException) as e:
            slog.debug('*** ExpiredKeyException, CacheMissException *** %s', e)
            pass
        except Exception:
            slog.exception("Unknown zr-cache error. Please check your Redis free space.")

        conn = yield self._get_conn()
        try:
            cur = conn.cursor()
            slog.debug('NO CACHE %s', key)
            yield cur.execute(query, params)
            yield self.store_json(key, cur, expires)
            yield cur.close()
        except Exception as e:
            slog.debug(e)
            self._close_conn(conn)
            raise
        else:
            self._put_conn(conn)
        result = self.get_json(key)
        # slog.debug('resultado==%s==: %s' % (key, result))
        if clear_cache:
            slog.debug('*** CLEAR CACHE *** %s', key)
            self.invalidate(key)
            self.flush_key(key)
        return Return(result)


class DoNotCache(Exception):
    _result = None

    def __init__(self, result):
        super(DoNotCache, self).__init__()
        self._result = result

    @property
    def result(self):
        return self._result


def to_unicode(data):
    return data
