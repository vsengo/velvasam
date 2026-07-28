#!/bin/bash
app_name=velvasam
keyDir=velvasam.pem
IP=18.207.68.86
USER=bitnami
HOME=`pwd`

if [ $# -lt 1 ]; then
	echo "velvasam.bash install/login"
	exit 1
fi
if [ $1 = 'install' ]; then
	if [ -f $app_name.tar ]; then
		rm -f $app_name.tar
	fi
	tar -cvf $app_name.tar accounts home reports util velvasam db.sqlite3 manage.py requirements.txt
	gzip $app_name.tar
	
	scp -v -i $keyDir $app_name.tar.gz  ${USER}@${IP}:~/velvasam/bkup/.
	ssh -v -i $keyDir  ${USER}@${IP}
elif [ $1 = 'getDb' ]; then
	scp -v -i $keyDir ${USER}@${IP}:~/velvasam/db.sqlite3  bkupdb_aws.sqlite3
elif [ $1 = 'putData' ]; then
	if [ $# -lt 2 ]; then
	   echo "Please provide a tar file"
	   exit 1
	fi
	scp -v -i $keyDir $2 ${USER}@${IP}:~/velvasam/.
elif [ $1 = 'getFile' ]; then
	scp -v -i $keyDir ${USER}@${IP}:~/velvasam/$2  bkup/$2
else
	ssh -v -i $keyDir  ${USER}@${IP}
fi



