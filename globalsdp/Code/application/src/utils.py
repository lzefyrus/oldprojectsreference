"""
Random features goes here.
"""

from application.src.models import User, UserTunnel, UserLa, Tunnel, Prebilling, Partner
from application import settings


def decode(bytes):
    """
    Decodes bytes to string.
    :param bytes:
    :return:
    """
    return bytes.decode("utf-8")


def row2dict(row):
    """
    Turns a row into a dict.
    :param row:
    :return: dict
    """
    d = {}
    for column in row.__table__.columns:
        try:
            d[column.name] = int(getattr(row, column.name))
        except:
            d[column.name] = str(getattr(row, column.name))
    return d


def list2dict(list):
    """
    Turns a list into a dict.
    :param list:
    :return: dict
    """
    return {"{0}".format(item.key): row2dict(item) for item in list}


def get_tunnel_map(db):
    """
    Finds all tunnel data.
    :param db:
    :return: dict
    """
    query = db.query(Tunnel).all()
    tunnels_by_id = {tunnel.id: row2dict(tunnel) for tunnel in query}
    tunnels_by_key = {tunnel.key: row2dict(tunnel) for tunnel in query}
    tunnels = tunnels_by_id.copy()
    tunnels.update(tunnels_by_key)
    return tunnels


def get_auth_map(db):
    """
    Finds all authentication data.
    :param db:
    :return: dict
    """
    query = db.query(UserTunnel, User, Tunnel).join(User).join(Tunnel).all()
    return {"{0}-{1}-{2}".format(auth[1].key, auth[1].secret, auth[2].key): auth[2].url for auth in query}


def get_auth_la_map(db):
    """
    Finds all LA authentication data.
    :param db:
    :return: dict
    """
    query = db.query(UserLa, User).join(User).all()
    map = {}

    for auth_la in query:
        user_key = auth_la[1].key

        if user_key in map:
            map[user_key] += [auth_la[0].la]
        else:
            map[user_key] = [auth_la[0].la]

    return map


def get_prebilling_map(db):
    """
    Finds all prebilling data.
    :param db:
    :return: dict
    """
    query = db.query(Prebilling, Partner).join(Partner).all()
    map = {}

    for prebilling in query:
        partner = prebilling[1].name.lower()

        if partner in map:
            map[partner].update({prebilling[0].product: prebilling[0].periodicity*24*60*60})
        else:
            map[partner] = {prebilling[0].product: prebilling[0].periodicity*24*60*60}

    return map


def get_headers(headers, filter=None):
    """
    Turns tornado headers into a dict.
    :param headers:
    :param filter:
    :return: dict
    """
    filter = headers.keys() if filter is None else filter
    filter = [key.upper() for key in filter]  # Uppercase to avoid case sensitive issues.

    return {key: value for (key, value) in headers.get_all() if key.upper() in filter}


def get_files_path(module):
    """
    Returns the path for the "files" folder.
    :param module: The name of the module
    :return: the path of the "files" folder
    """
    return "{0}/{1}/files".format(settings.INTEGRATIONS_DIR, module)


def get_optional_key(json, key, default_value=None):
    """
    Get an optional value from a dict.
    :param json:
    :param key:
    :param default_value:
    :return:
    """
    try:
        return json[key]
    except KeyError:
        return default_value


def str2bool(string):
    """
    Converts string to bool
    :param string:
    :return: bool
    """
    return str(string).lower() in ("yes", "true", "t", "1")
