echo "Starting the purge activity"
echo "Disk space before purging" && df -kh | grep /opt/oracle
for DOMAIN_NAME in o2c-domain aabc-domain osb-domain odi-domain cod-domain; do echo "Purging JFR logs in $DOMAIN_NAME" && find /opt/oracle/domains/$DOMAIN_NAME/shared/jfrlogs -type f -mtime +2 -exec rm -f {} + ;  done
for DOMAIN_NAME in o2c-domain aabc-domain osb-domain odi-domain cod-domain; do echo "Purging GC logs in $DOMAIN_NAME" && find /opt/oracle/domains/$DOMAIN_NAME/shared/gclogs -type f -mtime +2 -exec rm -f {} + ; done
echo "Disk space after purging" && df -kh | grep /opt/oracle
echo "Completed the purge activity"
