FROM debian:12

RUN mkdir /opt/ldap-restore

ARG CT_NAME=deb-openldap

RUN apt-get -y update \
  && LC_ALL=C DEBIAN_FRONTEND=noninteractive \
  apt-get install -yqq slapd git ldap-utils vim ldapvi \
  python3 python3-ldap sssd sssd-tools \
  && apt-get clean

#RUN git clone https://github.com/clustervision/obol.git /opt/obol
RUN git clone https://forge.inrae.fr/isdm-meso/obolix.git /opt/obol

RUN printf "[sssd]\n\
config_file_version = 2\n\
domains = LDAP\n\
services = nss, pam\n\
\n\
[domain/LDAP]\n\
auth_provider = ldap\n\
cache_credentials = True\n\
chpass_provider = ldap\n\
enumerate = True\n\
id_provider = ldap\n\
ldap_enumeration_refresh_timeout = 10800\n\
ldap_schema = rfc2307bis\n\
ldap_search_base = dc=local\n\
ldap_tls_reqcert = allow\n\
ldap_uri = ldap://${CT_NAME}" > /etc/sssd/sssd.conf

RUN printf '#!/usr/bin/bash \n\
mkdir /var/lib/ldap 2>/dev/null \n\
rm -rf /etc/ldap/slapd.d/* /var/lib/ldap/* \n\
/usr/sbin/slapadd -F /etc/ldap/slapd.d -b cn=config -l /opt/ldap-restore/config.ldif \n\
/usr/sbin/slapadd -F /etc/ldap/slapd.d -b dc=local -l /opt/ldap-restore/data.ldif \n\
mkdir /etc/ldap/certs/ \n\
ln -sf /opt/ldap-restore/ssl /etc/ldap/certs/ssl \n\
mkdir /var/run/ldap 2>/dev/null \n\
chown -R openldap:openldap /etc/ldap/slapd.d \n\
chown -R openldap:openldap /var/lib/ldap \n\
chown -R openldap:openldap /var/run/ldap \n' > /usr/local/sbin/restore-ldap.sh

RUN printf "#!/usr/bin/bash\n\
ulimit -n 1024\n\
export FQDN=${CT_NAME}\n" > /usr/local/sbin/start-ldap.sh
RUN printf 'export HOST_PARAM="ldap://$FQDN:389"\n\
export LDAP_LOG_LEVEL=3\n\
exec /usr/sbin/slapd -h "$HOST_PARAM ldapi:///" -u openldap -g openldap -d "$LDAP_LOG_LEVEL" &\n\
exec /usr/sbin/sssd -D -c /etc/sssd/sssd.conf 2>&1 >> /var/log/sssd/sssd.log\n' >> /usr/local/sbin/start-ldap.sh

RUN ln -s  /opt/ldap-restore/obol.conf /etc/obol.conf
RUN ln -sf /opt/ldap-restore/obol.conf /opt/obol/obol.conf
RUN printf '#!/usr/bin/env bash\n\
python3 /opt/obol/main.py $@' > /usr/local/bin/obol

RUN echo "TLS_REQCERT never" >> /etc/ldap/ldap.conf

RUN chmod u+x /usr/local/sbin/restore-ldap.sh
RUN chmod u+x /usr/local/sbin/start-ldap.sh
RUN chmod u+x /usr/local/bin/obol
RUN chmod 600 /etc/sssd/sssd.conf

#CMD ["/bin/bash", "-c", "/usr/local/sbin/start-ldap.sh"]
