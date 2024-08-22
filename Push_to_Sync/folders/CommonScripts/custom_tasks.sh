#!/bin/sh
# Author: Yash Shah <shah.yash@accenture.com>
# This script is used to take back-up of custom configurations for all FMW domains of desired environments
# Usage: Run the script ./custom_tasks.sh and enter choice for environments

echo "For ST/SIT environments: Choose 1";echo "For GDC environments: Choose 2"
echo -n "Enter choice for environment: "
read env

# Setting up domain home variable for desired environment
if [[ $env -eq 1 ]]
then 
	DOMAIN_HOME='/opt/oracle/domains'
	MS_COUNT=2
else
    DOMAIN_HOME='/opt/SP/oracle/domains'
	MS_COUNT=5
fi

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

# Function for taking config backup 
function config_bkp {
	for DOMAIN_NAME in o2c-domain aabc-domain osb-domain odi-domain cod-domain 
	do
		cd $DOMAIN_HOME/$DOMAIN_NAME/$DOMAIN_NAME/config
		cp config.xml config.xml."$(date +"%m-%d-%y")"
		cp -r jdbc jdbc."$(date +"%m-%d-%y")"
		echo "Config back-up done for $DOMAIN_NAME"
		cd
	done
}

# Function for taking logs backup 
function logs_bkp {
	for DOMAIN_NAME in o2c-domain aabc-domain osb-domain odi-domain cod-domain 
	do
		cd $DOMAIN_HOME/$DOMAIN_NAME/$DOMAIN_NAME/servers/AdminServer
		cp -r logs logs."$(date +"%m-%d-%y")"
		for (( c=1; c<=$MS_COUNT; c++ ))
		do
			server_prefix_logic
			cd $DOMAIN_HOME/$DOMAIN_NAME/$DOMAIN_NAME/servers/${SERVER_PREFIX}_server${c}
			cp -r logs logs."$(date +"%m-%d-%y")"
		done
		echo "Logs back-up done for $DOMAIN_NAME"
	done
	cd
}

# Function for clear logs 
function clear_logs {
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
}

# Function for clean restart  
function clean_up {
	for DOMAIN_NAME in o2c-domain aabc-domain osb-domain odi-domain cod-domain 
	do
		cd $DOMAIN_HOME/$DOMAIN_NAME/$DOMAIN_NAME/servers/AdminServer
		mv tmp tmp_"$(date +"%m-%d-%y")"
		mv cache cache_"$(date +"%m-%d-%y")"
		for (( c=1; c<=$MS_COUNT; c++ ))
		do
			server_prefix_logic
			cd $DOMAIN_HOME/$DOMAIN_NAME/$DOMAIN_NAME/servers/${SERVER_PREFIX}_server${c}
			mv tmp tmp_"$(date +"%m-%d-%y")"
			mv cache cache_"$(date +"%m-%d-%y")"
			mv stage stage_"$(date +"%m-%d-%y")"
		done
		echo "Clean-up done for $DOMAIN_NAME"
	done
	cd
}

echo "Configuration backup: Press 1";echo "Logs backup: Press 2";echo "Clear logs: Press 3";echo "Clean up tmp,cache,stage: Press 4"
echo -n "Enter choice for function: " 
read func

# Calling functions
if [[ $func -eq 1 ]]
then 
	config_bkp
elif [[ $func -eq 2 ]]
then
	logs_bkp
elif [[ $func -eq 3 ]]
then
	clear_logs	
elif [[ $func -eq 4 ]]
then
	clean_up		
else
    echo "Call new functions here"
fi
