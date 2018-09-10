import time
from application.src.exceptions import TpsErrorException

# Settings
partner_name = 'oi'
api_version = 'v1'


def has_available_tps(redis, tunnel_key, tunnel_settings, handler):
    """
    Verifies if there is available TPS to proceed with the Billing/ Check Credit request.
    :param redis:
    :param tunnel_key:
    :param tunnel_settings:
    :return: bool
    """
    current_time = int(time.time())
    try:
        current_tunnel = tunnel_settings[tunnel_key]
        try:
            parent_tunnel = tunnel_settings[current_tunnel['parent_id']]
        except KeyError:
            raise TpsErrorException('Parent tunnel not found. A parent tunnel is mandatory for Billing TPS calculation.')

        key_current_tunnel = "{0}:{1}:{2}".format(tunnel_key, parent_tunnel['key'], current_time)
        tps_current_tunnel = redis.incr(key_current_tunnel)

        # On key creation, set ttl to 3 seconds:
        if tps_current_tunnel == 1:
            redis.expire(key_current_tunnel, 3)

        if int(tps_current_tunnel) > current_tunnel['tps_max']:
            redis.decr(key_current_tunnel)
            return False

        keys = redis.keys("{0}:{1}:{2}".format('*', parent_tunnel['key'], current_time))
        tps_parent_tunnel = 0

        for key in keys:
            tps_parent_tunnel += int(redis.get(key))

        if tps_parent_tunnel > parent_tunnel['tps_max']:
            return False
    except Exception as e:
        raise TpsErrorException("Error: {0}".format(e))

    return True


def has_available_tps_for_mt(redis, tunnel_key, tunnel_settings, handler):
    """
    Verifies if there is available TPS to proceed with the MT request.
    :param redis:
    :param tunnel_key:
    :param tunnel_settings:
    :return: bool
    """
    current_time = int(time.time())
    try:
        la = handler.get_argument('la', None, strip=True)

        try:
            current_tunnel = tunnel_settings['{0}/{1}/la/{2}'.format(partner_name, api_version, la)]
        except KeyError:
            raise TpsErrorException('LA {0} not found on any group inside tunnel settings.'.format(la))

        try:
            parent_tunnel = tunnel_settings[current_tunnel['parent_id']]
        except KeyError:
            raise TpsErrorException('Parent tunnel not found. A parent tunnel is mandatory for MT TPS calculation.')

        key_current_tunnel = "{0}:{1}".format(parent_tunnel['key'], current_time)
        current_tps = redis.incr(key_current_tunnel)

        # On key creation, set ttl to 3 seconds:
        if current_tps == 1:
            redis.expire(key_current_tunnel, 3)

        if current_tps > parent_tunnel['tps_max']:
            return False

        return True
    except Exception as e:
        raise TpsErrorException("Error: {0}".format(e))
