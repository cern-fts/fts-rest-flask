Name:           fts-rest-client
Version:        3.13.4
Release:        1%{?dist}
Summary:        File Transfer Service (FTS) -- Python3 Client and CLI

License:        ASL 2.0
URL:            https://fts.web.cern.ch/
# git clone --depth=1 --branch v3.13.4 https://gitlab.cern.ch/fts/fts-rest-flask.git fts-rest-client-3.13.4
# tar -C fts-rest-client-3.13.4/ -czf fts-rest-client-3.13.4.tar.gz src/cli src/fts3 LICENSE setup.py setup.cfg --transform "s|^|fts-rest-client-3.13.4/|" --show-transformed-names
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
* Tue Sep 03 2024 Mihai Patrascoiu <mihai.patrascoiu@cern.ch> - 3.13.4-1
- New server release (no client changes)

* Tue Aug 20 2024 Mihai Patrascoiu <mihai.patrascoiu@cern.ch> - 3.13.3-1
- "Disable clean-up" feature

* Thu Aug 01 2024 Mihai Patrascoiu <mihai.patrascoiu@cern.ch> - 3.13.2-1
- "Overwrite-when-only-on-disk" feature

* Tue Jun 04 2024 Mihai Patrascoiu <mihai.patrascoiu@cern.ch> - 3.13.1-1
- Backwards compatibility fix for "spacetoken" field removal in job submission

* Thu May 30 2024 Mihai Patrascoiu <mihai.patrascoiu@cern.ch> - 3.13.0-1
- Alma9 release

* Thu Oct 19 2023 Mihai Patrascoiu <mihai.patrascoiu@cern.ch> - 3.12.4-1
- Allow sending Scitag label for transfers

* Tue Aug 08 2023 Joao Lopes <joao.pedro.batista.lopes@cern.ch> - 3.12.3-1
- Use SHA256 to sign the delegated proxy

* Thu Mar 02 2023 Mihai Patrascoiu <mihai.patrascoiu@cern.ch> - 3.12.2-1
- Reduce required "python3-setuptools" version (bugzilla#2164054)
- Do not crash if "authorityKeyIdentifier" certificate extention is missing.
  OpenSSL3 handling changed and would now throw an error

* Fri Dec 02 2022 Mihai Patrascoiu <mihai.patrascoiu@cern.ch> - 3.12.1-1
- Addition of staging and archiving metadata

* Wed Mar 30 2022 Joao Lopes <joao.pedro.batista.lopes@cern.ch> - 3.12.0-1
- First official release

* Wed Jan 26 2022 Joao Lopes <joao.pedro.batista.lopes@cern.ch> - 3.12.0-rc1
- First official release candidate
