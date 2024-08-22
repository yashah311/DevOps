#!/usr/bin/python
# -*- coding: utf-8 -*-

# Author: Yash Shah (shah.yash@accenture.com)
# This python script is used to target and untarget JCA for BRM adapter on the domain specific environment using wlst

import os
import sys
import re

# Assigning inputs to the variables
#PROP_FILE_CONFIG = sys.argv[1]
#domain = sys.argv[2].upper()

# DEBUG
PROP_FILE_CONFIG = "/u01/oracle/domains/shared/scripts/domain.properties"
domain = "O2C"

print ' >> Property file :', PROP_FILE_CONFIG
print ' >> Domain Name :', domain


# =======================================================================================
# Utility function to find the token value from the property config file
# =======================================================================================

def findPropVal(Search_str):
    token_list = [line for line in open(PROP_FILE_CONFIG).readlines()
                  if Search_str in line]
    for ln in token_list:
        if not ln.startswith('#'):
            start = Search_str + '='
            end = '\n'
            return re.search('%s(.*)%s' % (start, end), ln).group(1)


# =======================================================================================
# Utility function to perform the target/ untarget for the JCA adapter
# =======================================================================================

def targetuntarget():
    try:
        print 'Untargetting OracleBRMJCA15Adapter'
        edit()
        startEdit()
        cd('/AppDeployments/OracleBRMJCA15Adapter')
        set('Targets', jarray.array([], ObjectName))
        save()
        activate()
        print 'Targetting OracleBRMJCA15Adapter'
        edit()
        startEdit()
        cd('/AppDeployments/OracleBRMJCA15Adapter')
        set('Targets',jarray.array([ObjectName('com.bea:Name='+CLUSTER_NAME+',Type=Cluster')], ObjectName))
        save()
        activate()
        print ("JCA tgt untgt Successful")
    except:
        cancelEdit(defaultAnswer='y')
        print ("JCA tgt untgt Unsuccessful")

# =======================================================================================
# Main function to connect wlst and perform the target/ untarget for the JCA adapter
# =======================================================================================

if __name__ == 'main':
    username = findPropVal(domain + '_ADMIN_USERNAME')
    password = findPropVal(domain + '_ADMIN_PASSWORD')
    host = findPropVal(domain + '_ADMIN_LISTEN_ADDRESS')
    port = findPropVal(domain + '_ADMIN_LISTEN_PORT')
    admin_server_url = 't3://' + host + ':' + port
    CLUSTER_NAME = 'soa_cluster'

    # connect to the server

    connect(username, password, admin_server_url)

    # calling the function

    targetuntarget()
