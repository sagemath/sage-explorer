# # Patch the Sage library
# import sys, logging
# from recursive_monkey_patch import monkey_patch
# sage_explorer = sys.modules[__name__]
# import misc
# import sage
# monkey_patch(sage_explorer.misc, sage.misc, log_level=logging.INFO)

from .new_sage_explorer import NewSageExplorer, NewSageExplorer as explore
try:
    from ._widgets import *
except:
    pass
