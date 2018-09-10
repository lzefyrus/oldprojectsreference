from functools import wraps
import logging
import json

# Logging handler
log = logging.getLogger(__name__)


def validate_mo(func):
    """
    Validates Oi MO request (mandatory params only)
    """
    @wraps(func)
    def with_mo(self):
        # Validating parameters

        error_list = []
        # Getting arguments
        from_ = self.get_argument('from', None, strip=True)
        if from_ is None:
            error_list.append('from')
        to = self.get_argument('to', None, strip=True)
        if to is None:
            error_list.append('to')
        text = self.get_argument('text', None, strip=True)
        if text is None:
            error_list.append('text')

        if error_list:
            log.error("Missing mandatory parameters in URL: {0}".format(error_list).replace('\n',' '))
            return self.error({"status": "NOK", "message": "Missing mandatory parameters in URL: {0}"
                              .format(error_list)})

        # Validating backend access configs:
        try:
            configs = {
                'host_fs_entertainment': self.application.settings['config']['oi/v1/backend/host/fs-entertainment']['value'],
                'url_fs_entertainment': self.application.settings['config']['oi/v1/backend/mo/url/fs-entertainment']['value'],
                'las_fs_entertainment': self.application.settings['config']['oi/v1/fs-entertainment/las']['value'],
                'host_fs': self.application.settings['config']['oi/v1/backend/host/fs']['value'],
                'url_fs': self.application.settings['config']['oi/v1/backend/mo/url/fs']['value'],
            }
        except KeyError as ke:
            message = "Could not find access configs for Oi: {0}. Internal Error.".format(ke)
            log.error(message.replace('\n',' '))
            return self.error({"status": "NOK", "message": message})

        try:
            json.loads(configs['las_fs_entertainment'])
        except Exception as e:
            message = "Invalid Json config for oi/v1/fs-entertainment/las. Internal Error"
            log.error("{0}: {1}".format(message, e).replace('\n',' '))
            return self.error({"status": "NOK", "message": message})

        #TODO: log de sucesso

        return func(self)
    return with_mo
