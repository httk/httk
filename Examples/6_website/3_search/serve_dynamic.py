#!/usr/bin/env python

import httk, httk.db
from httk.httkweb.serve import serve

backend = httk.db.backend.Sqlite('../../../Tutorial/tutorial_data/tutorial.sqlite')
store = httk.db.store.SqlStore(backend)

serve("src", port=8080, global_data={'store':store, 'urls_without_ext':True})
