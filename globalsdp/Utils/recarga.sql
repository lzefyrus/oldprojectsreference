SELECT subsys, tariff_id, r.value, created_at as _data, count(*) as qtt
FROM gateway.etl_tim_v1_recharge AS r
WHERE created_at BETWEEN DATE('2016-01-01') AND DATE('2016-01-31')
GROUP BY subsys, tariff_id, r.value
LIMIT 100000000;
