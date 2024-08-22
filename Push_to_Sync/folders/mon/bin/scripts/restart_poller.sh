# Author: Yash Shah <shah.yash@accenture.com>
# This script is meant to restart all Pollers inside osb Admin container



#Stop all Pollers
pgrep -f Poller | xargs kill -9



#Start all Pollers
cd /u01/oracle/domains/osb-domain/NewCoCustomApps
nohup ./SendFulFilmentOrder_poller.sh &
nohup ./SurePayBundleRenewalNotification_poller.sh &
nohup ./SurePayModifyAssetNotification_BundleExhaustion_poller.sh &
nohup ./SurePayModifyAssetNotification_BundleExpiry_poller.sh &
