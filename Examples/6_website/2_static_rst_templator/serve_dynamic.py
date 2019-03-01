#!/usr/bin/env python

import os, shutil, sys

import httk 
#!/usr/bin/env python

from httk.httkweb.serve import serve

serve("src", port=8080, config="config_dynamic")
