#!/bin/bash

set -euox pipefail

sudo yum install -y python39 python39-pip gcc gcc-c++ openssl-devel libffi-devel \
    libxml2-devel libxslt-devel zlib-devel bzip2-devel 

[ ! -d 'venv' ] && python3.9 -m venv venv 
source venv/bin/activate

git submodule init && git submodule update
pushd tempest-fork/
git checkout no_admin_creds
git pull 
popd 
pushd python-tempestconf/ 
git checkout master
git pull 
popd 
pushd HealthMonitorTempestPlugin/
git checkout main
git pull
popd

pip install ansible 

export PBR_VERSION=14.0.0

pip install python-tempestconf/
pip install tempest-fork/
pip install HealthMonitorTempestPlugin/

touch venv/clouddev/etc/accounts.yml

[ ! -d 'venv/clouddev' ] && tempest init venv/clouddev

ansible-playbook setupDev.yml


