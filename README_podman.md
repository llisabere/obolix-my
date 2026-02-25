
# Usage


Create a `last_backup` directory with last LDAP dumps, certificates and [obol.conf](https://github.com/clustervision/obol/blob/main/obol.conf) file to connect to the LDAP.

`last_backup` structure hierarchy:

```bash
tree last_backup
```

```
last_backup
├── config.ldif
├── data.ldif
├── obol.conf
└── ssl
    ├── slapdcert.pem
    ├── slapdkey.pem
    └── slapd.pem

2 directories, 6 files
```

> Note: usually, you can generate ldif backups file from a directory with:
  `for i in {0..2}; do /usr/sbin/slapcat -n ${i} -l /var/backups/${_DATE}_ldap_base_${i}.ldif; done`
  `${_DATE}_ldap_base_0.ldif` should be your config file, while other databases are data databases.

Then, we can modify obol.conf file to be able to connect to the container LDAP's instance:

```bash
cp last_backup/obol.conf last_backup/obol.conf.orig
sed -i "s/localhost/deb-openldap/g" last_backup/obol.conf
```

If you want to change this default container name (here `deb-openldap`), then please don't forget to edit the Dockerfile accordingly.

## Podman


We are using podman in order to operate without root permissions locally, and we will use the Dockerfile in that same folder.

```bash
podman build -f Dockerfile -t io-ldap_ct
podman run -di --name deb-openldap --replace --volume ./last_backup:/opt/ldap-restore io-ldap_ct
podman exec deb-openldap restore-ldap.sh
```

Restoration can be quite long, depending on you LDAP directory size.

You can follow how it goes with:

```bash
watch podman top deb-openldap
```

When, it is over, in another terminal:

```bash
podman exec deb-openldap start-ldap.sh
```

You can now use obol commands:

```bash
podman exec deb-openldap obol user list
```

Other useful podman commands:

```bash
# for debugging
podman exec -ti deb-openldap /bin/bash
# for any launching issue
podman logs deb-openldap

# to stop it
podman stop deb-openldap
podman rm deb-openldap

# check with:
podman ps

# to clean image locally
podman rmi io-ldap_ct
```


To launch it without the need to build it again:

```bash
podman start deb-openldap 
podman exec deb-openldap start-ldap.sh
```
