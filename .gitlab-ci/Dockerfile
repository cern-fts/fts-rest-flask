FROM centos:7

RUN yum install python3 git python3-devel openssl-devel swig gcc gcc-c++ make mysql-devel mariadb -y && \
yum clean all
# install pyenv dependencies
RUN yum install gcc zlib-devel bzip2 bzip2-devel readline-devel sqlite sqlite-devel openssl-devel tk-devel libffi-devel -y && \
yum clean all

# create directory for logs
RUN mkdir /var/log/fts3rest
RUN chown ci /var/log/fts3rest

RUN useradd --create-home ci
WORKDIR /home/ci
USER ci

# install pyenv, following instructions from https://github.com/pyenv/pyenv
RUN git clone https://github.com/pyenv/pyenv.git ~/.pyenv
RUN echo 'export PYENV_ROOT="$HOME/.pyenv"' >> ~/.bashrc
RUN echo 'export PATH="$PYENV_ROOT/bin:$PATH"' >> ~/.bashrc
RUN echo -e 'if command -v pyenv 1>/dev/null 2>&1; then\n  eval "$(pyenv init -)"\nfi' >> ~/.bashrc
RUN exec "$SHELL"
RUN pyenv install 3.6.10
RUN pyenv install 3.7.7
RUN pyenv install 3.8.2

# this is needed for pip-tools
ENV LC_ALL en_US.utf-8
ENV LANG en_US.utf-8

# copy the requirements files
COPY --chown=ci pipcompile.sh pipsyncdev.sh dev-requirements.in requirements.in ./

# Prepare virtual environments this is needed to run pip in the venv
RUN pyenv global 3.6.10
ENV VIRTUAL_ENV_36 /home/ci/venv_36
ENV _OLD_VIRTUAL_PATH="$PATH"
ENV PATH="$VIRTUAL_ENV_36/bin:$PATH"
RUN python3 -m venv $VIRTUAL_ENV_36
RUN pip3 install --upgrade pip && pip3 install pip-tools
RUN chmod u+x pipcompile.sh && ./pipcompile.sh
RUN chmod u+x pipsyncdev.sh && ./pipsyncdev.sh
ENV PATH="$_OLD_VIRTUAL_PATH"

RUN pyenv global 3.7.7
ENV VIRTUAL_ENV_37 /home/ci/venv_37
ENV _OLD_VIRTUAL_PATH="$PATH"
ENV PATH="$VIRTUAL_ENV_37/bin:$PATH"
RUN python3 -m venv $VIRTUAL_ENV_37
RUN pip3 install --upgrade pip && pip3 install pip-tools
RUN chmod u+x pipcompile.sh && ./pipcompile.sh
RUN chmod u+x pipsyncdev.sh && ./pipsyncdev.sh
ENV PATH="$_OLD_VIRTUAL_PATH"

RUN pyenv global 3.8.2
ENV VIRTUAL_ENV_38 /home/ci/venv_38
ENV _OLD_VIRTUAL_PATH="$PATH"
ENV PATH="$VIRTUAL_ENV_38/bin:$PATH"
RUN python3 -m venv $VIRTUAL_ENV_38
RUN pip3 install --upgrade pip && pip3 install pip-tools
RUN chmod u+x pipcompile.sh && ./pipcompile.sh
RUN chmod u+x pipsyncdev.sh && ./pipsyncdev.sh
ENV PATH="$_OLD_VIRTUAL_PATH"

# by default we run on the lowest version supported
RUN pyenv global 3.6.10
ENV VIRTUAL_ENV_36 /home/ci/venv_36
ENV PATH="$VIRTUAL_ENV_36/bin:$PATH"
