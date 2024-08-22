#!/bin/bash
# Author: Yash Shah <shah.yash@accenture.com>
# This script is used to monitor various FMW components of environment and share detailed report on email
# Usage: Run the script ./master_monitor
hdir=$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )
cd ${hdir}

# Defining variables
export Stream="FMW+ODI"
#export Server_Status="GREEN"
#export FS_Status="YELLOW"
#export Issues_Highlighted="NA"
#export FS_UTIL="NO"
export Server_issues="NO"
export Logging_Level="As per PAT format"
export Queue_backlog="NA"
export timeStamp=`date +"%d%b%Y-%H%M%S"`
export start=$(date +%s.%N)
export NAS_MOUNT="/opt/oracle"
export GPH_MOUNT="/opt/docker"
export SCRIPT_HOME="${NAS_MOUNT}/teams/TA/monitoring_scripts"

echo "FMW12c monitoring script is triggered at ${timeStamp}"
rm ../outputs/* ../reports/* 

echo "# All Domains HC"
/usr/local/bin/platformw runtime status --env -q  > ../outputs/allHC.out
cat ../outputs/allHC.out  | { cat ; echo ; } | ./tabulate.sh -d " " -h "ENVIRONMENT HC" > ../reports/00_allHC_output.html
SS=$(expr $(awk '(NR>1) {print $4}' ../outputs/allHC.out | grep -v HEALTH_OK | wc -l))
if [ ${SS} -eq  0 ] ; then Server_Status="GREEN" ; else Server_Status="RED" ; fi

echo "# FS utilization"
NAS=$(df -kh | grep ${NAS_MOUNT} | awk '{print $5}'  | cut -d "%" -f 1)
GPH=$(df -kh | grep ${GPH_MOUNT} | awk '{print $5}'  | cut -d "%" -f 1)
echo "Mount STATUS" > ../outputs/allFS.out
if [ ${NAS} -le  80 ] ; then echo "${NAS_MOUNT} GREEN" && FS_UTIL="NO" ; elif [ ${NAS} -le  90 ] ; then echo "${NAS_MOUNT} YELLOW" && FS_UTIL="YES" ; else echo "${NAS_MOUNT} RED" && FS_UTIL="YES" ; fi >> ../outputs/allFS.out
if [ ${GPH} -le  80 ] ; then echo "${GPH_MOUNT} GREEN" && FS_UTIL="NO" ; elif [ ${GPH} -le  90 ] ; then echo "${GPH_MOUNT} YELLOW" && FS_UTIL="YES" ; else echo "${GPH_MOUNT} RED" && FS_UTIL="YES" ; fi >> ../outputs/allFS.out
cat ../outputs/allFS.out  | { cat ; echo ; } | ./tabulate.sh -d " " -h "FS UTILIZATION" > ../reports/01_allFS_output.html
if [ ${NAS} -le  80 ] && [ ${GPH} -le  80 ] ; then FS_Status="GREEN" ; elif [ ${NAS} -le  90 ] && [ ${GPH} -le  90 ] ; then FS_Status="YELLOW" ; else FS_Status="RED" ; fi

echo "# SPM stats"
for DOMAIN_NAME in aabc-domain o2c-domain ; do /usr/local/bin/platformw component spm status ${DOMAIN_NAME} -q >> ../outputs/allspm.out ;done
cat ../outputs/allspm.out  | { cat ; echo ; } | ./tabulate.sh -d " " -h "SPM STATS - AABC & O2C DOMAIN" > ../reports/02_allspm_output.html

echo "# JCA stats"
echo "Protocol  N1 N2 Local_Address Foreign_Address State PID" > ../outputs/alljca.out
for DOMAIN_NAME in aabc-domain ; do for SERVER_NAME in soa_server1 soa_server2 ; do /usr/local/bin/platformw runtime shell ${DOMAIN_NAME} -s ${SERVER_NAME} --exec "/u01/oracle/domains/shared/scripts/view_JCA_connections.sh" -q ;done ;done >> ../outputs/alljca.out
for DOMAIN_NAME in o2c-domain ; do for SERVER_NAME in soa_server1 soa_server2 ; do /usr/local/bin/platformw runtime shell ${DOMAIN_NAME} -s ${SERVER_NAME} --exec "/u01/oracle/domains/shared/scripts/view_JCA_connections.sh" -q ;done ;done >> ../outputs/alljca.out
#for DOMAIN_NAME in aabc-domain ; do for SERVER_NAME in soa_server1 soa_server2 soa_server3 soa_server4 ; do /usr/local/bin/platformw runtime shell ${DOMAIN_NAME} -s ${SERVER_NAME} --exec "/u01/oracle/domains/shared/scripts/view_JCA_connections.sh" -q ;done ;done >> ../outputs/alljca.out
#for DOMAIN_NAME in o2c-domain ; do for SERVER_NAME in soa_server1 soa_server2 soa_server3 ; do /usr/local/bin/platformw runtime shell ${DOMAIN_NAME} -s ${SERVER_NAME} --exec "/u01/oracle/domains/shared/scripts/view_JCA_connections.sh" -q ;done ;done >> ../outputs/alljca.out
jca_count=$(expr $(cat ../outputs/alljca.out | wc -l) - 1)
#awk '{sum+=$1} END {print sum}' ../outputs/alljca.out > ../outputs/alljca_count.out ; cat ../outputs/alljca_count.out
cat ../outputs/alljca.out  | { cat ; echo ; } | ./tabulate.sh -d " " -h "JCA STATS - Count=${jca_count}" > ../reports/03_alljca_output.html

echo "# Docker Images stats"
/usr/local/bin/platformw image list --env -q  > ../outputs/allimage.out
awk '{print $1, $2, $3, $4}' ../outputs/allimage.out > ../outputs/allimages.out
cat ../outputs/allimages.out  | { cat ; echo ; } | ./tabulate.sh -d " " -h "DOCKER IMAGES LIST" > ../reports/04_allimages_output.html

echo "# Docker container stats"
/usr/local/bin/platformw container list --env -q  > ../outputs/allcontainer.out
cat ../outputs/allcontainer.out  | { cat ; echo ; } | ./tabulate.sh -d " " -h "DOCKER CONTAINER LIST" > ../reports/05_allcontainer_output.html

echo "# Data source HC"
for DOMAIN_NAME in aabc-domain osb-domain  o2c-domain odi-domain cod-domain; do /usr/local/bin/platformw runtime wlst ${DOMAIN_NAME}  --exec "/u01/oracle/domains/shared/scripts/test_wls_datasources.py" -q  > ../outputs/tmp.out ; awk 'NR>12 {print}' ../outputs/tmp.out >> ../outputs/allDS_final.out ; done
cat ../outputs/allDS_final.out  | { cat ; echo ; } | ./tabulate.sh -d " " -h "DATASOURCES HC" > ../reports/06_allDS_output.html
DS=$(expr $(awk '(NR>1) {print $5}' ../outputs/allDS_final.out | grep -v TEST | grep -v OK | awk NF | wc -l))
if [ ${DS} -eq  0 ] ; then Issues_Highlighted="NA" ; else Issues_Highlighted="CHECK DATA SOURCES" ; fi

echo "# Preparing CSV report"
echo -e "Stream,Server Status,FS Status,Issues Highlighted,FS Utilisation more that 80%,Servers or Component issues,Logging Level,Queue-backlog\n${Stream},${Server_Status},${FS_Status},${Issues_Highlighted},${FS_UTIL},${Server_issues},${Logging_Level},${Queue_backlog}" > ../reports/FMW12c_report.csv

echo "# Winding up"
end=$(date +%s.%N)
runtime=$(python -c "print(${end} - ${start})")
echo "FMW12c_monitoring_v1.0" > ../outputs/log.out
cat ../outputs/log.out  | { cat ; echo ; } | ./tabulate.sh -d " " -h "FMW12c monitoring report generated in $runtime seconds" > ../reports/07_logout.html

echo "# Final compilation of reports"
finalreport="../archive/FMW_Monitoring_Report_${timeStamp}.html"
finalcsvreport="../archive/FMW_Monitoring_Report_${timeStamp}.csv"
cat ../reports/*.html >> ../reports/FMW12c_report.html ; cp ../reports/FMW12c_report.html $finalreport ; cp ../reports/FMW12c_report.csv $finalcsvreport

echo "# Share report in message body via email"
cat <<'EOF' - ../reports/FMW12c_report.html | /usr/sbin/sendmail -t
To: newco.ta.fmwaia@accenture.com
Subject: FMW12c monitoring report
Content-Type: text/html
EOF

#echo "# Share report as attachment body via email"
#mutt -s "FMW12c monitoring report on $timeStamp"  -a ${SCRIPT_HOME}/reports/FMW12c_report.html -- newco.ta.fmwaia@accenture.com
#echo -e "Please find attached report" |mailx -s  "FMW12c monitoring report on $timeStamp" -a ${SCRIPT_HOME}/reports/FMW12c_report.html -a ${SCRIPT_HOME}/reports/FMW12c_report.csv -r fmw12c@vfnewco.in -c mukul.c.verma@accenture.com shah.yash@accenture.com,newco.ta@accenture.com <  ${SCRIPT_HOME}/reports/FMW12c_report.csv

echo "FMW12c monitoring report generated in $runtime seconds. Please check email"
