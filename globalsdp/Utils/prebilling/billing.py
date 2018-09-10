import time
import datetime
import redis


# Redis connection
# connection = redis.Redis(
#     host='gsdp-billing.4daowg.ng.0001.sae1.cache.amazonaws.com',
#     port=6379,
#     password='',
#     db='0',
# )
connection = redis.Redis(
    host='localhost',
    port=6379,
    password='',
    db='0',
)

# Billing file
file = "/home/ec2-user/billing.csv"

with open(file, "r") as file:
    content = file.readlines()

# Cache
for data in content:
    try:
        # line
        data = data.split(",")

        # subscription_id
        subscription_id = data[0].strip()

        # date
        created_at = data[1].strip().replace("\n", "")
        created_at = created_at.split(" ")
        _date = created_at[0].split("-")
        _time = created_at[1].split(":")
        d = datetime.datetime(int(_date[0]), int(_date[1]), int(_date[2]), int(_time[0]), int(_time[1]), int(_time[2]))

        # date of last billing
        timestamp_last_billing = time.mktime(d.timetuple())

        # date of the next billing
        timestamp_next_billing = timestamp_last_billing + 30*24*60*60  # last billing + 30 days

        # current date
        timestamp_now = time.time()

        # seconds left till the next billing
        seconds_left = int(timestamp_next_billing - timestamp_now)

        connection.setex(subscription_id, 0, seconds_left)

        print("***********************************")
        print("Created: {0}".format(subscription_id))
        print("***********************************")

    except Exception as e:
        print("***********************************")
        print("Erro: {0}".format(e))
        print("***********************************")
        continue
