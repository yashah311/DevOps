show USER;
select count(*) from mediator_resequencer_message;
select count(*) from mediator_group_status;
delete from mediator_resequencer_message;
begin
                   for cur in (select fk.owner, fk.constraint_name , fk.table_name
                       from all_constraints fk, all_constraints pk
                       where fk.CONSTRAINT_TYPE = 'R' and
                       pk.owner = 'O2C_SOAINFRA' and
                       fk.R_CONSTRAINT_NAME = pk.CONSTRAINT_NAME and
                       pk.TABLE_NAME = 'MEDIATOR_GROUP_STATUS') loop
                       execute immediate 'ALTER TABLE '||cur.owner||'.'||cur.table_name||' MODIFY CONSTRAINT '||cur.constraint_name||' ENABLE';
                   end loop;
end;
/
Commit;
delete from mediator_group_status;
begin
                   for cur in (select fk.owner, fk.constraint_name , fk.table_name
                       from all_constraints fk, all_constraints pk
                       where fk.CONSTRAINT_TYPE = 'R' and
                       pk.owner = 'O2C_SOAINFRA' and
                       fk.R_CONSTRAINT_NAME = pk.CONSTRAINT_NAME and
                       pk.TABLE_NAME = 'MEDIATOR_GROUP_STATUS') loop
                       execute immediate 'ALTER TABLE '||cur.owner||'.'||cur.table_name||' MODIFY CONSTRAINT '||cur.constraint_name||' ENABLE';
                   end loop;
end;
/
Commit;
exit;
