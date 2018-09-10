root="/~/python/app/globalsdp/Code"

#Set env variable
export GATEWAY_ENV=homol
export C_FORCE_ROOT="true"

#Start virtualenv
source  /home/env/gateway/bin/activate

#Kill current celery processes
killall -9 celery


########################################################################################################################
############################################# WORKERS ##################################################################
########################################################################################################################

# Request
nohup celery -A celeryapp:celery_app worker -l DEBUG -c 10 -Q request -n worker_request.%h > /tmp/celery_request.log 2>&1 &

# Tim Camada
nohup celery -A celeryapp:celery_app worker -l DEBUG -c 5 -Q tim -n worker_tim.%h > /tmp/celery_tim.log 2>&1 &
nohup celery -A celeryapp:celery_app worker -l DEBUG -c 1 -Q tim.v1.partner.send_notification.error -n worker_tim_notification.%h > /tmp/celery_tim_send_notification_error.log 2>&1 &

# Tim Recarga
nohup celery -A celeryapp:celery_app worker -l DEBUG -c 5 -Q tim-etl -n worker_tim_etl.%h > /tmp/celery_tim_etl.log 2>&1 &

# Tim Fit
nohup celery -A celeryapp:celery_app worker -l DEBUG -c 1 -Q tim-fit -n worker_fit.%h > /tmp/celery_tim_fit.log 2>&1 &
nohup celery -A celeryapp:celery_app worker -l DEBUG -c 1 -Q tim-fit-mt-0 -n worker_fit_mt_0.%h > /tmp/celery_tim_fit.log 2>&1 &
nohup celery -A celeryapp:celery_app worker -l DEBUG -c 1 -Q tim-fit-mt-1 -n worker_fit_mt_1.%h > /tmp/celery_tim_fit.log 2>&1 &
nohup celery -A celeryapp:celery_app worker -l DEBUG -c 1 -Q tim-fit-mt-2 -n worker_fit_mt_2.%h > /tmp/celery_tim_fit.log 2>&1 &
nohup celery -A celeryapp:celery_app worker -l DEBUG -c 1 -Q tim-fit-mt-3 -n worker_fit_mt_3.%h > /tmp/celery_tim_fit.log 2>&1 &

# Algar
nohup celery -A celeryapp:celery_app worker -l DEBUG -c 5 -Q algar -n worker_algar.%h > /tmp/celery_algar.log 2>&1 &

# Claro
nohup celery -A celeryapp:celery_app worker -l DEBUG -c 5 -Q claro -n worker_claro.%h > /tmp/celery_claro.log 2>&1 &

# Oi
nohup celery -A celeryapp:celery_app worker -l DEBUG -c 5 -Q oi_mo -n worker_oi.%h > /tmp/celery_oi_mo.log 2>&1 &

# Nextel
nohup celery -A celeryapp:celery_app worker -l DEBUG -c 5 -Q nextel -n worker_nextel.%h > /tmp/celery_nextel.log 2>&1 &

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
# nohup celery -A celeryapp:celery_app beat -l DEBUG > /tmp/etl-tim.log 2>&1 &


########################################################################################################################
############################################# SERVICES #################################################################
########################################################################################################################

nohup sh $root/integrations/tim/fit/v1/files/receive_mo.sh > /tmp/tim_fit_receive_mo.txt 2>&1 &
