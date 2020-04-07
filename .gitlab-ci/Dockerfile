FROM centos:7

RUN yum install python3 git python3-devel openssl-devel swig gcc gcc-c++ make mysql-devel mariadb -y && \
yum clean all
# install pyenv dependencies
RUN yum install gcc zlib-devel bzip2 bzip2-devel readline-devel sqlite sqlite-devel openssl-devel tk-devel libffi-devel -y && \
yum clean all

RUN useradd --create-home ci

# create directory for logs
RUN mkdir /var/log/fts3rest
RUN chown ci /var/log/fts3rest

WORKDIR /home/ci
USER ci

# install pyenv, following instructions from https://github.com/pyenv/pyenv
RUN git clone https://github.com/pyenv/pyenv.git ~/.pyenv && \
echo 'export PYENV_ROOT="$HOME/.pyenv"' >> ~/.bashrc && \
echo 'export PATH="$PYENV_ROOT/bin:$PATH"' >> ~/.bashrc && \
echo -e 'if command -v pyenv 1>/dev/null 2>&1; then\n  eval "$(pyenv init -)"\nfi' >> ~/.bashrc && \
source ~/.bashrc && \
pyenv install 3.6.10 && \
pyenv install 3.7.7 && \
pyenv install 3.8.2

# this is needed for pip-tools
ENV LC_ALL en_US.utf-8
ENV LANG en_US.utf-8

# copy the requirements files
COPY --chown=ci pipcompile.sh pipsyncdev.sh dev-requirements.in requirements.in ./

# Prepare virtual environments this is needed to run pip in the venv
ENV VIRTUAL_ENV_36 /home/ci/venv_36
ENV _OLD_VIRTUAL_PATH="$PATH"
ENV PATH="$VIRTUAL_ENV_36/bin:$PATH"
RUN source ~/.bashrc && pyenv global 3.6.10 && python -m venv $VIRTUAL_ENV_36 && \
pip3 install --upgrade pip && pip3 install pip-tools && \
chmod u+x pipcompile.sh && ./pipcompile.sh && \
chmod u+x pipsyncdev.sh && ./pipsyncdev.sh
ENV PATH="$_OLD_VIRTUAL_PATH"

ENV VIRTUAL_ENV_37 /home/ci/venv_37
ENV _OLD_VIRTUAL_PATH="$PATH"
ENV PATH="$VIRTUAL_ENV_37/bin:$PATH"
RUN source ~/.bashrc && pyenv global 3.7.7 && python -m venv $VIRTUAL_ENV_37 && \
pip3 install --upgrade pip && pip3 install pip-tools && \
chmod u+x pipcompile.sh && ./pipcompile.sh && \
chmod u+x pipsyncdev.sh && ./pipsyncdev.sh
ENV PATH="$_OLD_VIRTUAL_PATH"

ENV VIRTUAL_ENV_38 /home/ci/venv_38
ENV _OLD_VIRTUAL_PATH="$PATH"
ENV PATH="$VIRTUAL_ENV_38/bin:$PATH"
RUN source ~/.bashrc && pyenv global 3.8.2 && python -m venv $VIRTUAL_ENV_38 && \
pip3 install --upgrade pip && pip3 install pip-tools && \
chmod u+x pipcompile.sh && ./pipcompile.sh && \
chmod u+x pipsyncdev.sh && ./pipsyncdev.sh
ENV PATH="$_OLD_VIRTUAL_PATH"

# by default we run on the lowest version supported
ENV VIRTUAL_ENV_36 /home/ci/venv_36
ENV PATH="$VIRTUAL_ENV_36/bin:$PATH"
RUN source ~/.bashrc && pyenv global 3.6.10
