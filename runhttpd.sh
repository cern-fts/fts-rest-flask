#!/bin/bash
cp fts3rest/httpd_fts.conf /etc/httpd/conf.d
systemctl restart httpd
