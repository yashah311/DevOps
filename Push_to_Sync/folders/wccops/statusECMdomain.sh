#!/bin/bash
pgrep -f Admin > admincount.out
pgrep -f UCM > mngservercount.out

AC=$(expr $(cat admincount.out | wc -l) )
MC=$(expr $(cat mngservercount.out | wc -l) )

if [ ${AC} -eq  0 ] ; then Admin_Server_Status="RED" ; else Admin_Server_Status="GREEN" ; fi
if [ ${MC} -eq  0 ] ; then Managed_Server_Status="RED" ; else Managed_Server_Status="GREEN" ; fi

echo
echo "==========ECM domain========"
echo "Admin Server|Managed Server"
echo "___${Admin_Server_Status}___|___${Admin_Server_Status}___"
echo

rm *.out
