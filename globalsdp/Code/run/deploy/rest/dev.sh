#Set env variable
export GATEWAY_ENV=dev

#Start server
killall -9 python
nohup python restapimock.py 8889 > /tmp/mock.log 2>&1 &
python restapi.py 8888
