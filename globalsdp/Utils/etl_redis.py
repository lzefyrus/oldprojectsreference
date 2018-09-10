__author__ = 'fsroot'

import redis
import sys

# Args
db = sys.argv[1]

# TODO: Run this script for DB 2
try:

    old_redis = redis.Redis(
        host="global-sdp.4daowg.ng.0001.sae1.cache.amazonaws.com",
        port=6379,
        password="",
        db=db
    )

    new_redis = redis.Redis(
        host="",
        port=6379,
        password="",
        db=db
    )

    keys = old_redis.keys('*')
    for key in keys:
        new_redis.set(key, old_redis.get(key))

    print("Successfully finished!!!")

except Exception as e:
    print("Error: {0}".format(e))


