FROM almalinux:9

RUN dnf install python3 git python3-devel openssl-devel gcc gcc-c++ make mariadb -y && \
    dnf clean all
# Install dependencies needed in pipcompile step
RUN dnf install swig mysql-devel -y --enablerepo=crb && \
    dnf clean all
# Install pyenv dependencies
RUN dnf install zlib-devel bzip2 bzip2-devel readline-devel sqlite sqlite-devel openssl-devel tk-devel libffi-devel -y && \
    dnf clean all
# Install rpmbuild dependencies
RUN dnf install rpm-build rpm-devel rpmlint rpmdevtools diffutils patch -y && \
    dnf clean all
# Workaround for Alma9 locale warnings
RUN dnf install glibc-langpack-en -y && \
    dnf clean all

RUN useradd --create-home ci

# Create directory for logs
RUN mkdir /var/log/fts3rest && chown ci:ci /var/log/fts3rest

WORKDIR /home/ci
USER ci

# Python versions selected for the CI environment
ENV PY39 3.9.18
ENV PY310 3.10.12
ENV PY311 3.11.8

# Install "pyenv" following instructions from https://github.com/pyenv/pyenv
RUN git clone --depth 1 --branch v2.4.0 https://github.com/pyenv/pyenv.git ~/.pyenv && \
echo 'export PYENV_ROOT="$HOME/.pyenv"' >> ~/.bashrc && \
echo 'export PATH="$PYENV_ROOT/bin:$PATH"' >> ~/.bashrc && \
echo -e 'if command -v pyenv 1>/dev/null 2>&1; then\n  eval "$(pyenv init --path)"\n  eval "$(pyenv init -)"\nfi' >> ~/.bashrc && \
source ~/.bashrc && \
pyenv install $PY39 && \
pyenv install $PY310 && \
pyenv install $PY311

# Needed for pip-tools
ENV LC_ALL en_US.utf-8
ENV LANG en_US.utf-8

# Copy the requirements files
USER root
COPY pipcompile.sh requirements.in dev-requirements.in ./
RUN cd /home/ci && chown ci:ci pipcompile.sh requirements.in dev-requirements.in
USER ci

# Prepare virtual environments
ENV VENV_39 /home/ci/venv_39
ENV VENV_310 /home/ci/venv_310
ENV VENV_311 /home/ci/venv_311

RUN . ~/.bashrc && pyenv global $PY39 && python3 -m venv $VENV_39 && \
    . $VENV_39/bin/activate && pip install --upgrade pip && pip install pip-tools && \
    . ./pipcompile.sh --sync && deactivate

RUN . ~/.bashrc && pyenv global $PY310 && python3 -m venv $VENV_310 && \
    . $VENV_310/bin/activate && pip install --upgrade pip && pip install pip-tools && \
    . ./pipcompile.sh --sync && deactivate

RUN . ~/.bashrc && pyenv global $PY311 && python3 -m venv $VENV_311 && \
    . $VENV_311/bin/activate && pip install --upgrade pip && pip install pip-tools && \
    . ./pipcompile.sh --sync && deactivate

# Run on Python3.9 by default
RUN . ~/.bashrc && pyenv global $PY39
ENV PATH="$VENV_39/bin:$PATH"
