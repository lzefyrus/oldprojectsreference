###params
#$1 = port


#Set env variable
export GATEWAY_ENV=homol
export C_FORCE_ROOT="true"

#Start virtualenv
source  /home/env/gateway/bin/activate

#Start servers
killall -9 python
nohup python restapimock.py 8889 > /tmp/mock.log 2>&1 &
python restapi.py $1