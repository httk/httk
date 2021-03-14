import sys
from utilities import elastic_config

dist_ind = int(sys.argv[1]) - 1
_, delta, _, _ = elastic_config()
print(len(delta[dist_ind]))
