#!/bin/bash
appName=velvasam
keyDir=~/Documents/MyWeb/velvasam/SengoRSAforEC2.pem
ssh -v -i $keyDir ec2@ec2-52-55-52-125.compute-1.amazonaws.com
