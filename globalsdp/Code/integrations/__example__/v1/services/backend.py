"""
Backend services
"""

import requests
import json
import logging

# Logging handler
log = logging.getLogger(__name__)


##### CANCELLATION #####
########################
class CancellationService(object):
    def cancel(configs, param1, param2):
        request_url = '{0}/{1}'.format(configs['host'], configs['url'])
        return requests.post(request_url, data=json.dumps(param1))


##### MT #####
##############
class MtService(object):
    def send_mt(configs, param1, param2):
        request_url = '{0}/{1}'.format(configs['host'], configs['url'])
        return requests.post(request_url, data=json.dumps(param1))
