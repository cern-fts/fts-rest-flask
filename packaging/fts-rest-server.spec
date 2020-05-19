Name:           fts-rest-server
Version:        0.1
Release:        1%{?dist}
Summary:        File Transfer Service (FTS) -- Python3 HTTP API Server

License:        ASL 2.0
URL:            https://fts.web.cern.ch/
Source0:        %{name}-%{version}.tar.gz

BuildRequires:  python3
Requires:       python3
Requires:       httpd
Requires:       httpd-devel
Requires:       rh-python36-mod_wsgi
Requires:       gridsite
Requires:       gfal2-python3
Requires:       gfal2-plugin-mock
Requires:       python36-m2crypto
Requires:       python36-requests
Requires:       python36-flask
Requires:       python36-sqlalchemy
Requires:       python36-dateutil
# from mysqlclient:
Requires:       python3-devel
Requires:       mysql-devel
# The packages below are not found in community repos and will have to be packaged by us
Requires:       python36-mako
 # does dirq work with Python3?
Requires:       python36-dirq
Requires:       python36-mysqlclient
Requires:       python36-PyJWT
Requires:       python36-jwcrypto
Requires:       python36-oic

BuildArch:      noarch

%description
File Transfer Service (FTS) -- Python3 HTTP API Server

%prep
%setup -q

%build
python3 -m compileall fts3rest/fts3rest

%install
mkdir -p %{buildroot}%{python3_sitelib}
mkdir -p %{buildroot}%{_libexecdir}/fts3rest
mkdir -p %{buildroot}%{_sysconfdir}/httpd/conf.d/
cp -r fts3rest/fts3rest %{buildroot}%{python3_sitelib}
cp fts3rest/fts3restwsgi.py %{buildroot}%{_libexecdir}/fts3rest
cp fts3rest/httpd_fts.conf %{buildroot}%{_sysconfdir}/httpd/conf.d/fts3rest.conf
mkdir -p %{buildroot}/%{_var}/log/fts3rest

%files
%license LICENSE
%config(noreplace) %{_sysconfdir}/httpd/conf.d/fts3rest.conf
%{python3_sitelib}/fts3rest/


%changelog
* Tue May 19 2020 Carles Garcia Cabot <carles.garcia.cabot@cern.ch> - 0.1-1
- First server package release