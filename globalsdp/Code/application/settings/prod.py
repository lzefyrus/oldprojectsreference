"""
Settings for prod environment.
"""

DEBUG = False

# Database
DATABASES = {
    'mysql-writer': {
        'NAME': 'gateway',
        'USER': 'app_globalsdp',
        'PASSWORD': 'A3zBoHoxGfqVK7IrBHD4',
        'HOST': 'globalsdp.clkadcgt8mnt.sa-east-1.rds.amazonaws.com',
        'PORT': 3306,
        'CHARSET': 'utf8',
    },
    'mysql-reader': {
        'NAME': 'gateway',
        'USER': 'app_globalsdp',
        'PASSWORD': 'A3zBoHoxGfqVK7IrBHD4',
        'HOST': 'globalsdp-read.clkadcgt8mnt.sa-east-1.rds.amazonaws.com',
        'PORT': 3306,
        'CHARSET': 'utf8',
    },
    'redis-tps': {
        'DB': '0',
        'PASSWORD': '',
        # 'HOST': 'global-sdp.4daowg.ng.0001.sae1.cache.amazonaws.com',
        'HOST': '10.170.31.11',
        'PORT': 6379,
    },
    'redis-request-id': {
        'DB': '2',
        'PASSWORD': '',
        # 'HOST': 'global-sdp.4daowg.ng.0001.sae1.cache.amazonaws.com',
        'HOST': '10.170.31.11',
        'PORT': 6379,
    },
    'redis-prebilling': {
        'DB': '0',
        'PASSWORD': '',
        'HOST': 'gsdp-billing.4daowg.ng.0001.sae1.cache.amazonaws.com',
        'PORT': 6379,
    },
    'rabbit': {
        'USER': 'gsdp',
        'PASSWORD': 'gsdp',
        'HOST': '10.170.224.194',
        'PORT': 5672,
    }
}

# TORNADO
TORNADO_SOCKETS = 150

# Celery
# CELERY_BROKER = 'redis://{0}:{1}/{2}'.format(
#     DATABASES["redis-celery"]["HOST"],
#     DATABASES["redis-celery"]["PORT"],
#     DATABASES["redis-celery"]["DB"]
# )

CELERY_BROKER = 'amqp://{0}:{1}@{2}:{3}'.format(
    DATABASES["rabbit"]["USER"],
    DATABASES["rabbit"]["PASSWORD"],
    DATABASES["rabbit"]["HOST"],
    DATABASES["rabbit"]["PORT"]
)

CELERY_RESULT_BACKEND = 'db+mysql://{0}:{1}@{2}/{3}'.format(
    DATABASES["mysql-writer"]["USER"],
    DATABASES["mysql-writer"]["PASSWORD"],
    DATABASES["mysql-writer"]["HOST"],
    DATABASES["mysql-writer"]["NAME"],
)
