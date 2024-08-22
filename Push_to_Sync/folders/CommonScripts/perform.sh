#!/bin/bash
# Author: Yash Shah (shah.yash@accenture.com)
#This script dynamically performs custom actions on FMW domains

display_usage() {
echo "./perform.sh start/stop/restart/clean_restart/clean_dat_restart o2c/aabc/osb/odi/cod/all_wls/all_ohs/all"
}

ACTION=$1

function start_command {
case $2 in
all)
for DOMAIN_NAME in ohs-domain-o2c ohs-domain-aabc ohs-domain-osb ohs-domain-odi ohs-domain-cod o2c-domain aabc-domain osb-domain odi-domain cod-domain
do nohup platformw $1 domain $DOMAIN_NAME --no-gov & 
done
;;
all_ohs)
for DOMAIN_NAME in ohs-domain-o2c ohs-domain-aabc ohs-domain-osb ohs-domain-odi ohs-domain-cod
do nohup platformw $1 domain $DOMAIN_NAME --no-gov & 
done
;;
all_wls)
for DOMAIN_NAME in o2c-domain aabc-domain osb-domain odi-domain cod-domain
do nohup platformw $1 domain $DOMAIN_NAME --no-gov & 
done
;;
o2c) platformw $1 domain o2c-domain --no-gov 
;;
osb) platformw $1 domain osb-domain --no-gov 
;;
aabc) platformw $1 domain aabc-domain --no-gov 
;;
odi) platformw $1 domain odi-domain --no-gov 
;;
cod) platformw $1 domain cod-domain --no-gov 
;;
*) echo "Invalid option";
display_usage;
;;
esac
}

function stop_command {
case $2 in
all)
for DOMAIN_NAME in ohs-domain-o2c ohs-domain-aabc ohs-domain-osb ohs-domain-odi ohs-domain-cod o2c-domain aabc-domain osb-domain odi-domain cod-domain
do nohup platformw $1 domain $DOMAIN_NAME --no-gov --f & 
done
;;
all_ohs)
for DOMAIN_NAME in ohs-domain-o2c ohs-domain-aabc ohs-domain-osb ohs-domain-odi ohs-domain-cod
do nohup platformw $1 domain $DOMAIN_NAME --no-gov --f & 
done
;;
all_wls)
for DOMAIN_NAME in o2c-domain aabc-domain osb-domain odi-domain cod-domain
do nohup platformw $1 domain $DOMAIN_NAME --no-gov --f & 
done
;;
o2c) platformw $1 domain o2c-domain --no-gov --f
;;
osb) platformw $1 domain osb-domain --no-gov --f
;;
aabc) platformw $1 domain aabc-domain --no-gov --f
;;
odi) platformw $1 domain odi-domain --no-gov --f
;;
cod) platformw $1 domain cod-domain --no-gov --f
;;
*) echo "Invalid option";
display_usage;
;;
esac
}

export DOMAIN_HOME='/opt/oracle/domains'
export MS_COUNT=2
#DOMAIN_HOME='/opt/SP/oracle/domains'
#MS_COUNT=5

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

function clean_up {
	for DOMAIN_NAME in $1-domain 
	do
		cd $DOMAIN_HOME/$DOMAIN_NAME/$DOMAIN_NAME/servers/AdminServer
		mv tmp tmp_"$(date +"%m-%d-%y-%H-%M-%S")"
		mv cache cache_"$(date +"%m-%d-%y-%H-%M-%S")"
		for (( c=1; c<=$MS_COUNT; c++ ))
		do
			server_prefix_logic
			cd $DOMAIN_HOME/$DOMAIN_NAME/$DOMAIN_NAME/servers/${SERVER_PREFIX}_server${c}
			mv tmp tmp_"$(date +"%m-%d-%y-%H-%M-%S")"
			mv cache cache_"$(date +"%m-%d-%y-%H-%M-%S")"
			mv stage stage_"$(date +"%m-%d-%y-%H-%M-%S")"
		done
		echo "Clean-up done for $DOMAIN_NAME"
	done
	cd
}

function clean_dat {
	for DOMAIN_NAME in $1-domain 
	do
		cd /opt/local-data/$DOMAIN_NAME
		echo "Moving below dat files to dump location /opt/oracle/teams/TA/common"
		find . -name *.DAT -type f
		find . -name *.DAT -type f | xargs rm -f
		echo "DAT files are cleaned for $DOMAIN_NAME"
	done
	cd
}

function clean_command {
platformw stop domain $1-domain --f
#platformw start admin $1-domain --clean
#platformw start nm $1-domain
#platformw start servers $1-domain --clean
clean_up $1
platformw start domain $1-domain
}

function clean_dat_command {
platformw stop domain $1-domain --f
#platformw start admin $1-domain --clean
#platformw start nm $1-domain
#platformw start servers $1-domain --clean
clean_up $1
clean_dat $1
ssh soa02 "clean_dat $1"
platformw start domain $1-domain
}

case $ACTION in
start) start_command start $2
;;
stop) stop_command stop $2
;;
restart) stop_command stop $2
start_command start $2
;;
clean_restart) clean_command $2
;;
clean_dat_restart) clean_dat_command $2
;;
*) echo "Invalid option!"
display_usage
;;
esac
