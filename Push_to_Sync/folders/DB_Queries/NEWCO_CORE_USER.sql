show USER;
ALTER TABLE INBOUND_MESSAGE
ADD MNP_TRANSACTION_NUMBER varchar2(10);
commit;

ALTER TABLE OUTBOUND_MESSAGE
MODIFY PORT_DATE DATE NOT NULL ENABLE;
COMMIT;

/* Adding constraint OUTBOUND_MESSAGE_PK with primary key "ACTION_CODE", "MSISDN", "TARGET", "PORT_DATE" */
ALTER TABLE OUTBOUND_MESSAGE
ADD CONSTRAINT "OUTBOUND_MESSAGE_PK" PRIMARY KEY ("ACTION_CODE", "MSISDN", "TARGET", "PORT_DATE");
COMMIT;

/* Dropping existing constraint OUTBOUND_MESSAGE_PK with primary key "ACTION_CODE", "MSISDN", "TARGET" */
ALTER TABLE OUTBOUND_MESSAGE
DROP CONSTRAINT "OUTBOUND_MESSAGE_PK";
COMMIT;

/* CCSX20.12 VFUKE-11413 INTFMW-490 InboundRepartionErrorhandling*/
ALTER TABLE OUTBOUND_MESSAGE
ADD ERROR_MESSAGE varchar(200);
COMMIT;



Insert into NEWCO_CORE.CONFIGURATION_STUB (INVENTORY_REF_ID,INTERFACE_NAME,OK_ID,KO_ID,FAULT_ID,ROOT_NAME,TARGET_ID,ID) values (1114,'SyncCachedCPA','719010101','936010101','719010301','UpdateAccountRequest',719010301,1223);
Insert into NEWCO_CORE.CONFIGURATION_STUB (INVENTORY_REF_ID,INTERFACE_NAME,OK_ID,KO_ID,FAULT_ID,ROOT_NAME,TARGET_ID,ID) values (1113,'SyncCachedCPA','719010103','936010103','719010303','DeleteAccountRequest',719010303,1222);
Insert into NEWCO_CORE.CONFIGURATION_STUB (INVENTORY_REF_ID,INTERFACE_NAME,OK_ID,KO_ID,FAULT_ID,ROOT_NAME,TARGET_ID,ID) values (1115,'SyncCachedCPA','719010102','936010102','719010302','ChangeAccountRequest',936010102,1224);
commit;


Insert into NEWCO_CORE.INTERNAL_STUB (ID,DESCRIPTION,FORWARDURI,MESSAGE,PATTERN,TESTID,DESTINATIONSYS) values (719010101,'default','UpdateAccountResponse','<CoherenceResponse>
<Result>
<code>0</code>
<description>OK</description>
</Result>
</CoherenceResponse>','SRR','OK','Coherence');
Insert into NEWCO_CORE.INTERNAL_STUB (ID,DESCRIPTION,FORWARDURI,MESSAGE,PATTERN,TESTID,DESTINATIONSYS) values (936010102,'default','ChangeAccountResponse','<CoherenceResponse>
<Result>
<code>0</code>
<description>OK with warning: Asset [AssetKey{assetId, productClass=MSISDN}] does not exist caused by: null with warning: Cannot create, asset [MSISDN:], already exists caused by: null </description>
</Result>
</CoherenceResponse>','SRR','Business Error','Coherence');
Insert into NEWCO_CORE.INTERNAL_STUB (ID,DESCRIPTION,FORWARDURI,MESSAGE,PATTERN,TESTID,DESTINATIONSYS) values (719010102,'default','ChangeAccountResponse','<CoherenceResponse>
<Result>
<code>0</code>
<description>OK</description>
</Result>
</CoherenceResponse>','SRR','OK','Coherence');
Insert into NEWCO_CORE.INTERNAL_STUB (ID,DESCRIPTION,FORWARDURI,MESSAGE,PATTERN,TESTID,DESTINATIONSYS) values (719010303,'default','DeleteAccountResponse','<CoherenceResponse>
<Result>
<code>2201</code>
<description>Asset Id is null or empty caused by: null </description>
</Result>
</CoherenceResponse>','SRR','FAULT','Coherence');
Insert into NEWCO_CORE.INTERNAL_STUB (ID,DESCRIPTION,FORWARDURI,MESSAGE,PATTERN,TESTID,DESTINATIONSYS) values (936010101,'default','UpdateAccountResponse','<CoherenceResponse>
<Result>
<code>0</code>
<description>OK with warning: Cannot create, asset [MSISDN:], already exists caused by: null with warning: Cannot create, asset [ICCID:VFRED], already exists caused by: null </description>
</Result>
</CoherenceResponse>','SRR','BusinessError','Coherence');
Insert into NEWCO_CORE.INTERNAL_STUB (ID,DESCRIPTION,FORWARDURI,MESSAGE,PATTERN,TESTID,DESTINATIONSYS) values (719010103,'default','DeleteAccountResponse','<CoherenceResponse>
<Result>
<code>0</code>
<description>OK</description>
</Result>
</CoherenceResponse>','SRR','OK','Coherence');
Insert into NEWCO_CORE.INTERNAL_STUB (ID,DESCRIPTION,FORWARDURI,MESSAGE,PATTERN,TESTID,DESTINATIONSYS) values (719010301,'default','UpdateAccountResponse','<CoherenceResponse>
<code>2010</code>
<description>
accountId is null or empty caused by: null
</description>
</CoherenceResponse>','SRR','Fault','Coherence');
Insert into NEWCO_CORE.INTERNAL_STUB (ID,DESCRIPTION,FORWARDURI,MESSAGE,PATTERN,TESTID,DESTINATIONSYS) values (719010302,'default','ChangeAccountResponse','<CoherenceResponse>
<Result>
<code>2036</code>
<description>Owner account is null or empty caused by: null </description>
</Result>
</CoherenceResponse>','SRR','Fault','Coherence');
commit;

