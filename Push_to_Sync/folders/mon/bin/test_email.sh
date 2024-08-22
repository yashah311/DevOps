#!/bin/bash
# Author: Yash Shah <shah.yash@accenture.com>
# This script is just to test mailx
export timeStamp=`date +"%d%b%Y-%H%M%S"`
export NAS_MOUNT="/opt/oracle"
export SCRIPT_HOME="${NAS_MOUNT}/teams/TA/monitoring_scripts"
echo -e "Ping"  |mailx -s  "Hello from $(hostname)" shah.yash@accenture.com
#echo -e "Please find attached report" |mailx -s  "FMW12c monitoring report on $timeStamp" -a ${SCRIPT_HOME}/reports/FMW12c_report.html -a ${SCRIPT_HOME}/reports/FMW12c_report.csv shah.yash@accenture.com <  ${SCRIPT_HOME}/reports/FMW12c_report.csv


