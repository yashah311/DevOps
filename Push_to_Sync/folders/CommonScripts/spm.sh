#!/bin/bash
export FPATH=/opt/oracle/teams/TA/folders/SOAP_Scripts
export PROPS_FILE=/opt/oracle/fmw-platform/config/properties/domain.properties

function get_property() {
  value=$(echo $(cat ${PROPS_FILE} | grep "^$1=" | egrep -o "=.+"))
  echo ${value:1}
}

echo "INFO: Reading the base properties"
export EHOST1=$(get_property ENVHOST1)
export EHOST2=$(get_property ENVHOST2)

cd ${FPATH}
grep -lr 'ENVHOST1' . | xargs sed -i -e "s#ENVHOST1#$EHOST1#gI"
grep -lr 'ENVHOST2' . | xargs sed -i -e "s#ENVHOST2#$EHOST2#gI"

echo "#######SOA SPM#########"
cd ${FPATH}/SOA && ./soa_spm.sh

echo "#######AIA SPM########"
cd ${FPATH}/AIA && ./aia_spm.sh

echo "######SOA ZD SPM##########"
cd ${FPATH}/SOA_ZD && ./spm_zd.sh

