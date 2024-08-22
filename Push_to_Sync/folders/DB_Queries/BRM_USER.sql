SPOOL /u01/oracle/POIDS.out
SET LINES 100
SET HEADING OFF
SET COLSEP '  '
column poid_id0 format 999999999999
column poid_rev format 999999999999
column name format a20
select
  poid_id0,
  poid_rev,
  name
from
  config_t
where
  poid_type = '/config/business_profile'
  and name in (
    'MvnoWholesale', 'MvnoRetail', 'PostPaid',
    'PrePaid', 'RedHybrid'
  );
SPOOL OFF
exit