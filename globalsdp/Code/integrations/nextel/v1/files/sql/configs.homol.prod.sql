/*
-- Query: SELECT * FROM gateway.config c where c.key like '%nextel%'
LIMIT 0, 1000

-- Date: 2015-12-15 19:27
*/
INSERT INTO `config` (`key`,`value`) VALUES ('nextel/v1/company/id','4');
INSERT INTO `config` (`key`,`value`) VALUES ('nextel/v1/27118/user','fsvas_nx_cloud');
INSERT INTO `config` (`key`,`value`) VALUES ('nextel/v1/27118/password','Nl7Xyx2c');
INSERT INTO `config` (`key`,`value`) VALUES ('nextel/v1/signature/code','5');
INSERT INTO `config` (`key`,`value`) VALUES ('nextel/v1/signature/description','Subscribe channel');
INSERT INTO `config` (`key`,`value`) VALUES ('nextel/v1/signature/auth/type','0');
INSERT INTO `config` (`key`,`value`) VALUES ('nextel/v1/signature/notification/type','208');
INSERT INTO `config` (`key`,`value`) VALUES ('nextel/v1/signature/notification/calltype','1');
INSERT INTO `config` (`key`,`value`) VALUES ('nextel/v1/signature/notification/callback','http://globalsdp-nextel.whitelabel.com.br/nextel/v1/notification/signature');
INSERT INTO `config` (`key`,`value`) VALUES ('nextel/v1/host','https://api.nextel.vashub.net');
INSERT INTO `config` (`key`,`value`) VALUES ('nextel/v1/cancellation/code','6');
INSERT INTO `config` (`key`,`value`) VALUES ('nextel/v1/cancellation/description','Unsubscribe channel');
INSERT INTO `config` (`key`,`value`) VALUES ('nextel/v1/mt/keepsession','false');
INSERT INTO `config` (`key`,`value`) VALUES ('nextel/v1/mt/notification/type','5');
INSERT INTO `config` (`key`,`value`) VALUES ('nextel/v1/mt/notification/calltype','0');
INSERT INTO `config` (`key`,`value`) VALUES ('nextel/v1/mt/notification/callback','globalsdp-nextel.whitelabel.com.br/nextel/v1/mo');
INSERT INTO `config` (`key`,`value`) VALUES ('nextel/v1/mt/url','InterfaceXML/Tangram.aspx');
INSERT INTO `config` (`key`,`value`) VALUES ('nextel/v1/cancellation/url','InterfaceXML/Tangram.aspx');
INSERT INTO `config` (`key`,`value`) VALUES ('nextel/v1/signature/url','InterfaceXML/Tangram.aspx');
INSERT INTO `config` (`key`,`value`) VALUES ('nextel/v1/billing/code','0');
INSERT INTO `config` (`key`,`value`) VALUES ('nextel/v1/billing/description','Register transaction');
INSERT INTO `config` (`key`,`value`) VALUES ('nextel/v1/billing/transaction/type','4');
INSERT INTO `config` (`key`,`value`) VALUES ('nextel/v1/billing/transaction/description','MO billing request');
INSERT INTO `config` (`key`,`value`) VALUES ('nextel/v1/billing/url','InterfaceXML/Tangram.aspx');
INSERT INTO `config` (`key`,`value`) VALUES ('nextel/v1/backend/mo/url','mo');
INSERT INTO `config` (`key`,`value`) VALUES ('nextel/v1/backend/host','http://nextel-homol.whitelabel.com.br');
INSERT INTO `config` (`key`,`value`) VALUES ('nextel/v1/mo/ack','true');
INSERT INTO `config` (`key`,`value`) VALUES ('nextel/v1/mo/is_billing','false');
INSERT INTO `config` (`key`,`value`) VALUES ('nextel/v1/mo/keep_session','true');
INSERT INTO `config` (`key`,`value`) VALUES ('nextel/v1/mo/description/code','0');
INSERT INTO `config` (`key`,`value`) VALUES ('nextel/v1/mo/description/text','Mensagem recebida com sucesso');
INSERT INTO `config` (`key`,`value`) VALUES ('nextel/v1/mo/fail/description/text','Could not receive MO. Internal Server Error.');
INSERT INTO `config` (`key`,`value`) VALUES ('nextel/v1/backend/url/notification/signature','notification/signature');
INSERT INTO `config` (`key`,`value`) VALUES ('nextel/v1/backend/url/notification/authentication','notification/authentication');
INSERT INTO `config` (`key`,`value`) VALUES ('nextel/v1/backend/notification/message','Message successfully received.');
INSERT INTO `config` (`key`,`value`) VALUES ('nextel/v1/backend/notification/error/message','Could not receive message. Internal Server Error.');
INSERT INTO `config` (`key`,`value`) VALUES ('nextel/v1/27118/service-id','1');
INSERT INTO `config` (`key`,`value`) VALUES ('nextel/v1/27115/user','fsvas_nx_protecao');
INSERT INTO `config` (`key`,`value`) VALUES ('nextel/v1/27115/password','@d:=pbJK');
INSERT INTO `config` (`key`,`value`) VALUES ('nextel/v1/27115/service-id','2');
INSERT INTO `config` (`key`, `value`) VALUES ('nextel/v1/cancellation/notification/type', '5');
INSERT INTO `config` (`key`, `value`) VALUES ('nextel/v1/cancellation/notification/calltype', '0');
INSERT INTO `config` (`key`, `value`) VALUES ('nextel/v1/cancellation/notification/callback', 'http://globalsdp-nextel.whitelabel.com.br/nextel/v1/notification/cancellation');
INSERT INTO `gateway`.`config` (`key`, `value`) VALUES ('nextel/v1/signature/notification/callback/backend', 'http://nextel-homol.whitelabel.com.br/mo/upd_cobrancas.php');
INSERT INTO `gateway`.`config` (`key`, `value`) VALUES ('nextel/v1/cancellation/notification/callback/backend', 'http://nextel-homol.whitelabel.com.br/mo/upd_cobrancas.php');
