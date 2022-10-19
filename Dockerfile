FROM quay.io/centos/centos:stream9
ARG USER=canary-agent
ARG GROUP=canary
ARG UID=43000
ARG GID=43000
ENV PBR_VERSION 14.0.0
RUN  yum install -y git python3-pip \
    gcc gcc-c++ openssl-devel libffi-devel \
    libxml2-devel libxslt-devel zlib-devel bzip2-devel

RUN mkdir -p /var/log/healthmon
RUN touch /var/log/healthmon/healthmon.log
RUN  groupadd --gid $GID $GROUP \
    && useradd -l -M --shell /usr/sbin/nologin --uid $UID --gid $GID $USER

RUN chown -R $UID:$GID /var/log/healthmon
COPY . /home/$USER
RUN chown -R $UID:$GID /home/$USER
RUN cd /home/$USER && git submodule init && git submodule update
RUN pip3 install /home/$USER/tempest-fork/
RUN pip3 install /home/$USER/python-tempestconf/
RUN pip3 install /home/$USER/HealthMonitorTempestPlugin/
RUN tempest init cloud
RUN chown -R $UID:$GID cloud
RUN chown -R $UID:$GID /tmp/tempest-lock
RUN touch cloud/etc/accounts.yml
USER $USER