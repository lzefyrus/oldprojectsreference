from tornado.escape import json_decode

def get_la_func(handler):
    body = json_decode(handler.request.body)
    return body['la']
