Name:           fts-rest-client
Version:        1.0
Release:        1%{?dist}
Summary:        File Transfer Service (FTS) -- Python3 Client and CLI

License:        ASL 2.0
URL:            https://fts.web.cern.ch/
Source0:        %{name}-%{version}.tar.gz

BuildRequires:  python3
Requires:       python3
Requires:       python36-m2crypto
Requires:       python36-requests

BuildArch:      noarch

%description
File Transfer Service (FTS) -- Python3 Client and CLI

%prep
%setup -q

%build
%py3_build

%install
mkdir -p %{buildroot}%{_sysconfdir}/fts3
cp src/cli/fts3client.cfg %{buildroot}%{_sysconfdir}/fts3
%py3_install


%files
%license LICENSE
%{python3_sitelib}/fts3/
%{python3_sitelib}/fts*-*.egg-info/
%{_bindir}/fts-rest-*
%config(noreplace) %{_sysconfdir}/fts3/fts3client.cfg

%changelog
* Tue Oct 13 2020 Carles Garcia Cabot <carles.garcia.cabot@cern.ch> - 0.2
- Pre-release improvements
* Mon May 18 2020 Carles Garcia Cabot <carles.garcia.cabot@cern.ch> - 0.1-1
- First package release