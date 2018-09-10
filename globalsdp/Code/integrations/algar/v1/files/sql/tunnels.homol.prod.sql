/*
-- Query: SELECT * FROM gateway.tunnel where url like '%algar%'
LIMIT 0, 1000

-- Date: 2015-12-15 19:44
*/
INSERT INTO `tunnel` (`id`,`partner_id`,`parent_id`,`group_id`,`key`,`tps_min`,`tps_max`,`priority`,`url`) VALUES (34,3,NULL,NULL,'2f65d2aa9a634c70a54e14127da07de5',200,500,100,'/algar/v1/backend/signature');
INSERT INTO `tunnel` (`id`,`partner_id`,`parent_id`,`group_id`,`key`,`tps_min`,`tps_max`,`priority`,`url`) VALUES (35,3,NULL,NULL,'431111f92c6e4a888aa2f404771bbe94',200,500,100,'/algar/v1/backend/cancellation');
INSERT INTO `tunnel` (`id`,`partner_id`,`parent_id`,`group_id`,`key`,`tps_min`,`tps_max`,`priority`,`url`) VALUES (36,3,NULL,NULL,'cae8390b179d40d98aaab21928ebcf75',200,500,100,'/algar/v1/backend/mt');
INSERT INTO `tunnel` (`id`,`partner_id`,`parent_id`,`group_id`,`key`,`tps_min`,`tps_max`,`priority`,`url`) VALUES (37,3,NULL,NULL,'a65d8407b5424fdcb479e0691c89c61a',200,500,100,'/algar/v1/backend/billing');
