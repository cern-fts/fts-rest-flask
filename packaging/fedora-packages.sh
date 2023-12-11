#!/usr/bin/env bash
set -e

if [[ -f /usr/bin/dnf ]]; then
  dnf install -y yum-utils dnf-plugins-core git rpm-build dnf-utils tree which
else
  yum install -y yum-utils git rpm-build tree which epel-rpm-macros
fi
