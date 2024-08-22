#cd /u01/oracle/domains/shared/heapdump
jmap -dump:live,format=b,file=/u01/oracle/domains/shared/hdlogs/${1}_hd_$(date +%Y%m%d%H%M%S).hprof $(ps -ef |grep ${1}| grep java | grep -v grep | awk '{print $2}')
#echo "hi $1" >> as.out
