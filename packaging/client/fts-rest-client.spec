Name:           fts-rest-client
Version:        3.12.0
Release:        1%{?dist}
Summary:        File Transfer Service (FTS) -- Python3 Client and CLI

License:        ASL 2.0
URL:            https://fts.web.cern.ch/
# git clone --depth=1 --branch v3.12.0-client https://gitlab.cern.ch/fts/fts-rest-flask.git fts-rest-client-3.12.0
# tar -C fts-rest-client-3.12.0/ -czf fts-rest-client-3.12.0.tar.gz src/cli src/fts3 LICENSE setup.py setup.cfg --transform "s|^|fts-rest-client-3.12.0/|" --show-transformed-names
Source0:        %{name}-%{version}.tar.gz

BuildRequires:  python3-devel
BuildRequires:  python3-setuptools
Requires:       python3
Requires:       python%{python3_pkgversion}-m2crypto
Requires:       python%{python3_pkgversion}-requests

# Replace previous FTS Python2 Client package
Provides:       python-fts = %{version}-%{release}
Provides:       fts-rest-cli = %{version}-%{release}
Obsoletes:      python-fts < 3.12.0
Obsoletes:      fts-rest-cli < 3.12.0

BuildArch:      noarch

%description
File Transfer Service (FTS) -- Python3 Client and CLI

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
* Wed Mar 30 2022 Joao Lopes <joao.pedro.batista.lopes@cern.ch> - 3.12.0-1
- First official release
* Wed Jan 26 2022 Joao Lopes <joao.pedro.batista.lopes@cern.ch> - 3.12.0-rc1
- First official release candidate
