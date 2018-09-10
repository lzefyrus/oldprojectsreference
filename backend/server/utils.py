import datetime
import decimal
import json
import logging
import math
import pickle
import sys
from uuid import uuid4

import tornado
from tornado.escape import json_encode
from tornado_cors import CorsMixin
from tornado_json.requesthandlers import APIHandler as APIHandler_Orig
from torndsession import session
from torndsession.session import SessionConfigurationError, SessionDriverFactory

import hashids
from game.models import User, Reward, Life

LIFE_LOCK_ = 'life_lock:{}'

log = logging.getLogger(__name__)


class DateTimeEncoder(json.JSONEncoder):
    def default(self, obj):
        if hasattr(obj, 'isoformat'):
            return obj.isoformat()
        elif isinstance(obj, decimal.Decimal):
            return float(obj)
        else:
            return json.JSONEncoder.default(self, obj)


class TokenSess(session.SessionManager):
    def __init__(self, handler):
        self._default_session_lifetime = datetime.datetime.utcnow() + datetime.timedelta(days=7)
        self.handler = handler
        self.settings = {}  # session configurations
        self._expires = self._default_session_lifetime
        self._is_dirty = True
        self.__init_session_driver()
        self.__init_session_object()  # initialize session object

    def __session_settings(self):
        session_settings = self.settings.get('cookie_config', {})
        session_settings.setdefault('expires', None)
        session_settings.setdefault('expires_days', None)
        return session_settings

    def __init_settings(self):
        session_settings = self.handler.settings.get("session")
        if not session_settings:  # use default
            session_settings = {}
            session_settings.update(driver='memory', driver_settings={'host': self.handler.application},
                                    force_persistence=True, cache_driver=True)
        driver = session_settings.get("driver")
        if not driver:
            raise SessionConfigurationError('driver is missed')
        self.settings = session_settings

    def __init_session_driver(self):
        """
        setup session driver.
        """
        self.__init_settings()

        driver = self.settings.get("driver")
        if not driver: raise SessionConfigurationError('driver not found')
        driver_settings = self.settings.get("driver_settings", {})
        if not driver_settings: raise SessionConfigurationError('driver settings not found.')

        cache_driver = self.settings.get("cache_driver", True)
        if cache_driver:
            cache_name = '__cached_session_driver'
            cache_handler = self.handler.application
            if not hasattr(cache_handler, cache_name):
                setattr(cache_handler, cache_name, SessionDriverFactory.create_driver(driver, **driver_settings))
            session_driver = getattr(cache_handler, cache_name)
        else:
            session_driver = SessionDriverFactory.create_driver(driver, driver_settings)
        self.driver = session_driver(**driver_settings)  # create session driver instance.

    def __init_session_object(self):
        session_id = self.getCookieOrToken()
        if not session_id:
            session_id = uuid4().hex
            self.handler.set_cookie(self.SESSION_ID,
                                    session_id,
                                    **self.__session_settings())
            self._is_dirty = True
            self.session = {}
        else:
            self.session = self.__get_session_object_from_driver(session_id)
            if not self.session:
                self.session = {}
                self._is_dirty = True
            else:
                self._is_dirty = False
        cookie_config = self.settings.get("cookie_config")
        if cookie_config:
            expires = cookie_config.get("expires")
            expires_days = cookie_config.get("expires_days")
            if expires_days is not None and not expires:
                expires = datetime.datetime.utcnow() + datetime.timedelta(days=expires_days)
            if expires and isinstance(expires, datetime.datetime):
                self._expires = expires
        self._expires = self._expires if self._expires else self._default_session_lifetime
        self._id = session_id

    def getCookieOrToken(self):
        session_id = self.handler.request.headers.get("Authorization")

        if not session_id:
            session_id = self.handler.get_cookie(self.SESSION_ID)

        return session_id

    def __get_session_object_from_driver(self, session_id):
        """
        Get session data from driver.
        """
        return self.driver.get(session_id)


class SessionMixin(object):
    @property
    def session(self):
        return self._create_mixin(self, '__session_manager', TokenSess)

    def _create_mixin(self, context, inner_property_name, session_handler):
        if not hasattr(context, inner_property_name):
            setattr(context, inner_property_name, session_handler(context))
        return getattr(context, inner_property_name)


class SessionBaseHandler(tornado.web.RequestHandler, SessionMixin):
    def prepare(self):
        """
        Overwrite tornado.web.RequestHandler prepare.
        """
        pass

    def on_finish(self):
        """
        Overwrite tornado.web.RequestHandler on_finish.
        """
        self.session.flush()  # try to save session


class APIHandler(CorsMixin, APIHandler_Orig, SessionMixin):
    CORS_ORIGIN = 'https://next.me'
    CORS_HEADERS = 'Authorization, Accept, Content-Length, Accept-Language, Content-Language, Content-Type, Accept-Encoding, Access-Control-Request-Headers, Access-Control-Request-Method, Connection, Host, Origin, User-Agent, Referer, Cookie'
    CORS_METHODS = 'GET, POST, DELETE, PUT, OPTIONS'
    CORS_CREDENTIALS = True
    CORS_MAX_AGE = 21600

    def prepare(self):
        self.db = self.application.settings.get('engine')
        user = self.get_user()

        if not user and self.request.method not in ['OPTIONS', 'options']:
            self.write_error(401, _reason='Auth token expired or invalid')

        self.current_user = user

    def gen_token(self, user):
        self.session['id'] = user.id
        self.session['facebook_id'] = user.facebook_id
        self.session['name'] = user.name

        return {'id': user.id,
                'facebook_id': user.facebook_id,
                'name': user.name}

    def get_user(self):
        if self.session.get('id'):
            try:
                uuser = self.db.get(User, facebook_id=self.session.get('facebook_id'), id=self.session.get('id'))
                if not uuser:
                    self.redirect('/', status='Not Registered')
                    return

                return uuser

            except Exception as e:
                return None

    def set_default_headers(self):
        self.set_header('Access-Control-Allow-Origin', self.CORS_ORIGIN)
        self.set_header('Access-Control-Allow-Headers', self.CORS_HEADERS)
        self.set_header('Access-Control-Allow-Methods', self.CORS_METHODS)
        self.set_header('Access-Control-Max-Age', self.CORS_MAX_AGE)
        self.set_header('Access-Control-Allow-Credentials', self.CORS_CREDENTIALS)
        self.set_header('Server', 'Next')

    def write_error(self, status_code, **kwargs):
        self.set_status(status_code)
        if kwargs not in ['', None, {}, [], 0]:
            self.write('')
        else:
            self.write(json_encode(
                dict(status=status_code, reason=kwargs.get('_reason', ''))))
        self.finish()

    def success(self, data):
        """When an API call is successful, the JSend object is used as a simple
        envelope for the results, using the data key.

        :type  data: A JSON-serializable object
        :param data: Acts as the wrapper for any data returned by the API
            call. If the call returns no data, data should be set to null.
        """
        try:
            self.write(data)
        except TypeError:
            self.write(str(data))
        self.finish()


class OpenApiHandler(APIHandler):
    def prepare(self):
        self.db = self.application.settings.get('engine')


class Scranble(object):
    def __init__(self, key, iconset):
        self.key = key
        self.iconset = iconset
        self.h = hashids.Hashids(key)

    def encrypt_data(self):
        ret = []
        for k in self.iconset.get('icons'):
            ret.append({'key': k.get('key'), 'code': self.h.encode(int(k.get('code')))})
        return ret

    def decrypt_data(self):
        ret = []
        try:
            for i in self.iconset.split('|'):
                log.warn(i)
                ret.append(str(self.h.decode(i)[0]))
        except Exception:
            log.warn("decrypt sequence [{}]is not valid for user".format(self.iconset))
        finally:
            return ret


def import_string(import_name, silent=False):
    # copy from https://github.com/mitsuhiko/werkzeug/blob/master/werkzeug/
    # utils.py
    """Imports an object based on a string.  This is useful if you want to
    use import paths as endpoints or something similar.  An import path can
    be specified either in dotted notation (``xml.sax.saxutils.escape``)
    or with a colon as object delimiter (``xml.sax.saxutils:escape``).
    If `silent` is True the return value will be `None` if the import fails.
    :param import_name: the dotted name for the object to import.
    :param silent: if set to `True` import errors are ignored and
                   `None` is returned instead.
    :return: imported object
    """
    # force the import name to automatically convert to strings
    # __import__ is not able to handle unicode strings in the fromlist
    # if the module is a package
    import_name = str(import_name).replace(':', '.')
    try:
        try:
            __import__(import_name)
        except ImportError:
            if '.' not in import_name:
                raise
        else:
            return sys.modules[import_name]

        module_name, obj_name = import_name.rsplit('.', 1)
        try:
            module = __import__(module_name, None, None, [obj_name])
        except ImportError:
            # support importing modules not yet set up by the parent module
            # (or package for that matter)
            module = import_string(module_name)

        try:
            return getattr(module, obj_name)
        except AttributeError as e:
            raise ImportError(e)

    except ImportError as e:
        if not silent:
            raise


def rounder(x, base=5):
    return int(base * round(float(x) / base))


def time_to_life(last_dec):
    if not last_dec:
        return 0
    plusone = 20 * 60  # segundos
    try:
        diff_secs = (datetime.datetime.now(datetime.timezone.utc) - last_dec).seconds
    except TypeError:
        diff_secs = (datetime.datetime.utcnow() - last_dec).seconds

    frac, plife = math.modf(diff_secs / plusone)
    if diff_secs >= plusone:
        if plife >= 3:
            return 0
        return plusone - int(frac * plusone)
    else:
        return plusone - diff_secs
    return 0


def has_life(cont, rr=True):
    udata = cont.db.get(Life, rr='life', user_id=cont.session.get('id'))
    if udata is not None and udata.last_dec:
        udata = give_life(cont, udata)
    if udata is not None and udata.life_qtd <= 0:
        if rr:
            cont.write_error(400, **{
                "message": "No more lives, wait for new ones.",
                "win": False,
                "prize": {},
                "status": "error",
                "nextLife": time_to_life(cont.session.get('last_dec', 0)),
                "lives": 0
            })
        return False
    return udata.life_qtd


def give_life(cont, udata):
    db = cont.application.db_conn.get('ping')

    try:
        if db.get(LIFE_LOCK_.format(cont.session.get('id'))):
            raise Exception('life giver in lock')
        db.set(LIFE_LOCK_.format(cont.session.get('id')), True)
        log.debug('LOCK: {}'.format(db.get(LIFE_LOCK_.format(cont.session.get('id')))))
        plusone = 20 * 60  # segundos
        log.debug('{}/n{}'.format(datetime.datetime.now(datetime.timezone.utc), udata.last_dec))
        diff_secs = (datetime.datetime.now(datetime.timezone.utc) - udata.last_dec).seconds
        log.debug('diff_secs: {}'.format(diff_secs))
        secs = 0
        if diff_secs >= plusone:
            if udata.life_qtd < 3:
                frac, plife = math.modf(diff_secs / plusone)
                extra = int(3 - udata.life_qtd)
                assert (extra >= 0)
                if int(plife) >= extra:
                    udata.life_qtd = udata.life_qtd + int(extra)
                    log.debug('plife {} >= {}'.format(plife, extra))
                elif int(plife) == 0 and frac > 0:
                    log.debug('plife elif {} {}'.format(int(plife), frac))
                    udata.life_qtd = udata.life_qtd + 1
                    secs = plusone
                else:
                    log.debug('plife else >= {}'.format(extra))
                    udata.life_qtd = udata.life_qtd + int(plife)
                    secs = int(plife * plusone)

                try:
                    udata.sync(constraints=[Life.life_qtd <= 3])
                except Exception as e:
                    log.warn(e.__repr__())

                log.debug(secs)

                if udata.life_qtd >= 3:

                    udata.last_dec = None
                    cont.session.delete('last_dec')
                    log.debug('REMOVE {}'.format(cont.session.get('last_dec', None)))
                else:
                    log.debug(udata.last_dec)
                    udata.last_dec = udata.last_dec + datetime.timedelta(seconds=secs)
                    log.debug(udata.last_dec)
                    cont.session['last_dec'] = udata.last_dec
            else:
                udata.last_dec = None
                cont.session.delete('last_dec')
            udata.sync()
    except Exception as e:
        log.warn('{}:'.format(e.__repr__(), cont.session.get('id')))
    finally:
        db.delete(LIFE_LOCK_.format(cont.session.get('id')))
        log.debug('UNLOCK: {}'.format(db.get(LIFE_LOCK_.format(cont.session.get('id')))))
        return udata


def use_life(cont):
    udata = cont.db.get(Life, rr='life', user_id=cont.session.get('id'))

    if udata.life_qtd == 3:
        udata.last_dec = datetime.datetime.utcnow()
        cont.session['last_dec'] = udata.last_dec

    if udata.life_qtd >= 0:
        udata.life_qtd = int(udata.life_qtd) - 1
    udata.sync()

    return udata.life_qtd


def won_week(cont, level, rr=True, retrewards=False):
    rewards = cont.db.query(Reward).filter(Reward.game_level == level,
                                           Reward.user_id == cont.session.get('id')).all()

    # thisweek = datetime.datetime.utcnow().isocalendar()[1]

    for i in rewards:
        # if i.updated_at.isocalendar()[1] == thisweek:
        if rr:
            cont.write_error(400, **{
                "message": "Already won this week.",
                "win": False,
                "status": "error",
                "prize": {},
                "nextLife": time_to_life(cont.session.get('last_dec', 0)),
                "lives": 0
            })
        if not retrewards:
            return False
    return rewards


def one_device(cont, user, new):
    name = 'back:{}'.format(user.id)
    sess = cont.application.db_conn.get('session')
    backref = sess.get(name)
    try:
        if backref and backref != new:
            sessdata = pickle.loads(sess.get(backref))
            if 'last_dec' in sessdata.keys():
                cont.session['last_dec'] = sessdata.get('last_dec')
            sess.delete(backref)
        sess.set(name, new)
    except Exception as e:
        print('{}:{} - {}'.format(backref, sess, e))


def smart_truncate(content, length=100, suffix='...'):
    if len(content) <= length:
        return content
    else:
        return ' '.join(content[:length + 1 - len(suffix)].split(' ')[0:-1]) + suffix

# def allowedRole(roles = None):
#     def decorator(func):
#         def decorated(self, *args, **kwargs):
#             self.db_conn.delete(self.session.get("id"))
#
#             # User is refused
#             if user is None:
#                 raise Exception('Cannot proceed role check: user not found')
#
#             role = user[_userRolePropertyName]
#
#             if _checkRole(role, roles) == False:
#                 self.set_status(403)
#                 self._transforms = []
#                 self.finish()
#                 return None
#
#             return func(self, *args, **kwargs)
#         return decorated
#     return decorator
#
