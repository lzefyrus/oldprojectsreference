import os

from .common import *

# Environment
try:
    env = os.environ['GATEWAY_ENV']
except:
    env = 'dev'

# Load settings according to environment
if env == 'prod':
    from .prod import *

elif env == 'homol':
    from .homol import *

else:
    from .dev import *

