FROM centos:7

RUN yum install python3 git -y

RUN useradd --create-home ci
WORKDIR /home/ci
USER ci

# this is needed to run pip in the venv
ENV VIRTUAL_ENV /home/ci/venv
ENV PATH="$VIRTUAL_ENV/bin:$PATH"

# this is needed for pip-tools
ENV LC_ALL en_US.utf-8
ENV LANG en_US.utf-8

RUN python3 -m venv $VIRTUAL_ENV && \
 pip3 install --upgrade pip && \
 pip3 install pip-tools black pylint radon bandit
