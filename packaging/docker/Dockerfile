#
# FTS-REST-Server Docker file
#

FROM centos:7
LABEL maintainer="FTS Team, fts-support@cern.ch, CERN 2022"

# Add EPEL repos
ADD https://linuxsoft.cern.ch/epel/epel-release-latest-7.noarch.rpm /tmp/epel-release-7.noarch.rpm
RUN yum localinstall /tmp/epel-release-7.noarch.rpm -y \
        && /usr/bin/yum --enablerepo=*-testing clean all \
        && rm /tmp/epel-release-7.noarch.rpm \
        && rm -rf /var/cache/yum

# Add FTS repo
ARG ftsrepo=https://fts-repo.web.cern.ch/fts-repo/fts3-continuous-el7.repo
ADD $ftsrepo /etc/yum.repos.d/fts.repo

# Add DMC repo
ARG dmcrepo=https://dmc-repo.web.cern.ch/dmc-repo/dmc-ci-el7.repo
ADD $dmcrepo /etc/yum.repos.d/dmc.repo
RUN yum clean all

# Enable Centos Software Collections repository
# Enable Centos Software Collections repository
RUN yum install -y centos-release-scl
RUN yum clean metadata

# Install FTS-REST-Server packages
RUN yum install -y fts-rest-server fts-rest-server-selinux

# Install VOMS packages
RUN yum install -y voms-config-wlcg voms-config-vo-dteam

# Expose ports
EXPOSE 8446

CMD ["/usr/sbin/apachectl", "-DFOREGROUND"]