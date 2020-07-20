FROM centos:7

RUN useradd fts
USER fts

RUN mkdir -p /usr/libexec/fts3rest
RUN mkdir -p /etc/fts3
RUN mkdir -p /etc/httpd/conf.d
RUN mkdir -p /var/log/fts3rest

COPY src/fts3rest/fts3rest /usr/lib/python3.6/site-packages/
COPY src/fts3rest/fts3rest.wsgi /usr/libexec/fts3rest
COPY src/fts3rest/fts3rest.conf /etc/httpd/conf.d
COPY src/fts3rest/fts3config /etc/httpd/conf.d

RUN yum-config-manager --enable centos-sclo-rh && \
    yum install httpd  httpd-devel rh-python36-mod_wsgi gfal2-python3  gfal2-plugin-mock \
        gridsite python3-devel openssl-devel swig gcc gcc-c++ make mysql-devel -y && \
    yum clean all

RUN pip install --upgrade pip &&  \
    pip install pip-tools && \
    pip-compile --upgrade requirements.in && \
    pip install -r requirements.txt

RUN systemctl httpd start



