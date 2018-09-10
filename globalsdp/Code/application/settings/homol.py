"""
Settings for homol environment.
"""

DEBUG = True

# Database
DATABASES = {
    'mysql-writer': {
        'NAME': 'gateway',
        'USER': 'root',
        'PASSWORD': '',
        'HOST': 'localhost',
        'PORT': 3306,
        'CHARSET': 'utf8',
    },
    'mysql-reader': {
        'NAME': 'gateway',
        'USER': 'root',
        'PASSWORD': '',
        'HOST': 'localhost',
        'PORT': 3306,
        'CHARSET': 'utf8',
    },
    'redis-tps': {
        'DB': '0',
        'PASSWORD': '',
        'HOST': 'localhost',
        'PORT': 6379,
    },
    'redis-celery': {
        'DB': '1',
        'PASSWORD': '',
        'HOST': 'localhost',
        'PORT': 6379,
    },
    'redis-prebilling': {
        'DB': '2',
        'PASSWORD': '',
        'HOST': 'localhost',
        'PORT': 6379,
    },
    'redis-request-id': {
        'DB': '3',
        'PASSWORD': '',
        'HOST': 'localhost',
        'PORT': 6379,
    },
    'rabbit': {
        'USER': 'gsdp',
        'PASSWORD': 'gsdp',
        'HOST': 'internal-lbi-queue-global-1622311459.sa-east-1.elb.amazonaws.com',
        'PORT': 5672,
    }
}

# TORNADO
TORNADO_SOCKETS = 50

# Celery
CELERY_BROKER = 'redis://{0}:{1}/{2}'.format(
    DATABASES["redis-celery"]["HOST"],
    DATABASES["redis-celery"]["PORT"],
    DATABASES["redis-celery"]["DB"]
)
# CELERY_BROKER = 'amqp://{0}:{1}@{2}:{3}'.format(
#     DATABASES["rabbit"]["USER"],
#     DATABASES["rabbit"]["PASSWORD"],
#     DATABASES["rabbit"]["HOST"],
#     DATABASES["rabbit"]["PORT"]
# )

CELERY_RESULT_BACKEND = 'db+mysql://{0}:{1}@{2}/{3}'.format(
    DATABASES["mysql-writer"]["USER"],
    DATABASES["mysql-writer"]["PASSWORD"],
    DATABASES["mysql-writer"]["HOST"],
    DATABASES["mysql-writer"]["NAME"],
)
