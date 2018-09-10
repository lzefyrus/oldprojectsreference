/*
-- Query: SELECT * FROM gateway.tunnel where url like '%claro%'
LIMIT 0, 1000

-- Date: 2015-12-14 21:01
*/
INSERT INTO `tunnel` (`id`,`partner_id`,`parent_id`,`group_id`,`key`,`tps_min`,`tps_max`,`priority`,`url`) VALUES (38,5,NULL,NULL,'edf4382e8507409ca255db612d68b924',200,500,100,'/claro/v1/backend/mt/mms');
INSERT INTO `tunnel` (`id`,`partner_id`,`parent_id`,`group_id`,`key`,`tps_min`,`tps_max`,`priority`,`url`) VALUES (41,5,NULL,NULL,'a351a67e219b42dc9c94e8a9198e792a',200,500,100,'/claro/v1/backend/mt/sms');
INSERT INTO `tunnel` (`id`,`partner_id`,`parent_id`,`group_id`,`key`,`tps_min`,`tps_max`,`priority`,`url`) VALUES (42,5,NULL,NULL,'acd168a0d5b9433480ed3f961ac699f8',200,500,100,'/claro/v1/backend/check-credit');
INSERT INTO `tunnel` (`id`,`partner_id`,`parent_id`,`group_id`,`key`,`tps_min`,`tps_max`,`priority`,`url`) VALUES (43,5,NULL,NULL,'4d72173e5962419f8a535f78942c2ade',200,500,100,'/claro/v1/backend/billing');
INSERT INTO `tunnel` (`id`,`partner_id`,`parent_id`,`group_id`,`key`,`tps_min`,`tps_max`,`priority`,`url`) VALUES (44,5,NULL,NULL,'cd7ad366e8b6420b94313cccab2cae8f',200,500,100,'/claro/v1/backend/mt/wap');
INSERT INTO `tunnel` (`id`,`partner_id`,`parent_id`,`group_id`,`key`,`tps_min`,`tps_max`,`priority`,`url`) VALUES (45,5,NULL,NULL,'19e7c913c7334b9aa3383220e05e3b81',200,500,100,'/claro/v1/backend/wib-push');
