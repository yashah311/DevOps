#!/bin/sh
# Author: Yash Shah <shah.yash@accenture.com>
# Check usage for this helper operations script to view or add bulk data in coherence
function usage() {
echo """
ERROR: Unknown argument passed
Run ./coherence_ops.sh view --> To view MSISDN present in coherence
Run ./coherence_ops.sh add  --> To add both account & msisdn in coherence
Run ./coherence_ops.sh view_size --> To view size of account, attribute and asset present in coherence
Run ./coherence_ops.sh compare <second host> --> To compare coherence configuration between 2 hosts
Run ./coherence_ops.sh HC --> To check cluster control status for required hosts(source_ips.txt)
"""
}

# Defining global variables
export RIG_PATH=/opt/rigcache/application/rig-authorisation
export ADD_PATH=/home/rigcache/test-client/bin

export VIEW_PATH=${RIG_PATH}/bin
export OPS_PATH=${RIG_PATH}/ops
export CONF_PATH=${RIG_PATH}/conf

NOW=$(date +%d_%m_%Y_%H_%M_%S)

# Defining custom variables
export SOURCE_FILE=${OPS_PATH}/test_data.txt
export HOST2="${2}"
export OPS_CMD_PATH=${OPS_PATH}/cmd
export OPS_LOGS_PATH=${OPS_PATH}/logs
export COMPARE_PATH=${OPS_PATH}/cmp
export VIEW_COMPARE_LOG_FILE=${OPS_LOGS_PATH}/report_diff_${NOW}.out
export VIEW_CMD_FILE=${OPS_CMD_PATH}/view_msisdn_${NOW}.cmd
export VIEW_LOG_FILE=${OPS_LOGS_PATH}/view_msisdn_${NOW}.out
export VIEW_SIZE_LOG_FILE=${OPS_LOGS_PATH}/view_size_${NOW}.out
export ADD_ACCOUNT_CMD_FILE=${OPS_CMD_PATH}/add_account_${NOW}.cmd
export ADD_ACCOUNT_LOG_FILE=${OPS_LOGS_PATH}/add_account_${NOW}.out
export ADD_MSISDN_CMD_FILE=${OPS_CMD_PATH}/add_msisdn_${NOW}.cmd
export ADD_MSISDN_LOG_FILE=${OPS_LOGS_PATH}/add_msisdn_${NOW}.out
export HC_LOG_FILE=${OPS_LOGS_PATH}/HC_${NOW}.out

# Checking pre-requisites
if [ ! -d ${OPS_PATH} ]; then
        mkdir -p ${OPS_PATH}
fi

if [ ! -d ${OPS_CMD_PATH} ]; then
        mkdir -p ${OPS_CMD_PATH}
fi

if [ ! -d ${OPS_LOGS_PATH} ]; then
        mkdir -p ${OPS_LOGS_PATH}
fi

if [ ! -d ${COMPARE_PATH} ]; then
        mkdir -p ${COMPARE_PATH}
fi

if [ ! -f ${SOURCE_FILE} ]; then
  echo "ERROR: ${SOURCE_FILE} is not present!"
  exit 1
fi

case $1 in
        "view") cd ${VIEW_PATH} && awk '{print $1}' ${SOURCE_FILE} |  sed 's#.*#yes | ./rigauth-operations.sh get msisdn &#' > ${VIEW_CMD_FILE} && sh ${VIEW_CMD_FILE} | grep JAVA > ${VIEW_LOG_FILE} && echo "Check ${VIEW_LOG_FILE} logs for view report"
        ;;
        "add") cd ${ADD_PATH} && awk '{print "yes | ./create-account.sh "$2" VFRED VFRED"}' ${SOURCE_FILE} > ${ADD_ACCOUNT_CMD_FILE} && sh ${ADD_ACCOUNT_CMD_FILE} | grep JAVA > ${ADD_ACCOUNT_LOG_FILE} && echo "Check ${ADD_ACCOUNT_LOG_FILE} logs for add account report" && awk '{print "yes | ./create-asset.sh "$1" MSISDN "$2" "$2" "$2 " null null"}' ${SOURCE_FILE} > ${ADD_MSISDN_CMD_FILE} && sh ${ADD_MSISDN_CMD_FILE} | grep JAVA > ${ADD_MSISDN_LOG_FILE}  && echo "Check ${ADD_MSISDN_LOG_FILE} logs for add msisdn report"
        ;;
        "view_size") cd ${VIEW_PATH} &&  for type in account attribute asset ; do yes | ./rigauth-operations.sh size ${type} | grep JAVA >> ${VIEW_SIZE_LOG_FILE} ; done && echo "Check ${VIEW_SIZE_LOG_FILE} logs for view size report"
        ;;
        "compare") rm -rf ${COMPARE_PATH}/* && cd ${COMPARE_PATH} && cp -r ${CONF_PATH} . && mv conf folder1 && scp -r rigcache@${HOST2}:${CONF_PATH}  . && mv conf folder2 && echo "Please check ${VIEW_COMPARE_LOG_FILE} for comparison report" && diff -r folder* > ${VIEW_COMPARE_LOG_FILE}
        ;;
        "HC") echo "==================================For Java host $(hostname)==================================" >> ${HC_LOG_FILE} ; cd ${RIG_PATH}/bin && yes | ./rigauth-cluster-control.sh status | grep Java >> ${HC_LOG_FILE} && cd ${OPS_PATH} & for i in `cat source_ips.txt`; do ssh $i " echo '==================================For Java host $(hostname)================================== '; cd ${RIG_PATH}/bin && yes | ./rigauth-cluster-control.sh status " ; done | grep Java >> ${HC_LOG_FILE} && cat ${HC_LOG_FILE} && echo "Check report --> ${HC_LOG_FILE} "
        ;;
        *) usage
        ;;
esac
