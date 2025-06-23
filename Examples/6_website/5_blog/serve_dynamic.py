#!/usr/bin/env python3

from httk.httkweb import serve

serve("src", port=8080, config="config_dynamic")
