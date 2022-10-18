FROM quay.io/centos/centos:stream9
COPY . /
RUN yum -y install python39 && yum install -y git python39 python39-devel \
     gcc gcc-c++ openssl-devel libffi-devel \
     libxml2-devel libxslt-devel zlib-devel bzip2-devel
RUN git submodule init && git submodule update
RUN mkdir -p /var/log/healthmon
RUN touch /var/log/healthmon/healthmon.log
RUN pip install tempest-fork/
RUN pip install python-tempestconf/
RUN pip install HealthMonitorTempestPlugin/
RUN tempest init cloud

RUN  groupadd --gid 43000 canary \
    && useradd -l -M --shell /usr/sbin/nologin --uid 43000 --gid 43000 canary-agent

USER canary-agent