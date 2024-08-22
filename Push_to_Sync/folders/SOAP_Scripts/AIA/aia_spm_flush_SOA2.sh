#!/bin/sh

#Print SPM stats
echo "SPM STATS Before SPM Flush `date`"
#./check_all_status.sh

# Load the property file
/opt/oracle/teams/TA/folders/SOAP_Scripts/AIA/aia_config.properties

# Global varibale used for getProperty function
CONFIG_FILE_NAME=/home/oracle/folders/SOAP_Scripts/AIA/aia_config.properties
SERVER_HOST_PORT=8102

if [[ ($# == 0) || ($# > 1) ]]; then
  echo "Wrong number of arguments supplied. Need to provide one argument with any of one value(ALL,"$AIA_SERVER_LIST")"
  exit
fi

DATE=$(date +%Y%m%d%H%M%S)
LOG_FILE_NAME=./logs/AIA_SPM_FLUSH_LOG_$DATE

# Function to fetch property value from name
getProperty()
 {
        #Reset the value first
        SERVER_HOST_PORT=""
        #Set the value for respective server
        SERVER_HOST_PORT=`cat ${CONFIG_FILE_NAME} | grep ${1}= | cut -d'=' -f2`
  }

# Function to terminate SPM 
terminateSPM()
{
          getProperty $1
#         url="http://$SERVER_HOST_PORT$SPM_SCA_URL"
#	  url="http://198.18.76.155:8101/soa-infra/services/default/AIASessionPoolManager/client"
         url="http://ENVHOST2:8102/soa-infra/services/default/AIASessionPoolManager/client"
          echo "Terminate SPM for server : " $1 " using endpoint : " $url " with soap action : " $SOAP_ACTION_TERMINATE >> $LOG_FILE_NAME
          request_xml=`cat request_terminate.xml`
          echo -e "Request xml : " $request_xml '\n' >> $LOG_FILE_NAME
          > response.xml
          curl -X POST -H "Content-Type: text/xml" -H "SOAPAction:$SOAP_ACTION_TERMINATE" -s -w "OPERATION:$SOAP_ACTION_TERMINATE|HTTPSTATUS:%{http_code}" --data @request_terminate.xml -o response.xml  -i $url
          echo -e '\n'
          response_xml=`cat response.xml`
          echo "Response xml : " $response_xml >> $LOG_FILE_NAME
          echo -e "Terminated SPM for server : " $1 '\n' >> $LOG_FILE_NAME
}

# Function to start SPM
startSPM()
{
          getProperty $1
#          url="http://$SERVER_HOST_PORT$SPM_SCA_URL"
#	  url="http://198.18.76.155:8101/soa-infra/services/default/AIASessionPoolManager/client"
         url="http://ENVHOST2:8102/soa-infra/services/default/AIASessionPoolManager/client"
          echo "Start SPM for server : " $1 " using endpoint : " $url " with soap action : " $SOAP_ACTION_START >> $LOG_FILE_NAME
          request_xml=`cat request_start.xml`
          echo -e "Request xml : " $request_xml '\n' >> $LOG_FILE_NAME
          > response.xml
          curl -X POST -H "Content-Type: text/xml" -H "SOAPAction:$SOAP_ACTION_START" -s -w "OPERATION:$SOAP_ACTION_START|HTTPSTATUS:%{http_code}" --data @request_start.xml -o response.xml  -i $url
          echo -e '\n'
          response_xml=`cat response.xml`
          echo "Response xml : " $response_xml >> $LOG_FILE_NAME
          echo -e "Started SPM for server : " $1 '\n' >> $LOG_FILE_NAME
}

# Function to get SPM
getSPM()
{
          getProperty $1
#         url="http://$SERVER_HOST_PORT$SPM_SCA_URL"
#	  url="http://198.18.76.155:8101/soa-infra/services/default/AIASessionPoolManager/client"
         url="http://ENVHOST2:8102/soa-infra/services/default/AIASessionPoolManager/client"
          echo "Get the token from server : " $1 " using endpoint : " $url " with soap action : " $SOAP_ACTION_GET >> $LOG_FILE_NAME
          request_xml=`cat request_get.xml`
          echo -e "Request xml : " $request_xml '\n' >> $LOG_FILE_NAME
          > response.xml
          curl -X POST -H "Content-Type: text/xml" -H "SOAPAction:$SOAP_ACTION_GET" -s -w "OPERATION:$SOAP_ACTION_GET|HTTPSTATUS:%{http_code}" --data @request_get.xml -o response.xml -i $url
          response_xml=`cat response.xml`
          echo "Response xml : " $response_xml >> $LOG_FILE_NAME
          echo -e "Get operation completed succesfully for server : " $1 '\n' >> $LOG_FILE_NAME
}


if [[  $# == 1  ]]; then
     input_length=`echo $1|wc -c`
     if [[  $1 == "ALL"  ]]; then
        echo "------------ SPM flush request for all servers ---------------" >> $LOG_FILE_NAME
        IFS=","
        for server in $AIA_SERVER_LIST
        do
          # Call the functions to flush
          echo -e '\n' "---------------" $server "-------------" 
          terminateSPM $server
          sleep 2
          startSPM $server
          sleep 2
          getSPM $server
          sleep 2
          #echo -e '\n' "-----------------------------------" 
         done
         echo "------------ SPM flushed for all servers -------------------------" >> $LOG_FILE_NAME
     elif [[ ($1 == *SOA*) && ($input_length > 4) ]]; then
        echo "------------ SPM flush request for server : " $1 "-------------------" >> $LOG_FILE_NAME
        # Call the functions to flush
          echo -e '\n' "---------------" $1 "-------------"
          terminateSPM $1
          sleep 2
          startSPM $1
          sleep 2
          getSPM $1
          sleep 2
         #echo -e '\n' "-----------------------------------"
        echo "------------- SPM flush completed -------------------------------" >> $LOG_FILE_NAME
     else 
        echo "Invalid option supplied. Kindly provide one of the valid option (ALL,"$AIA_SERVER_LIST")"
        exit
    fi
fi

#Print SPM stats post flush after 5 seconds
sleep 5
echo -e '\n'
echo "SPM STATS After SPM Flush `date`"
#./check_all_status.sh
