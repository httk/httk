#!/usr/bin/env python

'''
This file serves httkweb via WSGI.

To try out WSGI with Python's built-in WSGI-server meant for testing, use 'serve_wsgi' instead.

To serve via apache:

- Make sure to have mod-wsgi installed (e.g., `apt install libapache2-mod-wsgi` on Debian/Ubuntu; `yum install mod_wsgi` on RedHat, Fedora, OpenSUSE, etc., and run `a2enmod wsgi`.)

- Copy the httkweb setup into e.g. /var/www/optimade/

- Setup apache with a VirtualHost looking something like this:

```
Listen 8080
<VirtualHost *:8080>
    ServerName localhost

    WSGIDaemonProcess httkwebsite processes=4 threads=1
    WSGIScriptAlias / /var/www/optimade/serve.wsgi

    <Directory /var/www/optimade/public>
        WSGIProcessGroup httkweb
        WSGIApplicationGroup %{GLOBAL}
        Order deny,allow
        Allow from all
    </Directory>
</VirtualHost>
```
- (Re)start apache2.

Note:
- Parallelism is done here over processes instead of threads.
The Python interpreter can only execute on one thread at a time
due to a feature called 'GIL', and it is also very difficult to
know if Python library code is thread-safe or not. Threads can
still be beneficial in some cases, e.g., when most time is spent
waiting for heavy IO load, but without serious benchmarking it
is safer to do parallelism over processes than threads.)
'''

from httk.httkweb import create_wsgi_application
application = create_wsgi_application("src", port=8080, config="config_dynamic")
