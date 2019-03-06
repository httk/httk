#!/usr/bin/env python
import httk, httk.db
from httk.httkweb.app_qt5 import run_app

backend = httk.db.backend.Sqlite('../../../Tutorial/tutorial_data/tutorial.sqlite')
store = httk.db.store.SqlStore(backend)

run_app("src",global_data={'store':store})
