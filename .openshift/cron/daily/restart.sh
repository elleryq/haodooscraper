#!/bin/bash
export TZ='Asia/Taipei'
curl -I ${OPENSHIFT_APP_DNS} 2> /dev/null | head -1 | grep -q '200\|301\|302'
s=$?
if [ $s != 0 ];
	then
		echo "`date +"%Y-%m-%d %H:%M:%S"` down" >> ${OPENSHIFT_DATA_DIR}web_error.log
		echo "`date +"%Y-%m-%d %H:%M:%S"` restarting..." >> ${OPENSHIFT_DATA_DIR}web_error.log
		/usr/bin/gear stop 2>&1 /dev/null
		/usr/bin/gear start 2>&1 /dev/null
		echo "`date +"%Y-%m-%d %H:%M:%S"` restarted!!!" >> ${OPENSHIFT_DATA_DIR}web_error.log		
else
	echo "`date +"%Y-%m-%d %H:%M:%S"` is ok" > ${OPENSHIFT_DATA_DIR}web_run.log
fi
