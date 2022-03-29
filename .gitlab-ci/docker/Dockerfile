FROM centos:7

RUN yum install python3 git python3-devel openssl-devel swig gcc gcc-c++ make mysql-devel mariadb -y && \
    yum clean all
# Install pyenv dependencies
RUN yum install gcc zlib-devel bzip2 bzip2-devel readline-devel sqlite sqlite-devel openssl-devel tk-devel libffi-devel -y && \
    yum clean all
# Install rpmbuild dependencies
RUN yum install gcc rpm-build rpm-devel rpmlint make coreutils diffutils patch rpmdevtools -y && \
    yum clean all

RUN useradd --create-home ci

# Create directory for logs
RUN mkdir /var/log/fts3rest
RUN chown ci /var/log/fts3rest

WORKDIR /home/ci
USER ci

ENV PY36 3.6.10
ENV PY37 3.7.7
ENV PY38 3.8.2

# Install "pyenv" following instructions from https://github.com/pyenv/pyenv
RUN git clone --depth 1 --branch v2.2.5 https://github.com/pyenv/pyenv.git ~/.pyenv && \
echo 'export PYENV_ROOT="$HOME/.pyenv"' >> ~/.bashrc && \
echo 'export PATH="$PYENV_ROOT/bin:$PATH"' >> ~/.bashrc && \
echo -e 'if command -v pyenv 1>/dev/null 2>&1; then\n  eval "$(pyenv init --path)"\n  eval "$(pyenv init -)"\nfi' >> ~/.bashrc && \
source ~/.bashrc && \
pyenv install $PY36 && \
pyenv install $PY37 && \
pyenv install $PY38

# Needed for pip-tools
ENV LC_ALL en_US.utf-8
ENV LANG en_US.utf-8

# Copy the requirements files
USER root
COPY pipcompile.sh requirements.in dev-requirements.in ./
RUN cd /home/ci && chown ci:ci pipcompile.sh requirements.in dev-requirements.in
USER ci

# Prepare virtual environments
ENV VENV_36 /home/ci/venv_36
ENV VENV_37 /home/ci/venv_37
ENV VENV_38 /home/ci/venv_38

RUN . ~/.bashrc && pyenv global $PY36 && python3 -m venv $VENV_36 && \
    . $VENV_36/bin/activate && pip install --upgrade pip && pip install pip-tools && \
    . ./pipcompile.sh --sync && deactivate

RUN . ~/.bashrc && pyenv global $PY37 && python3 -m venv $VENV_37 && \
    . $VENV_37/bin/activate && pip install --upgrade pip && pip install pip-tools && \
    . ./pipcompile.sh --sync && deactivate

RUN . ~/.bashrc && pyenv global $PY38 && python3 -m venv $VENV_38 && \
    . $VENV_38/bin/activate && pip install --upgrade pip && pip install pip-tools && \
    . ./pipcompile.sh --sync && deactivate

# Run on Python3.6 by default
RUN . ~/.bashrc && pyenv global $PY36
ENV PATH="$VENV_36/bin:$PATH"
