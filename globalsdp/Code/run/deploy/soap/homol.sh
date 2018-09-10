###params
#$1 = port

#Set env variable
export GATEWAY_ENV=homol

#Start virtualenv
source  /home/env/gateway/bin/activate

#Start servers
python soapapi.py $1
