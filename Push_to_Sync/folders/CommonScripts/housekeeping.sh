#!/bin/bash
export DOMAIN_HOME=/opt/oracle/domains
export MS_COUNT=2

# Defining the server prefixes
function server_prefix_logic {
case $DOMAIN_NAME in
        "o2c-domain") SERVER_PREFIX=soa
        ;;
        "aabc-domain") SERVER_PREFIX=soa
        ;;
        "osb-domain") SERVER_PREFIX=osb
        ;;
        "odi-domain") SERVER_PREFIX=odi
        ;;
        "cod-domain") SERVER_PREFIX=odi
        ;;
esac
}

for DOMAIN_NAME in o2c-domain aabc-domain osb-domain odi-domain cod-domain
        do
                cd $DOMAIN_HOME/$DOMAIN_NAME/$DOMAIN_NAME/servers/AdminServer/logs
                rm -rf *.out0*
                rm -rf *.log0*
                rm -rf *diagnostic-*
                rm -rf *out_*
                for (( c=1; c<=$MS_COUNT; c++ ))
                do
                        server_prefix_logic
                        cd $DOMAIN_HOME/$DOMAIN_NAME/$DOMAIN_NAME/servers/${SERVER_PREFIX}_server${c}/logs
                        rm -rf *.out0*
                        rm -rf *.log0*
                        rm -rf *diagnostic-*
                        rm -rf *out_*
                done
                echo "Logs cleared for $DOMAIN_NAME"
        done
        cd

for DOMAIN_NAME in o2c-domain aabc-domain osb-domain odi-domain cod-domain; do mkdir -p $DOMAIN_HOME/$DOMAIN_NAME/shared/jfrlogs && find $DOMAIN_HOME/$DOMAIN_NAME/shared/jfrlogs -type f -mtime +2 -exec rm -f {} + ; done
