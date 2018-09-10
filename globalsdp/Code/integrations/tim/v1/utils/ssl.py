from application.src import utils
import os

def get_cert_file():
    """
    Returns the ssl cert file.
    :return:
    """
    return "{0}/{1}".format(utils.get_files_path("tim/v1"), "SR15322081.cer")


def verify():
    """
    If in production environment we must verify ssl.
    :return: boolean
    """
    # return True if os.environ['GATEWAY_ENV'] == 'prod' else False
    return False
