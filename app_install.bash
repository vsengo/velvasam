#!/bin/bash
appName=velvasam
keyDir=~/Documents/MyFin/Finance_2022/finApp/SengoMac.pem

if [ $# -gt 1 ]; then
	file=$1
	if [ $2 = put ]; then
		scp -i  $keyDir velvasam/$file  ec2-user@34.229.92.71:~/velvasam/$file
	else
		if [ -f velvasam/db.sqlite3 ]; then
			mv db.sqlite3 db.sqlite3.$$
			scp -i  $keyDir ec2-user@34.229.92.71:~/velvasam/db.sqlite3 velvasam/.
		fi
	fi
else
	f=${appName}.tar
	rm -f $f
	tar -cvf $f  ${appName}/accounts ${appName}/home ${appName}/util ${appName}/velvasam ${appName}/db.sqlite3 ${appName}/manage.py ${appName}/requirement.txt 
	gzip $f

	scp -i  $keyDir  $f.gz  ec2-user@34.229.92.71:~/.
fi

