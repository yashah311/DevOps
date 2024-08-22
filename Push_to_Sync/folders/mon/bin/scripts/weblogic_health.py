import sys
import re
import os
from java.util import Date
from java.text import SimpleDateFormat
print 'Starting JMX Data Extraction'
outputFileDir = ''

print 'Working till here...'
applicationName = ''
try:
   applicationName = 'FMW'
except KeyError:
   print "Please set the environment variable ApplicationName"
   sys.exit(1)

logFileName = os.path.join(outputFileDir, "wls_jmx_minute.log")
def deleteContent(logFile):
    logFile.seek(0)
    logFile.truncate()
def writeServerData(dataStr, stream):
        currTime=SimpleDateFormat("MMM dd, yyyy hh:mm:ss a zzz").format(Date())
        logStr = "timestamp=%s|ApplicationName=%s|Stream=%s|%s\n" % ( currTime, applicationName, stream, dataStr )
	print(logStr)
try:

	#connect('OSB_ADMIN','OSB_ADMIN','t3://uk5078yr:7301')
       print("connecting...")
       #connect(sys.argv[2],sys.argv[3],sys.argv[1])
	#connect('weblogic','Welcome21!','t3://uk5055yr:7301')
       connect('weblogic','Welcome_91','t3://cpp2-fmw12c-01:7301')

except Exception, e:
	print('Could not connect due to ' + str(e))
l = pwd()
print l

# Author: Yash Shah (shah.yash@accenture.com)

#print 'INFO: Connecting to WLS admin server'
#connect(args["user"],args["password"],'t3://' + args["admin_host"] + ':' + str(args["admin_port"]))
#connect('weblogic','Welcome_91','t3://cpp2-fmw12c-01:7301')


domainRuntime = domainRuntime()
domain=domainRuntime.getName()
cd('ServerRuntimes')
servers = domainRuntimeService.getServerRuntimes()
if (len(servers) > 0):
        for server in servers:
                servername=server.getName()
                cd ('/ServerRuntimes/' + servername )
                server_health_state = str(re.findall(r'State:\w+',str(cmo.getHealthState()))).split(':')[1].replace('\']','')
                serverDataStr = "domain=%s|server=%s|server_state=%s|server_health=%s|server_health_state=%s|server_host=%s" % ( domain, servername, str(cmo.getState()), str(cmo.getHealthState()), server_health_state, str(cmo.getListenAddress()) )
                writeServerData(serverDataStr, "Health")
                server_host = cmo.getListenAddress()
                cd ('/ServerRuntimes/' + servername + '/JVMRuntime/'  + servername)
                jvmDataStr = "domain=%s|server=%s|heap_size_current=%s|server_host=%s" % ( domain, servername, str(cmo.getHeapSizeCurrent()),server_host)
                jvmDataStr = jvmDataStr + "|heap_free_current=%s" % ( str(cmo.getHeapFreeCurrent()) )
                jvmDataStr = jvmDataStr + "|heap_free_percent=%s" % ( str(cmo.getHeapFreePercent()) )
                writeServerData(jvmDataStr, "JVMRuntime")

                cd ('/ServerRuntimes/' + servername + '/ThreadPoolRuntime/ThreadPoolRuntime')
                threadPoolDataStr = "domain=%s|server=%s|throughput=%s|server_host=%s" % ( domain, servername, str(cmo.getThroughput()),server_host )
                threadPoolDataStr = threadPoolDataStr + "|total_threads=%s" % ( str(cmo.getExecuteThreadTotalCount()) )
                threadPoolDataStr = threadPoolDataStr + "|completed_reqs=%s" % ( str(cmo.getCompletedRequestCount()) )
                threadPoolDataStr = threadPoolDataStr + "|hogging_threads=%s" % ( str(cmo.getHoggingThreadCount()) )
                threadPoolDataStr = threadPoolDataStr + "|pending_reqs=%s" % ( str(cmo.getPendingUserRequestCount()) )
                writeServerData(threadPoolDataStr, "ThreadPool")

                jmsRuntime = server.getJMSRuntime();
                jmsServers = jmsRuntime.getJMSServers();

                for jmsServer in jmsServers:
                        jmsServerDataStr = "domain=%s|server=%s|jms_server=%s|server_host=%s" % ( domain, servername, jmsServer.getName(),server_host )
                        jmsServerDataStr = jmsServerDataStr + "|jms_current_messages_count=%s|jms_pending_messages_count=%s" % ( str(jmsServer.getMessagesCurrentCount()), str(jmsServer.getMessagesPendingCount()) )
                        jmsServerDataStr = jmsServerDataStr + "|jms_current_connection_count=%s" % ( str(jmsRuntime.getConnectionsCurrentCount()) )
                        writeServerData(jmsServerDataStr, "jmsServers")

                jdbcRuntime = server.getJDBCServiceRuntime();
                datasources = jdbcRuntime.getJDBCDataSourceRuntimeMBeans();
                for datasource in datasources:
                        jdbcDataStr = "domain=%s|server=%s|server_host=%s" % ( domain, servername,server_host )
                        jdbcDataStr = jdbcDataStr + "|jdbc_datasource_name=%s|jdbc_active_connection_count=%s" % ( datasource.getName(), repr(datasource.getActiveConnectionsCurrentCount()) )
                        jdbcDataStr = jdbcDataStr + "|jdbc_datasource_status=%s" % ( str(datasource.getState()) )
                        jdbcDataStr = jdbcDataStr + "|jdbc_available_connections=%s" % ( repr(datasource.getNumAvailable()) )
                        writeServerData(jdbcDataStr, "datasource")

                userLockRuntime = server.getServerSecurityRuntime().getDefaultRealmRuntime().getUserLockoutManagerRuntime();
                userLockStr = "domain=%s|server=%s|server_host=%s" % ( domain, servername,server_host )
                writeServerData(userLockStr, "userLock")

cd('/AppRuntimeStateRuntime/AppRuntimeStateRuntime')
appList = cmo.getApplicationIds()
for app in appList:
        appStateStr = "domain=%s|server=%s|app=%s|app_state=%s" % ( domain, server.getName(), app , cmo.getIntendedState(app) )
        writeServerData( appStateStr, "AppRuntimeState" );

