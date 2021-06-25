#!/bin/bash

set -e

APPNAME=tow-pacer
BUCKET=$APPNAME-deployment2
DEPLOYMENT_GROUP=production
DEPLOYARCHIVEFN=deploy-$APPNAME.tar.gz

tar -cvf infra/${DEPLOYARCHIVEFN%.gz} --exclude pacerporcupine/pacerporcupine/models/classifier/ --exclude pacerporcupine/pacerporcupine/models/flairner/ search_warrant_alerter/* pacerporcupine/* infra/deploy/*
tar -rvf infra/${DEPLOYARCHIVEFN%.gz}  -C courtlistener_search_warrant_alerter appspec.yml
gzip -f infra/${DEPLOYARCHIVEFN%.gz}

aws s3 mb --region us-east-1 s3://$BUCKET || echo "bucket exists already"
aws s3 rm s3://$BUCKET/$DEPLOYARCHIVEFN
aws s3 cp --region us-east-1 infra/$DEPLOYARCHIVEFN s3://$BUCKET/

# rm infra/$DEPLOYARCHIVEFN

depl=$(aws deploy create-deployment  --output text --region us-east-1 --application-name $APPNAME --deployment-group-name $DEPLOYMENT_GROUP --ignore-application-stop-failures --s3-location bundleType=tgz,bucket=$BUCKET,key=$DEPLOYARCHIVEFN --file-exists-behavior=OVERWRITE)
echo $depl
sleep 30
aws deploy get-deployment  --output text --region us-east-1 --deployment-id $depl | head -n 1 | rev | cut -f2 -d '	' | rev
sleep 30
aws deploy get-deployment  --output text --region us-east-1 --deployment-id $depl | head -n 1 | rev | cut -f2 -d '	' | rev
sleep 30
aws deploy get-deployment  --output text --region us-east-1 --deployment-id $depl | head -n 1 | rev | cut -f2 -d '	' | rev

echo "To check deployment status, run 'AWS_PROFILE=$AWS_PROFILE aws deploy get-deployment --region us-east-1 --deployment-id $depl'"
# 
