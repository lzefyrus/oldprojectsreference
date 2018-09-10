/*
-- Query: SELECT * FROM gateway.config c where c.key like '%algar%'
LIMIT 0, 1000

-- Date: 2015-12-15 19:44
*/
INSERT INTO `config` (`id`,`key`,`value`) VALUES (61,'algar/v1/host','http://200.233.216.80');
INSERT INTO `config` (`id`,`key`,`value`) VALUES (63,'algar/v1/company/id','61');
INSERT INTO `config` (`id`,`key`,`value`) VALUES (64,'algar/v1/22020/user','A416BRTec');
INSERT INTO `config` (`id`,`key`,`value`) VALUES (65,'algar/v1/22020/password','kx437Y');
INSERT INTO `config` (`id`,`key`,`value`) VALUES (66,'algar/v1/signature/code','5');
INSERT INTO `config` (`id`,`key`,`value`) VALUES (67,'algar/v1/signature/description','Subscribe channel');
INSERT INTO `config` (`id`,`key`,`value`) VALUES (68,'algar/v1/signature/auth/type','0');
INSERT INTO `config` (`id`,`key`,`value`) VALUES (69,'algar/v1/signature/notification/type','208');
INSERT INTO `config` (`id`,`key`,`value`) VALUES (70,'algar/v1/signature/notification/calltype','1');
INSERT INTO `config` (`id`,`key`,`value`) VALUES (71,'algar/v1/signature/notification/callback','http://localhost:8888/algar/v1/notification');
INSERT INTO `config` (`id`,`key`,`value`) VALUES (72,'algar/v1/cancellation/description','Unsubscribe channel');
INSERT INTO `config` (`id`,`key`,`value`) VALUES (73,'algar/v1/cancellation/code','6');
INSERT INTO `config` (`id`,`key`,`value`) VALUES (74,'algar/v1/mt/keepsession','False');
INSERT INTO `config` (`id`,`key`,`value`) VALUES (75,'algar/v1/mt/notification/type','5');
INSERT INTO `config` (`id`,`key`,`value`) VALUES (76,'algar/v1/mt/notification/calltype','0');
INSERT INTO `config` (`id`,`key`,`value`) VALUES (77,'algar/v1/mt/notification/callback','http://localhost:8888/algar/v1/notification');
INSERT INTO `config` (`id`,`key`,`value`) VALUES (78,'algar/v1/mt/url','InterfaceXML/Tangram.aspx');
INSERT INTO `config` (`id`,`key`,`value`) VALUES (79,'algar/v1/cancellation/url','InterfaceXML/Tangram.aspx');
INSERT INTO `config` (`id`,`key`,`value`) VALUES (80,'algar/v1/signature/url','InterfaceXML/Tangram.aspx');
INSERT INTO `config` (`id`,`key`,`value`) VALUES (105,'algar/v1/billing/code','0');
INSERT INTO `config` (`id`,`key`,`value`) VALUES (106,'algar/v1/billing/description','Register transaction');
INSERT INTO `config` (`id`,`key`,`value`) VALUES (107,'algar/v1/billing/transaction/type','4');
INSERT INTO `config` (`id`,`key`,`value`) VALUES (108,'algar/v1/billing/transaction/description','MO billing request');
INSERT INTO `config` (`id`,`key`,`value`) VALUES (109,'algar/v1/backend/mo/url','mo');
INSERT INTO `config` (`id`,`key`,`value`) VALUES (110,'algar/v1/billing/url','InterfaceXML/Tangram.aspx');
INSERT INTO `config` (`id`,`key`,`value`) VALUES (122,'algar/v1/mo/fail/description/text','Could not receive MO. Internal Server Error.');
INSERT INTO `config` (`id`,`key`,`value`) VALUES (123,'algar/v1/backend/url/notification/authentication','notification/authentication');
INSERT INTO `config` (`id`,`key`,`value`) VALUES (124,'algar/v1/backend/url/notification/signature','notification/authentication');
INSERT INTO `config` (`id`,`key`,`value`) VALUES (174,'algar/v1/backend/host','http://localhost:8889/algar-mock/backend/v1');
INSERT INTO `config` (`id`,`key`,`value`) VALUES (175,'algar/v1/mo/ack','true');
INSERT INTO `config` (`id`,`key`,`value`) VALUES (176,'algar/v1/mo/is_billing','false');
INSERT INTO `config` (`id`,`key`,`value`) VALUES (177,'algar/v1/mo/keep_session','true');
INSERT INTO `config` (`id`,`key`,`value`) VALUES (178,'algar/v1/mo/description/code','0');
INSERT INTO `config` (`id`,`key`,`value`) VALUES (179,'algar/v1/mo/description/text','Mensagem recebida com sucesso');
INSERT INTO `config` (`id`,`key`,`value`) VALUES (180,'algar/v1/backend/notification/message','Message successfully received.');
INSERT INTO `config` (`id`,`key`,`value`) VALUES (182,'algar/v1/backend/notification/error/message','Could not receive message. Internal Server Error.');
INSERT INTO `config` (`id`,`key`,`value`) VALUES (249,'algar/v1/22020/service-id','1');
INSERT INTO `config` (`id`,`key`,`value`) VALUES (250,'algar/v1/22030/user','A417BRTec');
INSERT INTO `config` (`id`,`key`,`value`) VALUES (251,'algar/v1/22030/password','z6aR27');
INSERT INTO `config` (`id`,`key`,`value`) VALUES (252,'algar/v1/22030/service-id','2');
INSERT INTO `config` (`id`,`key`,`value`) VALUES (253,'algar/v1/40810/user','A419BRTec');
INSERT INTO `config` (`id`,`key`,`value`) VALUES (254,'algar/v1/40810/password','7xR14c');
INSERT INTO `config` (`id`,`key`,`value`) VALUES (255,'algar/v1/40810/service-id','4');
INSERT INTO `config` (`id`,`key`,`value`) VALUES (256,'algar/v1/77000/user','A418BRTec');
INSERT INTO `config` (`id`,`key`,`value`) VALUES (257,'algar/v1/77000/password','pH48y5');
INSERT INTO `config` (`id`,`key`,`value`) VALUES (258,'algar/v1/77000/service-id','3');
INSERT INTO `config` (`id`,`key`,`value`) VALUES (259,'algar/v1/77011/user','A420BRTec');
INSERT INTO `config` (`id`,`key`,`value`) VALUES (260,'algar/v1/77011/password','nC5T29');
INSERT INTO `config` (`id`,`key`,`value`) VALUES (261,'algar/v1/77011/service-id','5');
INSERT INTO `config` (`id`,`key`,`value`) VALUES (262,'algar/v1/77013/user','A420BRTec');
INSERT INTO `config` (`id`,`key`,`value`) VALUES (263,'algar/v1/77013/password','nC5T29');
INSERT INTO `config` (`id`,`key`,`value`) VALUES (264,'algar/v1/77013/service-id','5');
INSERT INTO `config` (`id`,`key`,`value`) VALUES (265,'algar/v1/77014/user','A420BRTec');
INSERT INTO `config` (`id`,`key`,`value`) VALUES (266,'algar/v1/77014/password','nC5T29');
INSERT INTO `config` (`id`,`key`,`value`) VALUES (267,'algar/v1/77014/service-id','5');
INSERT INTO `config` (`id`,`key`,`value`) VALUES (268,'algar/v1/322/user','A425FSvas');
INSERT INTO `config` (`id`,`key`,`value`) VALUES (269,'algar/v1/322/password','zt84u2');
INSERT INTO `config` (`id`,`key`,`value`) VALUES (270,'algar/v1/322/service-id','4');
INSERT INTO `config` (`id`,`key`,`value`) VALUES (271,'algar/v1/323/user','A410FSVAS');
INSERT INTO `config` (`id`,`key`,`value`) VALUES (272,'algar/v1/323/password','j7xn83');
INSERT INTO `config` (`id`,`key`,`value`) VALUES (273,'algar/v1/323/service-id','2');
