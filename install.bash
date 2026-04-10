#!/bin/bash
APP_NAME=velvasam
APP_PATH=/opt/bitnami/projects/$APP_NAME
cp bkup/${APP_NAME}.tar.gz .
gunzip ${APP_NAME}.tar.gz
tar -tf ${APP_NAME}.tar > bkup/REL.txt

#Backup
BKUP_TAR=${APP_NAME}_$$.tar
tar -cf $BKUP_TAR -T bkup/REL.txt
gzip $BKUP_TAR
mv $BKUP_TAR.gz bkup/.

#Release
tar -xvf ${APP_NAME}.tar
rm ${APP_NAME}.tar

#change permission
sudo chown daemon:daemon db.sqlite3
sudo chown daemon:daemon $APP_PATH
sudo chmod g+w db.sqlite3
sudo chmod g+w $APP_PATH

#restart
cd /opt/bitnami
sudo ./ctlscript.sh restart
