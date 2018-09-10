"""
Settings that is common to all environments: dev, homol and prod.
"""
import os
from datetime import timedelta
from celery.schedules import crontab

# Base dir of the project
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# Integrations directory
INTEGRATIONS_DIR = "{0}/../integrations".format(BASE_DIR)

# Active REST APIs
REST_MODULES = [
    'application',
    'integrations.tim.v1.api.rest',
    'integrations.tim.fit.v1.api.rest',
    'integrations.algar.v1.api.rest',
    'integrations.claro.v1.api.rest',
    'integrations.oi.v1.api.rest',
]

# Active Mock REST APIs
REST_MOCK_MODULES = [
    'integrations.tim.v1.api.rest.mock',
    'integrations.algar.v1.api.rest.mock',
    'integrations.claro.v1.api.rest.mock',
    'integrations.oi.v1.api.rest.mock',
]

# Active SOAP APIs
SOAP_MODULES = [
    'integrations.tim.v1.api.soap',
]

# Celery Tasks (Async)
CELERY_TASKS = [
    'integrations.tim.v1.services',
    'integrations.tim.fit.v1.services',
    'integrations.algar.v1.services',
    'integrations.claro.v1.services',
    'integrations.oi.v1.services',
    'integrations.nextel.v1.services',
]

# Celery Schedule (Jobs)
CELERY_SCHEDULE_TASKS = [
]

# Celery Routes
CELERY_ROUTES = {
    # Application
    'application.request': {'queue': 'request'},

    # Tim
    'tim.v1.partner.send_notification': {'queue': 'tim'},
    'tim.v1.partner.send_mo': {'queue': 'tim'},
    'integrations.tim.v1.utils.etl.recharge.async': {'queue': 'tim-etl'},

    # Tim Fit
    # 'tim.fit.v1.backend.send_mt': {'queue': 'tim-fit'},

    # Algar
    'algar.v1.partner.send_notification': {'queue': 'algar'},
    'algar.v1.partner.send_mo': {'queue': 'algar'},

    # Claro
    'claro.v1.partner.send_mt_notification': {'queue': 'claro'},
    'claro.v1.partner.send_mms_mt_notification': {'queue': 'claro'},
    'claro.v1.partner.send_wap_mt_notification': {'queue': 'claro'},
    'claro.v1.partner.send_wib_push_notification': {'queue': 'claro'},
    'claro.v1.partner.send_mo': {'queue': 'claro'},
    'claro.v1.partner.send_mms_mo': {'queue': 'claro'},

    # Oi
    'oi.v1.partner.send_mo_async': {'queue': 'oi_mo'},

    # Nextel
    'nextel.v1.partner.send_notification': {'queue': 'nextel'},
    'nextel.v1.partner.send_mo': {'queue': 'nextel'},

}

CELERY_ACCEPT_CONTENT = ['pickle', 'json', 'msgpack', 'yaml']

CELERY_RETRY = {
    'max_retries': 3,
    'default_retry_delay': 120,
}

CELERY_SERIALIZATION = 'yaml'
CELERY_TIMEZONE = 'UTC'

# Secret hashcode to access internal URLs
INTERNAL_SECRET = '864c536e7cf74794bc25aad23bf8b758'

# Logging
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'default': {
            'format': '%(asctime)s %(levelname)-5.5s [%(name)s][%(threadName)s] %(message)s'
        },
    },
    'loggers': {
        'root': {
            'level': 'DEBUG',
            'handlers': ['console'],
        },
        'application': {
            'level': 'INFO',
            'handlers': ['file'],
            'propagate': True,
        },
        'integrations': {
            'level': 'INFO',
            'handlers': ['file'],
            'propagate': True,
        },
        'celery': {
            'level': 'INFO',
            'handlers': ['file'],
            'propagate': True,
        }
    },
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
            'level': 'NOTSET',
            'formatter': 'default',
        },
        'file': {
            'class': 'logging.handlers.TimedRotatingFileHandler',
            'level': 'INFO',
            'formatter': 'default',
            'filename': "{0}/logs/gateway.log".format(BASE_DIR),
            'when': "D",
        },
    },
}
LOG_HASHES = {
    "application": {
        "mt": "dbb8fefd7bb54f11b3094f98151d60fa",
    },
    "oi": {
        "mt": "de93614b4e423fbe62a90d710efb7e",
        "billing": "b630a8e4e29e49a2a7b8268f716cd0e1",
        "check_credit": "f0e8e889769f448ab61177790a1ff52d",
        "mo": "d3bd7aa83e84a88ab011bbf610cc4dd9"
    },
    "claro": {
        "mt": "fe0589c5e7fe469a88g52f28b58076fb9",
        "mms_mt": "f22e0435a1c742db59a921ca1580d3c5c",
        "wap_mt": "c7e8cb7951514xde8bc6b65fc64c9698e",
        "billing": "a7b55e8ac4614470939f910ab071c1080",
        "check_credit": "f1c271afd4b6b9d6661036a42bfd8f",
        "wib_push": "b4fecb139584d8d9b4f061d02738658d",
        "mt_notification": "fc5329d33431418d02906cf56fcce8",
        "mms_mt_notification": "da6f99326cd3644b98b00aac934a66d3a",
        "wap_mt_notification": "e085b61c3ffb54b7291a1241e0933a9c6",
        "wib_push_notification": "b7d056076d88c443fbd7bf2f26773b519",
        "mo": "cee1d4d8ba94c434ca206425e3",
        "mms_mo": "b044e34aec8963a0ed1a5b80ae8"
    },
    "algar": {
        "signature": "f0c378ee9d6d4739b99137e4a1fa2d82",
        "cancellation": "e91071bf81cc4e5887fd62af8035b908",
        "mt": "d6695c34ba46c482347c5fcc9c6ecc",
        "billing": "893aeba98dc8448ead868b655a5daf5b",
        "signature_notification": "asd2345hgb6t35g4grvb3eyty",
        "cancellation_notification": "asdfd36y6u54yh35rbg24tgr",
        "auth_notification": "r4t8plkj890oplkjhu8iol3r",
        "mo": "b53a5167d9c44bfab57d1f912797361b"
    },
    "nextel": {
        "signature": "77ed412320a8401e8007cac8d330e19a",
        "cancellation": "2b3e0b41be74435b9e456e9c204f027c",
        "mt": "9559c0140d1541fb9bd514287985fe09",
        "billing": "a81e9419a6b5449bb1b07ae5ccbc998b",
        "signature_notification": "6ff0117702864dc28962cbdd7f533e0f",
        "cancellation_notification": "1234rfccx345hbv25yhgfq23rtg33",
        "auth_notification": "2rt54yhtgf2tg2ftg25t4gf4tgft3rc",
        "mo": "538032121f3a4ebb9c02f032113f742f",
    },
    "tim": {
        "cancellation": "84ca3d6cbc7e4f0e9ec400a1857b7e5c",
        "billing": "7debc81545e844399e67b9972ce7f088",
        "billing-status": "0aa766439d7847988506568df4efb0c9",
        "migration": "d739c7495fbe46779c570ee635a26a70",
        "mt": "456c8a04aa24496ba25b91410e8a0bba",
        "mo": "3004726f841242e7b482c2cf8f7b212b",
        "notification": "7f2c16dadea0459aa07f336b16986f5c",
    },
    "tim/fit": {
        "billing": "9e2f5e513e19485d8c04ac0e83896dbc",
        "mt": "faa37f547f5747b2a6bfd204181e9b0b",
        "mo": "d84cbdb50cbc44f2957f928d9a1f7ab0"
    },
}

# Request_id periodicity (7 days in seconds)
REQUEST_ID_PERIODICITY = 7 * 24 * 60 * 60
