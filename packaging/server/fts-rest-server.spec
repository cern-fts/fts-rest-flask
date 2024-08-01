Name:           fts-rest-server
Version:        3.13.0
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
Requires:       gridsite
Requires:       gfal2-python3
Requires:       gfal2-plugin-mock
Requires:       python3-mod_wsgi
Requires:       python%{python3_pkgversion}-m2crypto
Requires:       python%{python3_pkgversion}-requests
Requires:       python%{python3_pkgversion}-flask
Requires:       python%{python3_pkgversion}-dateutil
Requires:       python%{python3_pkgversion}-jwt
Requires:       python%{python3_pkgversion}-typing-extensions
Requires:       python%{python3_pkgversion}-sqlalchemy >= 1.1.15
Requires:       python%{python3_pkgversion}-mysqlclient
Requires:       python%{python3_pkgversion}-jwcrypto
Requires:       python%{python3_pkgversion}-dirq
Requires:       python%{python3_pkgversion}-mako
### The following three packages are still not found in community repositories on RHEL9 and were build by us
### They follow the naming convention for python packages on RHEL9
Requires:       python%{python3_pkgversion}-pyjwkest = 1.4.2-1.el9.cern
Requires:       python%{python3_pkgversion}-beaker = 1.11.0-1.el9.cern
Requires:       python%{python3_pkgversion}-oic = 1.4.0-1.git64c5e3b.el9.cern

BuildArch:      noarch
Obsoletes:      fts-rest < 3.12.0

%description
File Transfer Service (FTS) -- Python3 HTTP API Server

%package selinux
Summary:        SELinux support for FTS-REST
Group:          Applications/Internet
Requires:       %{name} = %{version}-%{release}
Requires:       policycoreutils-python-utils
Obsoletes:      fts-rest-selinux < 3.12.0

%description selinux
SELinux support for the FTS HTTP API Server

%prep
%setup -q

%build
python3 -m compileall fts3rest/fts3rest

# Check https://docs.fedoraproject.org/en-US/packaging-guidelines/Python/
# Program files go in /usr/lib/python3.6/site-packages
# WSGI files go in /usr/libexec
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
cp fts3rest/fts3restconfig %{buildroot}%{_sysconfdir}/fts3
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
%config(noreplace) %{_sysconfdir}/fts3/fts3restconfig
%config(noreplace) %{_sysconfdir}/logrotate.d/fts-rest
%{python3_sitelib}/fts3rest/
%attr(0755,fts3,fts3) /var/log/fts3rest
%{_libexecdir}/fts3rest

%files selinux

%changelog
* Thu May 30 2024 Mihai Patrascoiu <mihai.patrascoiu@cern.ch> - 3.13.0
- Alma9 release

* Thu Oct 19 2023 Mihai Patrascoiu <mihai.patrascoiu@cern.ch> - 3.12.4
- Allow sending Scitag label for transfers

* Tue Aug 08 2023 Joao Lopes <joao.pedro.batista.lopes@cern.ch> - 3.12.3
- Disable deletion submissions via the FTS-REST
- Refuse FTS job submissions if archive/staging metadata exceeds configurable size
- Allow configuring the TPC role per Storage Endpoint
- Turn configurable eviction flag into skip-eviction

* Thu Mar 02 2023 Mihai Patrascoiu <mihai.patrascoiu@cern.ch> - 3.12.2-1
- Refactoring of job submission checks, especially for AutoSessionReuse mode
- Log time it takes to store submission into the database

* Fri Dec 02 2022 Mihai Patrascoiu <mihai.patrascoiu@cern.ch> - 3.12.1-1
- Introduce profiling logs for HTTP requests
- Introduce new "/admin/force-start" endpoint
- OAuth2 token-exchange workflow improvements

* Wed Jul 14 2021 Joao Lopes <joao.pedro.batista.lopes@cern.ch> - 3.12.0-1
- First production release of FTS-REST-FLASK (Python3)
- Compatibility with MySQL8.0
- Support for tape REST API
- OC11/GDPR compliance with regards to VO names
- OAuth2 token refactoring
- Full migration to Gitlab-CI
