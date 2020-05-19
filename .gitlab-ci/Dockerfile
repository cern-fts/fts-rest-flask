FROM centos:7

RUN yum install python3 git python3-devel openssl-devel swig gcc gcc-c++ make mysql-devel mariadb -y && \
yum clean all
# install pyenv dependencies
RUN yum install gcc zlib-devel bzip2 bzip2-devel readline-devel sqlite sqlite-devel openssl-devel tk-devel libffi-devel -y && \
yum clean all
# install rpmbuild dependencies
RUN yum install gcc rpm-build rpm-devel rpmlint make coreutils diffutils patch rpmdevtools -y

RUN useradd --create-home ci

# create directory for logs
RUN mkdir /var/log/fts3rest
RUN chown ci /var/log/fts3rest

WORKDIR /home/ci
USER ci

ENV PY36 3.6.10
ENV PY37 3.7.7
ENV PY38 3.8.2

# install pyenv, following instructions from https://github.com/pyenv/pyenv
RUN git clone --depth 1 --branch master https://github.com/pyenv/pyenv.git ~/.pyenv && \
echo 'export PYENV_ROOT="$HOME/.pyenv"' >> ~/.bashrc && \
echo 'export PATH="$PYENV_ROOT/bin:$PATH"' >> ~/.bashrc && \
echo -e 'if command -v pyenv 1>/dev/null 2>&1; then\n  eval "$(pyenv init -)"\nfi' >> ~/.bashrc && \
source ~/.bashrc && \
pyenv install $PY36 && \
pyenv install $PY37 && \
pyenv install $PY38

# this is needed for pip-tools
ENV LC_ALL en_US.utf-8
ENV LANG en_US.utf-8

# copy the requirements files
COPY --chown=ci pipcompile.sh pipsyncdev.sh dev-requirements.in requirements.in ./

# Prepare virtual environments
ENV VENV_36 /home/ci/venv_36
ENV VENV_37 /home/ci/venv_37
ENV VENV_38 /home/ci/venv_38

RUN . ~/.bashrc && pyenv global $PY36 && python -m venv $VENV_36 && \
. $VENV_36/bin/activate && pip install --upgrade pip && pip install pip-tools && \
. ./pipcompile.sh && . ./pipsyncdev.sh && deactivate

RUN . ~/.bashrc && pyenv global $PY37 && python -m venv $VENV_37 && \
. $VENV_37/bin/activate && pip install --upgrade pip && pip install pip-tools && \
. ./pipcompile.sh && . ./pipsyncdev.sh && deactivate

RUN . ~/.bashrc && pyenv global $PY38 && python -m venv $VENV_38 && \
. $VENV_38/bin/activate && pip install --upgrade pip && pip install pip-tools && \
. ./pipcompile.sh && . ./pipsyncdev.sh && deactivate

# by default we run on the lowest version supported
RUN . ~/.bashrc && pyenv global $PY36
ENV PATH="$VENV_36/bin:$PATH"
