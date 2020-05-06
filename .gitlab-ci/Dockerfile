FROM centos:7

RUN yum install python3 git python3-devel openssl-devel swig gcc-c++ mysql-devel mariadb -y && \
yum clean all

RUN useradd --create-home ci

# create directory for logs
RUN mkdir /var/log/fts3rest
RUN chown ci /var/log/fts3rest

WORKDIR /home/ci
USER ci


# this is needed for pip-tools
ENV LC_ALL en_US.utf-8
ENV LANG en_US.utf-8

# copy the requirements files
COPY --chown=ci pipcompile.sh pipsyncdev.sh dev-requirements.in requirements.in ./

# Prepare virtual environments
ENV VENV_36 /home/ci/venv_36

RUN python3.6 -m venv $VENV_36 && source $VENV_36/bin/activate && \
    pip install --upgrade pip && pip install pip-tools && \
    source ./pipcompile.sh && source ./pipsyncdev.sh && deactivate

ENV PATH="$VENV_36/bin:$PATH"
