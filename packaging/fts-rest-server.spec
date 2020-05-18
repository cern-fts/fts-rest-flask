Name:           fts-rest-server
Version:        0.1
Release:        1%{?dist}
Summary:        File Transfer Service (FTS) -- Python3 HTTP API Server

License:        ASL 2.0
URL:            https://fts.web.cern.ch/
Source0:        %{name}-%{version}.tar.gz

BuildRequires:  python3
Requires:       python3
Requires:       python3-devel # from mysqlclient
Requires:       mysql-devel # from mysqlclient
Requires:       python36-m2crypto
Requires:       python36-requests
Requires:       python36-flask
Requires:       python36-sqlalchemy
Requires:       python36-dateutil
Requires:       python-mako ###### does it work with Python3?
Requires:       python-dirq ###### does it work with Python3?
Requires:       mysqlclient ###### not in repos
Requires:       PyJWT ###### not in repos
Requires:       jwcrypto ###### not in repos
Requires:       oic ###### not in repos

BuildArch:      noarch

%description
File Transfer Service (FTS) -- Python3 HTTP API Server

%prep
%setup -q

%build
%py3_build

%install
%py3_install

%files
%license LICENSE
%{python3_sitelib}/fts3/
%{python3_sitelib}/fts*-*.egg-info/
%{_bindir}/fts-rest-*

%changelog
* Mon May 18 2020 Carles Garcia Cabot <carles.garcia.cabot@cern.ch> - 0.1-1
- First server package release