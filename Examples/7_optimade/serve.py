#!/usr/bin/env python

import httk, httk.db, httk.optimade

backend = httk.db.backend.Sqlite('../../Tutorial/tutorial_data/tutorial.sqlite')
store = httk.db.store.SqlStore(backend)

config = {
  "links": [
    {
        "id": "index",
        "name": "omdb index",
        "description": "Index for omdb's OPTIMADE databases",
        "base_url": "https://optimade-index.openmaterialsdb.se",
        "homepage": "http://openmaterialsdb.se",
        "link_type": "root"
    },
  ]
}

httk.optimade.serve(store, config, port=8080)
