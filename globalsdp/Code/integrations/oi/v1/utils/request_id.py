
def get_request_uid_func(handler):
    return handler.get_argument('uid', None, strip=True)
