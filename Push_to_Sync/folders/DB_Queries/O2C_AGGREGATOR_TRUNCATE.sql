show USER;
select count(*) from aia_aggregated_entities;
truncate table aia_aggregated_entities;
select count(*) from aia_aggregated_entities;
exit;
