Name:           fts-rest-server
Version:        1.0.0
Release:        1%{?dist}
Summary:        File Transfer Service (FTS) -- Python3 HTTP API Server

License:        ASL 2.0
URL:            https://fts.web.cern.ch/
Source0:        %{name}-%{version}.tar.gz

BuildRequires:  python3
BuildRequires:  python3-rpm-macros
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
Requires:       python36-dateutil
Requires:       python36-jwt
Obsoletes:      fts-rest

# from mysqlclient:
Requires:       python3-devel
Requires:       mysql-devel
# from jwcrypto
Requires:       python36-cryptography
# from oic
Requires:       python36-defusedxml
Requires:       python36-pycryptodomex
# from mako
Requires:       python36-markupsafe

### The packages below are not found in community repos and will have to be packaged by us
# from oic (pyjwkest may require six, future...)
Requires:       pyjwkest
Requires:       Beaker
Requires:       typing_extensions
Requires:       SQLAlchemy >= 1.1.15
Obsoletes:      python36-sqlalchemy
Requires:       Mako
Requires:       mysqlclient
Requires:       jwcrypto
Requires:       oic
Requires:       dirq

BuildArch:      noarch

%description
File Transfer Service (FTS) -- Python3 HTTP API Server

%package selinux
Summary:        SELinux support for FTS-REST
Group:          Applications/Internet
Requires:       %{name} = %{version}-%{release}
Obsoletes:      fts-rest-selinux

%description selinux
SELinux support for the FTS HTTP API Server

%prep
%setup -q

%build
python3 -m compileall fts3rest/fts3rest

# Check https://docs.fedoraproject.org/en-US/packaging-guidelines/Python/
# Program files go in /usr/lib/python3.6/site-packages
# Where does the WSGI file go? /usr/libexec
%install
mkdir -p %{buildroot}%{python3_sitelib}
mkdir -p %{buildroot}%{_libexecdir}/fts3rest
mkdir -p %{buildroot}%{_sysconfdir}/httpd/conf.d
mkdir -p %{buildroot}%{_sysconfdir}/fts3
mkdir -p %{buildroot}%{_var}/log/fts3rest
mkdir -p %{buildroot}%{_sysconfdir}/logrotate.d/
cp -r fts3rest/fts3rest %{buildroot}%{python3_sitelib}
cp fts3rest/fts3rest.wsgi %{buildroot}%{_libexecdir}/fts3rest
cp fts3rest/fts3rest.conf %{buildroot}%{_sysconfdir}/httpd/conf.d/fts3rest.conf
cp fts3rest/ftsrestconfig %{buildroot}%{_sysconfdir}/fts3
cp fts3rest/fts-rest.logrotate %{buildroot}%{_sysconfdir}/logrotate.d/fts-rest

# Create fts3 user and group
%pre
getent group fts3 >/dev/null || groupadd -r fts3
getent passwd fts3 >/dev/null && usermod -a -G apache fts3
# For an unknown reason SELinux does not allow useradd with -m to create home directory
getent passwd fts3 >/dev/null || \
    useradd -r -g fts3 -G apache -d /var/log/fts3 -s /sbin/nologin \
    -c "File Transfer Service user" fts3
if [ ! -d /var/log/fts3 ] ; then
mkdir /var/log/fts3
chown fts3:fts3 /var/log/fts3
fi
exit 0

# SELinux scriptlets
%post selinux
if [ "$1" -eq "1" ] ; then
semanage port -a -t http_port_t -p tcp 8446
setsebool -P httpd_can_network_connect on
setsebool -P httpd_setrlimit=1
setsebool -P httpd_execmem on
semanage fcontext -a -t httpd_log_t "/var/log/fts3rest(/.*)?"
restorecon -R /var/log/fts3rest
fi

%preun selinux
if [ "$1" -eq "0" ] ; then
semanage port -d -t http_port_t -p tcp 8446
setsebool -P httpd_can_network_connect off
setsebool -P httpd_execmem off
fi

%files
%license LICENSE
%config(noreplace) %{_sysconfdir}/httpd/conf.d/fts3rest.conf
%config(noreplace) %{_sysconfdir}/fts3/ftsrestconfig
%config(noreplace) %{_sysconfdir}/logrotate.d/fts-rest
%{python3_sitelib}/fts3rest/
%attr(0755,fts3,fts3) /var/log/fts3rest
%{_libexecdir}/fts3rest

%files selinux

%changelog
* Thu Oct 15 2020 Carles Garcia Cabot <carles.garcia.cabot@cern.ch> - 1.0
- First production-grade release
* Tue Oct 13 2020 Carles Garcia Cabot <carles.garcia.cabot@cern.ch> - 0.2
- Pre-release improvements
* Tue Oct 13 2020 Carles Garcia Cabot <carles.garcia.cabot@cern.ch> - 0.1-2
- Set SELinux httpd_execmem on
* Tue May 19 2020 Carles Garcia Cabot <carles.garcia.cabot@cern.ch> - 0.1-1
- First server package release
