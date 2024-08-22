# Author: Yash Shah (shah.yash@accenture.com)
# This python script is used to test all datasources on the domain specific environment using wlst
import sys, traceback
connect('weblogic','Welcome_91','t3://cpp2-fmw12c-01:7301')

def main():
  try:
    domainName = cmo.getName();
    allServers=domainRuntimeService.getServerRuntimes();
    if (len(allServers) > 0):
      for tempServer in allServers:
        jdbcServiceRT = tempServer.getJDBCServiceRuntime();
        dataSources = jdbcServiceRT.getJDBCDataSourceRuntimeMBeans();
        serverName = tempServer.getName();
        if (len(dataSources) > 0):
          print('DOMAIN SERVER DATASOURCE STATE TEST')
          for dataSource in dataSources:
            testPool = dataSource.testPool()
            dataSourceName = dataSource.getName()
            if (testPool == None):
              print domainName +'\t'+ serverName +'\t'+ dataSourceName+'\t'+dataSource.getState()+'\tOK'
            else:
              print domainName +'\t'+ serverName +'\t'+ dataSourceName+'\t'+dataSource.getState()+'\tFailure: '
              print testPool

  except:
    apply(traceback.print_exception, sys.exc_info())
    exit(exitcode=1)
#
main();

