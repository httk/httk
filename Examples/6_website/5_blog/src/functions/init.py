import os

def execute(global_data,**kargs):

    prefix = 'src/content'
    filterlist = ['.md','.rst','.html']
    path = 'blogposts'

    # Chicken-or-egg problem of having to partially render blog posts to sort them, but their renders refer to the other blogposts
    global_data['blogposts'] = []
    global_data['blogposts_latest'] = []

    def listdirsorted(path):
        return [x[0] for x in sorted([(fn, global_data['pages'](os.path.join(path,fn),'date')) for fn in os.listdir(os.path.join(prefix,path))], key = lambda x: x[1])]

    global_data['blogposts'] = [os.path.join(path, f) for f in listdirsorted(path) if os.path.isfile(os.path.join(prefix, path, f)) and any([f.endswith(t) for t in filterlist])]

    global_data['blogposts_latest'] = global_data['blogposts'][:5]
