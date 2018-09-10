###params
#$1 = port

#Set env variable
export GATEWAY_ENV=prod

#Start virtualenv
source  /home/env/globalsdp/bin/activate

#Start servers
python soapapi.py $1