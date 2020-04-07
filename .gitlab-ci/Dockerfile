FROM centos:7

RUN yum install python3 git python3-devel openssl-devel swig gcc gcc-c++ make mysql-devel -y && \
yum clean all

RUN useradd --create-home ci
WORKDIR /home/ci
USER ci

# this is needed to run pip in the venv
ENV VIRTUAL_ENV /home/ci/venv
ENV PATH="$VIRTUAL_ENV/bin:$PATH"

# this is needed for pip-tools
ENV LC_ALL en_US.utf-8
ENV LANG en_US.utf-8

COPY --chown=ci pipcompile.sh pipsyncdev.sh dev-requirements.in requirements.in ./

RUN python3 -m venv $VIRTUAL_ENV
RUN pip3 install --upgrade pip && pip3 install pip-tools
RUN chmod u+x pipcompile.sh && ./pipcompile.sh
RUN chmod u+x pipsyncdev.sh && ./pipsyncdev.sh

USER root
RUN mkdir /var/log/fts3rest
RUN chmod o+rwx /var/log/fts3rest

USER ci