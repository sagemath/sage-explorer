# # Patch the Sage library
# import sys, logging
# from recursive_monkey_patch import monkey_patch
# sage_explorer = sys.modules[__name__]
# import misc
# import sage
# monkey_patch(sage_explorer.misc, sage.misc, log_level=logging.INFO)

from .sage_explorer import SageExplorer, SageExplorer as explore
try:
    import _widgets
except:
    pass
