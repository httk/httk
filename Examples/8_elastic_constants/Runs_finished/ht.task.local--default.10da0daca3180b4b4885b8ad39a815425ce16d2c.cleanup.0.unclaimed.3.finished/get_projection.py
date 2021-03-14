from utilities import elastic_config

_, _, _, project = elastic_config()
if project:
    print(1)
else:
    print(0)
