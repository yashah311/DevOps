
# Author: Yash Shah (shah.yash@accenture.com)

print 'INFO: Connecting to WLS admin server'
#connect(args["user"],args["password"],'t3://' + args["admin_host"] + ':' + str(args["admin_port"]))
connect('weblogic','Welcome_91','t3://cpp2-fmw12c-01:7301')
# =======================================================================================
# Utility function to fetch 
# =======================================================================================

def getwlsserverstatus(): 
  try: 
    servers=cmo.getServers()
    print "-------------------------------------------------------" 
    print "\t"+cmo.getName()+" domain status"                        
    print "-------------------------------------------------------"  
    for server in servers:
        state(server.getName(),server.getType())
    print "-------------------------------------------------------"  
  except:
    print ("Unexpected failure")

def fetchHC():
   servers=domainRuntimeService.getServerRuntimes()
   for server in servers: 
     healthStateVar=str(server.getHealthState());
     healthStateVarList=healthStateVar.split(",",3)[1].split(":",2)[1].split("_",2)
     overallHealthStateVarList=str(server.getOverallHealthState()).split(",",3)[1].split(":",2)[1].split("_",2);
     cd("/ServerRuntimes/"+server.getName()+"/ThreadPoolRuntime/ThreadPoolRuntime")
     serverName=server.getName();
     stateVar= server.getState();
     hoggingTC=cmo.getHoggingThreadCount()
     standByTC=cmo.getStandbyThreadCount()
     idleTC=cmo.getExecuteThreadIdleCount()
     pending=cmo.getPendingUserRequestCount()
     print serverName + " " + stateVar + " " + hoggingTC + " " + standByTC + " " + idleTC + " " + pending 

def getdatasourcesstatus():
 allServers=domainRuntimeService.getServerRuntimes();
 
 if (len(allServers) > 0):
 
  for tempServer in allServers:
 
    jdbcServiceRT = tempServer.getJDBCServiceRuntime();
 
    dataSources = jdbcServiceRT.getJDBCDataSourceRuntimeMBeans();
 
    if (len(dataSources) > 0):
 
        for dataSource in dataSources:
 
            print 'ActiveConnectionsAverageCount      '  ,  dataSource.getActiveConnectionsAverageCount()
            print 'ActiveConnectionsCurrentCount      '  ,  dataSource.getActiveConnectionsCurrentCount()
            print 'ActiveConnectionsHighCount         '  ,  dataSource.getActiveConnectionsHighCount()
            print 'ConnectionDelayTime                '  ,  dataSource.getConnectionDelayTime()
            print 'ConnectionsTotalCount              '  ,  dataSource.getConnectionsTotalCount()
            print 'CurrCapacity                       '  ,  dataSource.getCurrCapacity()
            print 'CurrCapacityHighCount              '  ,  dataSource.getCurrCapacityHighCount()
            print 'DeploymentState                    '  ,  dataSource.getDeploymentState()
            print 'FailedReserveRequestCount          '  ,  dataSource.getFailedReserveRequestCount()
            print 'FailuresToReconnectCount           '  ,  dataSource.getFailuresToReconnectCount()
            print 'HighestNumAvailable                '  ,  dataSource.getHighestNumAvailable()
            print 'HighestNumUnavailable              '  ,  dataSource.getHighestNumUnavailable()
            print 'LeakedConnectionCount              '  ,  dataSource.getLeakedConnectionCount()
            print 'ModuleId                           '  ,  dataSource.getModuleId()
            print 'Name                               '  ,  dataSource.getName()
            print 'NumAvailable                       '  ,  dataSource.getNumAvailable()
            print 'NumUnavailable                     '  ,  dataSource.getNumUnavailable()
            print 'Parent                             '  ,  dataSource.getParent()
            print 'PrepStmtCacheAccessCount           '  ,  dataSource.getPrepStmtCacheAccessCount()
            print 'PrepStmtCacheAddCount              '  ,  dataSource.getPrepStmtCacheAddCount()
            print 'PrepStmtCacheCurrentSize           '  ,  dataSource.getPrepStmtCacheCurrentSize()
            print 'PrepStmtCacheDeleteCount           '  ,  dataSource.getPrepStmtCacheDeleteCount()
            print 'PrepStmtCacheHitCount              '  ,  dataSource.getPrepStmtCacheHitCount()
            print 'PrepStmtCacheMissCount             '  ,  dataSource.getPrepStmtCacheMissCount()
            print 'Properties                         '  ,  dataSource.getProperties()
            print 'ReserveRequestCount                '  ,  dataSource.getReserveRequestCount()
            print 'State                              '  ,  dataSource.getState()
            print 'Type                               '  ,  dataSource.getType()
            print 'VersionJDBCDriver                  '  ,  dataSource.getVersionJDBCDriver()
            print 'WaitingForConnectionCurrentCount   '  ,  dataSource.getWaitingForConnectionCurrentCount()
            print 'WaitingForConnectionFailureTotal   '  ,  dataSource.getWaitingForConnectionFailureTotal()
            print 'WaitingForConnectionHighCount      '  ,  dataSource.getWaitingForConnectionHighCount()
            print 'WaitingForConnectionSuccessTotal   '  ,  dataSource.getWaitingForConnectionSuccessTotal()
            print 'WaitingForConnectionTotal          '  ,  dataSource.getWaitingForConnectionTotal()
            print 'WaitSecondsHighCount               '  ,  dataSource.getWaitSecondsHighCount()                                            
                                        

#main
if __name__ == 'main':
  # calling the function
  getwlsserverstatus()
  #getdatasourcesstatus()
  #fetchHC()
