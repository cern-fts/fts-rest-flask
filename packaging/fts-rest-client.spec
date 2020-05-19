Name:           fts-rest-client
Version:        0.1
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
%py3_install

%files
%license LICENSE
%{python3_sitelib}/fts3/
%{python3_sitelib}/fts*-*.egg-info/
%{_bindir}/fts-rest-*

%changelog
* Mon May 18 2020 Carles Garcia Cabot <carles.garcia.cabot@cern.ch> - 0.1-1
- First package release