FROM centos:7

RUN useradd fts
USER fts

RUN yum-config-manager --add-repo http://fts-repo.web.cern.ch/fts-repo/testing/el7/x86_64/ && \
    yum install epel-release && \
    yum install centos-release-scl && \
    yum install fts-rest-server && \
    yum clean all

EXPOSE 8446

ENTRYPOINT ["/usr/sbin/httpd", "-D", "FOREGROUND"]