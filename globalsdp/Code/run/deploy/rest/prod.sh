###params
#$1 = port

#Set env variable
export GATEWAY_ENV=prod
export C_FORCE_ROOT="true"

#Start virtualenv
source  /home/env/globalsdp/bin/activate

#Cleans python cache
find . | egrep "*.pyc|__pycache__" | xargs rm -rf

#Start servers
killall -9 python
python restapi.py $1