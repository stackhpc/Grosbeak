FROM quay.io/centos/centos:stream9
COPY . /
ENV PBR_VERSION 14.0.0
RUN  yum install -y git python3-pip \
     gcc gcc-c++ openssl-devel libffi-devel \
     libxml2-devel libxslt-devel zlib-devel bzip2-devel
RUN git submodule init && git submodule update
RUN mkdir -p /var/log/healthmon
RUN touch /var/log/healthmon/healthmon.log
RUN pip3 install tempest-fork/
RUN pip3 install python-tempestconf/
RUN pip3 install HealthMonitorTempestPlugin/
RUN tempest init cloud

RUN  groupadd --gid 43000 canary \
    && useradd -l -M --shell /usr/sbin/nologin --uid 43000 --gid 43000 canary-agent

USER canary-agent