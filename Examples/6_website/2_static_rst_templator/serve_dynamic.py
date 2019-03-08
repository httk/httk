#!/usr/bin/env python

from httk.httkweb import serve

serve("src", port=8080, config="config_dynamic")
