# -*- encoding: utf-8 -*-

import logging
from tornado.escape import json_decode
from application.src.rewrites import APIHandler
from application.src.models import Config, Tunnel
from application.src.auth import internal
from application.src import utils
from application import settings
from application.src.validators import validate_mt
from application.src import services


# Logging handler
log = logging.getLogger(__name__)
LOG_HASH_MT = settings.LOG_HASHES["application"]["mt"]


class ConfigHandler(APIHandler):
    """
    Config API.
    """

    __urls__ = [r"/config", r"/config/"]

    @internal
    def get(self):
        db = self.application.db
        configs = utils.list2dict(db.query(Config).all())
        return self.success(configs)

    @internal
    def post(self):
        db = self.application.db

        key = self.get_argument('key', None, strip=True)
        value = self.get_argument('value', None, strip=True)

        if not key or not value:
            log.error("Could not add Config on POST method! Key or Value not in request.")
            return self.error({"message": "Key or Value not found"})

        config = db.query(Config).filter_by(key=key).all()

        if config:
            log.warning("Config not added on POST method! Key {0} already in use.".format(key))
            return self.error({"message": "Key {0} already in use, try update it with PUT method".format(key)})

        config = Config(key=key, value=value)

        try:
            db.begin()
            db.add(config)
            db.commit()

            log.info("Config {0} successfully added with value {1}.".format(key, value))
            return self.success({"message": "{0}:{1} successfully added".format(key, value)})
        except:
            db.rollback()

            log.warning("Could not add config. Key {0}. Value {1}.".format(key, value))
            return self.error({"message": "Could not add config."})

    @internal
    def put(self):
        db = self.application.db

        key = self.get_argument('key', None, strip=True)
        value = self.get_argument('value', None, strip=True)

        if not key or not value:
            log.error("Could not update Config on PUT method! Key or Value not in request.")
            return self.error({"message": "Key or Value not found"})

        try:
            config = db.query(Config).filter_by(key=key).one()
            config.value = value
        except Exception as e:
            log.warning("Could not update Config on PUT method! Key {} not in use.".format(key))
            return self.error({"message": "Key not in use, try create it with POST method"})

        try:
            db.begin()
            db.add(config)
            db.commit()

            log.info("Config {0} successfully updated with value {1}.".format(key, value))
            return self.success({"message": "{0}:{1} successfully updated".format(key, value)})
        except:
            db.rollback()

            log.warning("Could not update config. Key {0}. Value {1}.".format(key, value))
            return self.error({"message": "Could not update config."})

    @internal
    def delete(self):
        db = self.application.db
        key = self.get_argument('key', None, strip=True)

        if not key:
            log.error("Could not DELETE Config! Key not in request.")
            return self.error({"message": "Key not found"})

        try:
            config = db.query(Config).filter_by(key=key).one()

            db.begin()
            db.delete(config)
            db.commit()

            log.info("Config {0} successfully removed.".format(key))
            return self.success({"message": "{0} successfully removed".format(key)})
        except Exception as e:
            db.rollback()

            log.error("Could not DELETE Config! Reason: {0}.".format(e))
            return self.error({"message": "Could not delete"})


class ConfigCacheHandler(APIHandler):
    """
    Config Cache API.
    """

    __urls__ = [r"/config/cache", r"/config/cache/"]

    @internal
    def get(self):
        configs = self.application.settings['config']
        return self.success(configs)

    @internal
    def post(self):
        db = self.application.db
        self.application.settings['config'] = utils.list2dict(db.query(Config).all())
        log.info("Config cache successfully updated.")
        return self.success({"message": "Config cache successfully updated"})


class TunnelHandler(APIHandler):
    """
    Tunnel API.
    """

    __urls__ = [r"/tunnel", r"/tunnel/"]

    @internal
    def get(self):
        db = self.application.db
        tunnels = utils.list2dict(db.query(Tunnel).all())
        return self.success(tunnels)

    @internal
    def post(self):
        db = self.application.db
        partner_id = self.get_argument('partner_id', None)
        parent_id = self.get_argument('parent_id', None)
        group_id = self.get_argument('group_id', None)
        key = self.get_argument('key', None, strip=True)
        tps_min = self.get_argument('tps_min', None)
        tps_max = self.get_argument('tps_max', None)
        priority = self.get_argument('priority', None)
        url = self.get_argument('url', None, strip=True)

        tunnel = db.query(Tunnel).filter_by(key=key).all()
        if tunnel:
            log.warning("Could not add Tunnel on POST method! Key {0} already in use.".format(key))
            return self.error({"message": "Key {0} already in use, try update it with PUT method".format(key)})

        tunnel = Tunnel(partner_id=partner_id, parent_id=parent_id, group_id=group_id,
                        key=key, tps_min=tps_min, tps_max=tps_max, priority=priority, url=url)

        try:
            db.begin()
            db.add(tunnel)
            db.commit()

            log.info("Tunnel {0} successfully added".format(key))
            return self.success({"message": "{0} successfully added".format(key)})
        except:
            db.rollback()

            log.error("Could not add tunnel. Key {0}. Value {1}.".format(key))
            return self.error({"message": "Could not add tunnel."})

    @internal
    def put(self):
        db = self.application.db
        partner_id = self.get_argument('partner_id', None)
        parent_id = self.get_argument('parent_id', None)
        group_id = self.get_argument('group_id', None)
        key = self.get_argument('key', None, strip=True)
        tps_min = self.get_argument('tps_min', None)
        tps_max = self.get_argument('tps_max', None)
        priority = self.get_argument('priority', None)
        url = self.get_argument('url', None, strip=True)

        try:
            tunnel = db.query(Tunnel).filter_by(key=key).one()
            tunnel.partner_id = partner_id if partner_id else tunnel.partner_id
            tunnel.parent_id = parent_id if parent_id else tunnel.parent_id
            tunnel.group_id = group_id if group_id else tunnel.group_id
            tunnel.key = key if key else tunnel.key
            tunnel.tps_min = tps_min if tps_min else tunnel.tps_min
            tunnel.tps_max = tps_max if tps_max else tunnel.tps_max
            tunnel.priority = priority if priority else tunnel.priority
            tunnel.url = url if url else tunnel.url
        except:
            log.warning("Could not update Tunnel on PUT method! Key {0} not in use".format(key))
            return self.error({"message": "Key not in use, try create it with POST method"})

        try:
            db.begin()
            db.add(tunnel)
            db.commit()

            log.info('Tunnel {0} successfully updated'.format(key))
            return self.success({"message": "{0} successfully updated".format(key)})
        except:
            db.rollback()

            log.error("Could not update tunnel. Key {0}.".format(key))
            return self.error({"message": "Could not update tunnel."})

    @internal
    def delete(self):
        db = self.application.db
        key = self.get_argument('key', None, strip=True)

        if not key:
            log.error("Could not DELETE Tunnel! Key {0} not in request.".format(key))
            return self.error({"message": "Key not found"})

        try:
            tunnel = db.query(Tunnel).filter_by(key=key).one()

            db.begin()
            db.delete(tunnel)
            db.commit()

            log.info('Tunnel {0} successfully removed.'.format(key))
            return self.success({"message": "{0} successfully removed".format(key)})
        except Exception as e:
            db.rollback()

            log.error("Could not DELETE Tunnel! Reason: {0}.".format(e))
            return self.error({"message": "Could not delete"})


class TunnelCacheHandler(APIHandler):
    """
    Tunnel Cache API.
    """

    __urls__ = [r"/tunnel/cache", r"/tunnel/cache/"]

    @internal
    def get(self):
        tunnels = self.application.settings['tunnel']
        return self.success(tunnels)

    @internal
    def post(self):
        db = self.application.db
        self.application.settings['tunnel'] = utils.list2dict(db.query(Tunnel).all())

        log.info('Tunnel cache successfully updated.')
        return self.success({"message": "Tunnel cache successfully updated"})


class AuthCacheHandler(APIHandler):
    """
    Auth Cache API.
    """

    __urls__ = [r"/auth/cache", r"/auth/cache/"]

    @internal
    def get(self):
        auth = self.application.settings['auth']
        return self.success(auth)

    @internal
    def post(self):
        db = self.application.db
        self.application.settings['auth'] = utils.get_auth_map(db)

        log.info('Auth cache successfully updated.')
        return self.success({"message": "Auth cache successfully updated"})


class MtHandler(APIHandler):
    """
    Generic MT API.
    """

    __urls__ = [r"/api/v1/mt(?:/)?"]

    @validate_mt
    def post(self):
        """
        Receives POST requests.
        :return:
        """
        # Getting body
        body = json_decode(self.request.body)

        try:
            # Getting parameters
            msisdn = str(body['msisdn'])
            la = str(body['la'])
            text = str(body['text'])
            carrier = str(body['carrier'])

            # Getting service class according to carrier
            service = getattr(services, "Mt" + carrier.capitalize())

            # Getting configs
            configs = service.get_configs(self.application.settings['config'])

            # Async call
            if "async" in body:
                priority = body['async']['priority']
                callback = body['async']['callback']

                service.send.apply_async(
                    args=[configs, msisdn, la, text, callback],
                    queue="globalsdp.mt.{0}.{1}".format(carrier, priority),
                    serializer=settings.CELERY_SERIALIZATION
                )

                # Log success
                log.info("MT queued. "
                         "Request body: {0}. "
                         "Request headers: {1}. "
                         "Operation Hash: {2}. "
                         .format(body, self.request.headers, LOG_HASH_MT))

                # Return success
                return self.success({"message": "MT successfully queued", "success": 1})

            # Sync call
            response = service.send(configs, msisdn, la, text)

            if response.status_code not in [200, 201, 202]:
                # Log error
                log.error("Could not send MT. "
                          "Request body: {0}. "
                          "Request headers: {1}. "
                          "Response body: {2}. "
                          "Response code: {3}. "
                          "Operation Hash: {4}. "
                          .format(body, self.request.headers, response.text, response.status_code,
                                  LOG_HASH_MT))

                # Return error
                return self.error({"message": "Could not send MT", "success": 0})

            # Log success
            log.info("MT sent to partner. "
                     "Request body: {0}. "
                     "Request headers: {1}. "
                     "Response body: {2}. "
                     "Response code: {3}. "
                     "Operation Hash: {4}. "
                     .format(body, self.request.headers, response.text, response.status_code, LOG_HASH_MT))

            # Return success
            return self.success({"message": "MT sent: {0}".format(response.text), "success": 1})

        except Exception as e:
            # Log error
            log.error("Could not send MT. "
                      "Error: {0}. "
                      "Request body: {1}. "
                      "Request headers: {2}. "
                      "Operation Hash: {3}. "
                      .format(e, body, self.request.headers, LOG_HASH_MT))

            # Return error
            return self.error({"message": "Could not send MT", "success": 0}, 500)
