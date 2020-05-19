%{!?python_sitelib: %global python_sitelib %(%{__python} -c "from distutils.sysconfig import get_python_lib; print (get_python_lib())")}
%{!?python_sitearch: %global python_sitearch %(%{__python} -c "from distutils.sysconfig import get_python_lib; print (get_python_lib(1))")}

%{!?nosetest_path: %global nosetest_path "/tmp"}

Name:           fts-rest
Version:        3.10.0
Release:        1%{?dist}
BuildArch:      noarch
Summary:        FTS3 Rest Interface
Group:          Applications/Internet
License:        ASL 2.0
URL:            http://fts3-service.web.cern.ch/

Source0:        %{name}-%{version}.tar.gz

BuildRequires:  gfal2-python
BuildRequires:  gfal2-plugin-mock
BuildRequires:  cmake
BuildRequires:  python-jsonschema

BuildRequires:  python-dateutil
BuildRequires:  python-pylons
BuildRequires:  m2crypto
BuildRequires:  python-mock
BuildRequires:  python-m2ext
BuildRequires:  python-sqlalchemy
BuildRequires:  python-requests
BuildRequires:  python-dirq
BuildRequires:  python-jwcrypto
BuildRequires:  python-jwt
BuildRequires:  python-oic
BuildRequires:  MySQL-python

Requires:       gridsite%{?_isa} >= 1.7
Requires:       httpd%{?_isa}
Requires:       mod_wsgi
Requires:       python-fts = %{version}-%{release}
Requires:       gfal2-python%{?_isa}
%description
This package provides the FTS3 REST interface

%if %{?rhel}%{!?rhel:0} >= 7
%package firewalld
Summary: FTS3 Rest Firewalld
Group: Applications/Internet

Requires:  firewalld-filesystem

%description firewalld
FTS3 Rest firewalld.
%endif


%package cli
Summary:        FTS3 Rest Interface CLI
Group:          Applications/Internet

Requires:       python-fts = %{version}-%{release}
Requires:       python-m2ext

%description cli
Command line utilities for the FTS3 REST interface

%package selinux
Summary:        SELinux support for fts-rest
Group:          Applications/Internet

Requires:       %{name} = %{version}-%{release}

%description selinux
SELinux support for fts-rest


%post
/sbin/service httpd condrestart >/dev/null 2>&1 || :
if [ "$1" -eq "2" ]; then # Upgrade
    # 3.5.1 needs owner to be fts3, since fts3rest runs as fts3
    chown fts3.fts3 /var/log/fts3rest
    chown fts3.fts3 /var/log/fts3rest/fts3rest.log || true
fi

%postun
if [ "$1" -eq "0" ] ; then
    /sbin/service httpd condrestart >/dev/null 2>&1 || :
fi

%post selinux
if [ "$1" -le "1" ] ; then # First install
semanage port -a -t http_port_t -p tcp 8446
setsebool -P httpd_can_network_connect=1
setsebool -P httpd_setrlimit=1
semanage fcontext -a -t httpd_log_t "/var/log/fts3rest(/.*)?"
restorecon -R /var/log/fts3rest/
fi

%preun selinux
if [ "$1" -lt "1" ] ; then # Final removal
semanage port -d -t http_port_t -p tcp 8446
setsebool -P httpd_can_network_connect=0
setsebool -P httpd_setrlimit=0
fi

%prep
%setup -q

%build
# Make sure the version in the spec file and the version used
# for building matches
fts_api_ver=`awk 'match($0, /^API_VERSION = dict\(major=([0-9]+), minor=([0-9]+), patch=([0-9]+)\)/, m) {print m[1]"."m[2]"."m[3]; }' src/fts3rest/fts3rest/controllers/api.py`
fts_spec_ver=`expr "%{version}" : '\([0-9]*\\.[0-9]*\\.[0-9]*\)'`
if [ "$fts_api_ver" != "$fts_spec_ver" ]; then
    echo "The version in the spec file does not match the api.py version!"
    echo "$fts_api_ver != %{version}"
    exit 1
fi

%cmake . -DCMAKE_INSTALL_PREFIX=/ -DPYTHON_SITE_PACKAGES=%{python_sitelib}

make %{?_smp_mflags}

%check
pushd src/fts3rest
PYTHONPATH=../ nosetests --with-xunit --xunit-file=%{?nosetest_path}/nosetests.xml --no-skip
popd

%install
mkdir -p %{buildroot}
make install DESTDIR=%{buildroot}
mkdir -p %{buildroot}/%{_var}/cache/fts3rest/
mkdir -p %{buildroot}/%{_var}/log/fts3rest/


cp --preserve=timestamps -r src/fts3 %{buildroot}/%{python_sitelib}
cat > %{buildroot}/%{python_sitelib}/fts3.egg-info <<EOF
Metadata-Version: 1.0
Name: fts3
Version: %{version}
Summary: FTS3 Python Libraries.
Home-page: http://fts3-service.web.cern.ch
Author: FTS Developers
Author-email: fts-devel@cern.ch
License: Apache2
EOF

%files 

%dir %{python_sitelib}/fts3rest/

%{python_sitelib}/fts3rest.egg-info/*

%{python_sitelib}/fts3rest/__init__.py*
%{python_sitelib}/fts3rest/websetup.py*

%{python_sitelib}/fts3rest/config/*.py*
%{python_sitelib}/fts3rest/config/routing/__init__.py*
%{python_sitelib}/fts3rest/config/routing/base.py*

%{python_sitelib}/fts3rest/controllers/api.py*
%{python_sitelib}/fts3rest/controllers/archive.py*
%{python_sitelib}/fts3rest/controllers/autocomplete.py*
%{python_sitelib}/fts3rest/controllers/banning.py*
%{python_sitelib}/fts3rest/controllers/config/*.py*
%{python_sitelib}/fts3rest/controllers/datamanagement.py*
%{python_sitelib}/fts3rest/controllers/delegation.py*
%{python_sitelib}/fts3rest/controllers/error.py*
%{python_sitelib}/fts3rest/controllers/__init__.py*
%{python_sitelib}/fts3rest/controllers/files.py*
%{python_sitelib}/fts3rest/controllers/jobs.py*
%{python_sitelib}/fts3rest/controllers/optimizer.py*
%{python_sitelib}/fts3rest/controllers/serverstatus.py*

%{python_sitelib}/fts3rest/lib/api/
%{python_sitelib}/fts3rest/lib/app_globals.py*
%{python_sitelib}/fts3rest/lib/base.py*
%{python_sitelib}/fts3rest/lib/openidconnect.py*
%{python_sitelib}/fts3rest/lib/gfal2_wrapper.py*
%{python_sitelib}/fts3rest/lib/heartbeat.py*
%{python_sitelib}/fts3rest/lib/IAMTokenRefresher.py*
%{python_sitelib}/fts3rest/lib/helpers/
%{python_sitelib}/fts3rest/lib/http_exceptions.py*
%{python_sitelib}/fts3rest/lib/__init__.py*
%{python_sitelib}/fts3rest/lib/JobBuilder.py*
%{python_sitelib}/fts3rest/lib/middleware/*.py*
%{python_sitelib}/fts3rest/lib/middleware/fts3auth/*.py*
%{python_sitelib}/fts3rest/lib/middleware/fts3auth/methods/__init__.py*
%{python_sitelib}/fts3rest/lib/middleware/fts3auth/methods/ssl.py*
%{python_sitelib}/fts3rest/lib/scheduler/schd.py*
%{python_sitelib}/fts3rest/lib/scheduler/db.py*
%{python_sitelib}/fts3rest/lib/scheduler/Cache.py*
%{python_sitelib}/fts3rest/lib/scheduler/__init__.py*

%{python_sitelib}/fts3rest/model/

%{python_sitelib}/fts3rest/public/
%{python_sitelib}/fts3rest/templates/delegation.html
%{python_sitelib}/fts3rest/templates/config/

%{_libexecdir}/fts3
%config(noreplace) %{_sysconfdir}/fts3/fts3rest.ini
%config(noreplace) %{_sysconfdir}/httpd/conf.d/fts3rest.conf
%config(noreplace) %{_sysconfdir}/logrotate.d/fts-rest
%config(noreplace) %{_sysconfdir}/cron.d/fts-rest-graceful.cron
%dir %attr(0755,fts3,fts3) %{_var}/cache/fts3rest
%dir %attr(0755,fts3,fts3) %{_var}/log/fts3rest
%doc docs/README.md
%doc docs/install.md
%doc docs/api.md

%files firewalld
%config(noreplace) %{_prefix}/lib/firewalld/services/fts3rest.xml


%files cli
%{_bindir}/fts-rest-*
%config(noreplace) %{_sysconfdir}/fts3/fts3client.cfg
%{_mandir}/man1/fts-rest*

%files selinux



%changelog
* Mon Aug 19 2019 Andrea Manzi <amanzi@cern.ch> - 3.9.2-1
- New bugfix release
