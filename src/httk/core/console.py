import sys

def cout(*args):
    sys.stdout.write(' '.join(map(str, args))+'\n')

def cerr(*args):
    sys.stdout.write(' '.join(map(str, args))+'\n')    

#def err(*args):
#    sys.stderr.write(' '.join(map(str, args))+'\n')



