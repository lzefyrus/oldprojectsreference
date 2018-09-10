import logging
from datetime import datetime, timedelta
from urllib.parse import quote
from uuid import uuid4

import flywheel
from dynamo3 import CheckFailed
from tornado.auth import FacebookGraphMixin
from tornado.gen import coroutine

from game.models import User, Life
from referral.models import ReferralUser, ReferralRequest
from utils import SessionBaseHandler, one_device, smart_truncate

log = logging.getLogger(__name__)

HTML = """<html>
<head>
    <meta http-equiv="refresh" content="1; url={}/#/code/{}" />
    <meta property="og:url"                content="http://www.next.me" />
    <meta property="og:type"               content="website" />
    <meta property="og:title"              content="Você está pronto ?" />
    <meta property="og:description"        content="Super desafio NEXT!" />
    <meta property="og:image"              content="" />
    <title>Next.me</title>
</head>
<body style="background-color:black; color:#2dff72">
redirecionando ...
</body>
</html>
"""


class FacebookGraphLoginHandler(FacebookGraphMixin, SessionBaseHandler):
    @coroutine
    def get(self):

        if self.get_argument("error", None):
            log.error(self.get_argument("error"))
            self.write(self.get_argument("error"))
            return True

        redirectp = '{}/auth/login'.format(self.application.settings.get('instance', {}).get('api'))

        try:
            if self.get_argument("code", None):
                user = yield self.get_authenticated_user(
                    redirect_uri=redirectp,
                    client_id=self.settings["facebook_api_key"],
                    client_secret=self.settings["facebook_secret"],
                    code=self.get_argument("code"),
                    extra_fields=['email', 'gender', 'age_range'])
                user = yield self.save_user(user)
                self.current_user = self.gen_token(user)
                self.write(HTML.format(self.application.settings.get('instance', {}).get('front'),
                                       self.session.getCookieOrToken() or self.session.id))
            else:
                log.info('auth')
                yield self.authorize_redirect(
                    redirect_uri=redirectp,
                    client_id=self.settings["facebook_api_key"],
                    extra_params={"scope": "email"})
        except Exception as e:
            log.error(e)

        if not self._finished:
            log.debug("not finished")
            self.finish()

    @coroutine
    def save_user(self, user):
        db = self.application.settings.get('engine')
        local_user = None
        pictures = {}

        referred_id = uuid4().hex

        try:
            big_picture = yield self.facebook_request('/me/picture', type='square', width='200', height='200',
                                                      redirect=False, access_token=user.get('access_token'))
            pictures['small'] = user.get('picture', {}).get('data', {}).get('url')
            if 'data' not in big_picture.keys():
                big_picture = None
            else:
                pictures['big'] = big_picture.get('data', {}).get('url')
        except Exception as e:
            big_picture = None

        log.info(big_picture)

        try:
            local_user = db.query(User).filter(User.facebook_id == user.get('id')).one()
            log.info(local_user)
            if local_user and not local_user.avatar:
                local_user.avatar = pictures
                db.sync(local_user)
            life = local_user = db.query(Life).filter(Life.user_id == local_user.id).one()
            if life.last_dec:
                self.session['last_dec'] = life.last_dec

        except flywheel.query.EntityNotFoundException:
            try:
                email = user.get('email')
                if not email:
                    email = '{}@nomail.me'.format(user.get('id'))

                local_user = User()
                local_user.id = uuid4().hex
                local_user.facebook_id = int(user.get('id'))
                local_user.facebook_token = user.get('access_token')
                local_user.facebook_data = user
                local_user.email = email
                local_user.name = user.get('name')
                local_user.referral = referred_id
                local_user.avatar = pictures
                local_user.created_at = datetime.utcnow()
                db.sync(local_user)

                user_life = Life()
                user_life.user_id = local_user.id
                user_life.created_at = datetime.utcnow()
                db.sync(user_life)

                referral = ReferralRequest()
                referral.user_id = local_user.id
                referral.id = referred_id
                referral.created_at = datetime.utcnow()
                db.sync(referral)
            except Exception as e:
                log.error(e)
                raise

            self.referred(local_user, db)
            try:
                self.application.db_conn.get('ping').incr('user_count')
            except Exception as e:
                log.warn('User incr not completed: {}'.format(e))

            try:
                if 'nomail.me' not in local_user.email:
                    mail = self.application.settings.get('mailer')
                    path = '{}/assets'.format(self.application.settings.get('instance', {}).get('front'))
                    lShare = quote('{}/r/{}'.format(self.application.settings.get('instance', {}).get('api_email'),
                                                           referred_id))
                    log.info(lShare)
                    # faceid = self.application.settings.get('facebook_api_key')
                    mail.send(to=local_user.email,
                              format='html',
                              subject="Bem-vindo ao Desafio Next!",
                              body=self.render_string(
                                  "template-welcome.html",
                                  userName=local_user.name,
                                  path=path,
                                  shareFacebook=lShare,
                                  shareTwitter=lShare))
                    log.info('Email sent')
                else:
                    log.warning('User has no mail')
            except Exception as e:
                log.warn('EMAIL ERROR: {}'.format(e))

        except Exception as e:
            raise e

        finally:
            return local_user

    def gen_token(self, user):
        one_device(self, user, self.session.id)
        self.session['id'] = user.id
        self.session['facebook_id'] = user.facebook_id
        self.session['name'] = user.name

        return {'id': user.id,
                'facebook_id': user.facebook_id,
                'name': user.name}

    def referred(self, user, db):
        user_id = user.id
        log.info(user_id)
        if not self.session.get('referred', None):
            return

        log.info(self.session.get('referred'))
        try:
            referred_user = ReferralUser()
            referred_user.refered_id = self.session.get('referred')
            name = '{} {}'.format(user.facebook_data.get('first_name'), user.facebook_data.get('last_name', ''))
            referred_user.face_data = {'name': smart_truncate(name, 24), 'picture': user.avatar.get('small')}
            referred_user.user_id = user_id
            referred_user.created_at = datetime.utcnow()

            db.sync(referred_user)
            thisweek = (datetime.utcnow() - timedelta(days=2))
            start = (thisweek - timedelta(days=thisweek.weekday())).replace(hour=0, minute=0, second=0, microsecond=0)
            end = (start + timedelta(days=6)).replace(hour=23, minute=59, second=59, microsecond=999)
            log.info(start)
            log.info(end)
            references = db.query(ReferralUser).filter(ReferralUser.refered_id == referred_user.refered_id,
                                                       ReferralUser.created_at <= end,
                                                       ReferralUser.created_at >= start).count()

            log.info(references)
            if references < 15:
                udata = db.get(Life, rr='life', user_id=referred_user.refered_id)
                udata.incr_(life_qtd=1)
                log.info('added live')
                try:
                    udata.sync(constraints=[Life.life_qtd <= 15])
                    self.application.db_conn.get('ping').set(referred_user.refered_id, 1)
                    referred_user.life = 1
                    db.sync(referred_user)
                    log.info('pingued')
                except CheckFailed:
                    log.warn('User {} already received more than 15 lives this week.'.format(
                        self.session.get('referred', None)))
                finally:
                    self.session.delete('referred')

        except Exception as e:
            log.error('User {} could not receive an extra life from user {}. traceback: {}'.format(
                self.session.get('referred', None), user_id, e))


class FacebookFinishRedirectHandler(SessionBaseHandler):
    def initialize(self):
        self.db = self.application.settings.get('engine')

    def get(self):
        if self.current_user:
            self.finish(self.current_user)
