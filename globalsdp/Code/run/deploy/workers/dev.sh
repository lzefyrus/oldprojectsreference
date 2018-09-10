root="/home/fsroot/dev/globalsdp/Code"
venv="/home/fsroot/dev/env/gatewayframework/bin/activate"

#Set env variable
export GATEWAY_ENV=dev
export C_FORCE_ROOT="true"

#Start virtualenv
source $venv

#Kill current celery processes
killall -9 celery


########################################################################################################################
############################################# WORKERS ##################################################################
########################################################################################################################

# Request
nohup celery -A celeryapp:celery_app worker -l DEBUG -c 1 -Q request  > /tmp/celery_request.log 2>&1 &

# Tim Camada
nohup celery -A celeryapp:celery_app worker -l DEBUG -c 1 -Q tim  > /tmp/celery_tim.log 2>&1 &

# Tim Recarga
nohup celery -A celeryapp:celery_app worker -l DEBUG -c 1 -Q tim-etl  > /tmp/celery_tim_etl.log 2>&1 &

# Tim Fit
nohup celery -A celeryapp:celery_app worker -l DEBUG -c 1 -Q tim-fit  > /tmp/celery_tim_fit.log 2>&1 &
nohup celery -A celeryapp:celery_app worker -l DEBUG -c 1 -Q tim-fit-mt-0  > /tmp/celery_tim_fit.log 2>&1 &
nohup celery -A celeryapp:celery_app worker -l DEBUG -c 1 -Q tim-fit-mt-1  > /tmp/celery_tim_fit.log 2>&1 &
nohup celery -A celeryapp:celery_app worker -l DEBUG -c 1 -Q tim-fit-mt-2  > /tmp/celery_tim_fit.log 2>&1 &
nohup celery -A celeryapp:celery_app worker -l DEBUG -c 1 -Q tim-fit-mt-3  > /tmp/celery_tim_fit.log 2>&1 &

# Algar
nohup celery -A celeryapp:celery_app worker -l DEBUG -c 1 -Q algar  > /tmp/celery_algar.log 2>&1 &

# Claro
nohup celery -A celeryapp:celery_app worker -l DEBUG -c 1 -Q claro  > /tmp/celery_claro.log 2>&1 &

# Oi
nohup celery -A celeryapp:celery_app worker -l DEBUG -c 1 -Q oi_mo  > /tmp/celery_oi_mo.log 2>&1 &

# Nextel
nohup celery -A celeryapp:celery_app worker -l DEBUG -c 1 -Q nextel  > /tmp/celery_nextel.log 2>&1 &

# MT
nohup celery -A celeryapp:celery_app worker -l DEBUG -c 1 -Q globalsdp.mt.algar.0  > /tmp/celery_mt_algar_0.log 2>&1 &
nohup celery -A celeryapp:celery_app worker -l DEBUG -c 2 -Q globalsdp.mt.algar.1  > /tmp/celery_mt_algar_1.log 2>&1 &
nohup celery -A celeryapp:celery_app worker -l DEBUG -c 3 -Q globalsdp.mt.algar.2  > /tmp/celery_mt_algar_2.log 2>&1 &
nohup celery -A celeryapp:celery_app worker -l DEBUG -c 4 -Q globalsdp.mt.algar.3  > /tmp/celery_mt_algar_3.log 2>&1 &

nohup celery -A celeryapp:celery_app worker -l DEBUG -c 1 -Q globalsdp.mt.claro.0  > /tmp/celery_mt_claro_0.log 2>&1 &
nohup celery -A celeryapp:celery_app worker -l DEBUG -c 2 -Q globalsdp.mt.claro.1  > /tmp/celery_mt_claro_1.log 2>&1 &
nohup celery -A celeryapp:celery_app worker -l DEBUG -c 3 -Q globalsdp.mt.claro.2  > /tmp/celery_mt_claro_2.log 2>&1 &
nohup celery -A celeryapp:celery_app worker -l DEBUG -c 4 -Q globalsdp.mt.claro.3  > /tmp/celery_mt_claro_3.log 2>&1 &

nohup celery -A celeryapp:celery_app worker -l DEBUG -c 1 -Q globalsdp.mt.nextel.0  > /tmp/celery_mt_nextel_0.log 2>&1 &
nohup celery -A celeryapp:celery_app worker -l DEBUG -c 2 -Q globalsdp.mt.nextel.1  > /tmp/celery_mt_nextel_1.log 2>&1 &
nohup celery -A celeryapp:celery_app worker -l DEBUG -c 3 -Q globalsdp.mt.nextel.2  > /tmp/celery_mt_nextel_2.log 2>&1 &
nohup celery -A celeryapp:celery_app worker -l DEBUG -c 4 -Q globalsdp.mt.nextel.3  > /tmp/celery_mt_nextel_3.log 2>&1 &

nohup celery -A celeryapp:celery_app worker -l DEBUG -c 1 -Q globalsdp.mt.oi.0  > /tmp/celery_mt_oi_0.log 2>&1 &
nohup celery -A celeryapp:celery_app worker -l DEBUG -c 2 -Q globalsdp.mt.oi.1  > /tmp/celery_mt_oi_1.log 2>&1 &
nohup celery -A celeryapp:celery_app worker -l DEBUG -c 3 -Q globalsdp.mt.oi.2  > /tmp/celery_mt_oi_2.log 2>&1 &
nohup celery -A celeryapp:celery_app worker -l DEBUG -c 4 -Q globalsdp.mt.oi.3  > /tmp/celery_mt_oi_3.log 2>&1 &

nohup celery -A celeryapp:celery_app worker -l DEBUG -c 1 -Q globalsdp.mt.tim.0  > /tmp/celery_mt_tim_0.log 2>&1 &
nohup celery -A celeryapp:celery_app worker -l DEBUG -c 2 -Q globalsdp.mt.tim.1  > /tmp/celery_mt_tim_1.log 2>&1 &
nohup celery -A celeryapp:celery_app worker -l DEBUG -c 3 -Q globalsdp.mt.tim.2  > /tmp/celery_mt_tim_2.log 2>&1 &
nohup celery -A celeryapp:celery_app worker -l DEBUG -c 4 -Q globalsdp.mt.tim.3  > /tmp/celery_mt_tim_3.log 2>&1 &

nohup celery -A celeryapp:celery_app worker -l DEBUG -c 1 -Q globalsdp.mt.vivo.0  > /tmp/celery_mt_vivo_0.log 2>&1 &
nohup celery -A celeryapp:celery_app worker -l DEBUG -c 2 -Q globalsdp.mt.vivo.1  > /tmp/celery_mt_vivo_1.log 2>&1 &
nohup celery -A celeryapp:celery_app worker -l DEBUG -c 3 -Q globalsdp.mt.vivo.2  > /tmp/celery_mt_vivo_2.log 2>&1 &
nohup celery -A celeryapp:celery_app worker -l DEBUG -c 4 -Q globalsdp.mt.vivo.3  > /tmp/celery_mt_vivo_3.log 2>&1 &

########################################################################################################################
############################################# SCHEDULE #################################################################
########################################################################################################################

#Start Celery Beat
nohup celery -A celeryapp:celery_app beat -l DEBUG > /tmp/etl-tim.log 2>&1 &


########################################################################################################################
############################################# SERVICES #################################################################
########################################################################################################################

nohup sh $root/integrations/tim/fit/v1/files/receive_mo.sh $root > /tmp/tim_fit_receive_mo.txt 2>&1 &
