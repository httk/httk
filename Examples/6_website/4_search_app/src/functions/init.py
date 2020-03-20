import httk, httk.db

def execute(global_data,**kargs):

    backend = httk.db.backend.Sqlite('../../../Tutorial/tutorial_data/tutorial.sqlite')
    store = httk.db.store.SqlStore(backend)

    global_data['store'] = store
    