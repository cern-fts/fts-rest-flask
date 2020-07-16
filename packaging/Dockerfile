FROM centos:7

RUN useradd fts
USER fts
WORKDIR /home/fts

COPY src/fts3rest/fts3rest .
RUN python3 -m venv venv
ENV PATH="/home/fts/venv/bin:$PATH"
RUN pip install --upgrade pip &&  \
    pip install pip-tools && \
    pip-compile --upgrade requirements.in && \
    pip-sync requirements.txt

mkdir -p %{buildroot}%{python3_sitelib}
mkdir -p %{buildroot}%{_libexecdir}/fts3rest
mkdir -p %{buildroot}%{_sysconfdir}/httpd/conf.d
mkdir -p %{buildroot}%{_sysconfdir}/fts3
mkdir -p %{buildroot}/%{_var}/log/fts3rest
cp -r fts3rest/fts3rest %{buildroot}%{python3_sitelib}
cp fts3rest/fts3rest.wsgi %{buildroot}%{_libexecdir}/fts3rest
cp fts3rest/fts3rest.conf %{buildroot}%{_sysconfdir}/httpd/conf.d/fts3rest.conf
cp fts3rest/fts3config %{buildroot}%{_sysconfdir}/fts3