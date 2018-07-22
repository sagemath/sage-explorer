"""
Defining standard widgets for some Sage classes
"""

from sage.all import *

# Workaround:
# Tableau is lazy imported by default, and lazy import objects don't yet have a
# __setattr__ method (see #25898). This forces a normal import.

from .sage_explorer import PlotWidget

sage.schemes.curves.curve.Curve_generic._widget_ = PlotWidget

# Crystals can be slow / infinite to plot; one heuristic would be to plot the
# crystal on its first 10/20 elements.
# For now it would be best to only set this for Crystals.Finite, but it does
# not yet have a ParentMethods
Crystals.ParentMethods._widget_ = PlotWidget
Posets().Finite().ParentMethods._widget_ = PlotWidget
sage.graphs.generic_graph.GenericGraph._widget_ = PlotWidget

# The decision for whether to display the graph or not is duplicating what's
# already done in the Jupyter notebook REPL; this logic should presumably be
# shared.


# Additional widgets if sage-combinat-widgets is installed
try:
    import sage_combinat_widgets
except:
    pass
else:
    # TODO: make the various widgets below into BindableClass as for
    # PlotWidget, to avoid the need for the wrapper method below
    from sage.combinat.tableau import Tableau, StandardTableau, SemistandardTableau
    Tableau._widget_ = lambda self: sage_combinat_widgets.TableauWidget(self)
    SemistandardTableau._widget_ = lambda self: sage_combinat_widgets.SemistandardTableauWidget(self)
    StandardTableau._widget_ = lambda self: sage_combinat_widgets.StandardTableauWidget(self)
    Partition._widget_ = lambda self: sage_combinat_widgets.PartitionWidget(self)
    # Not yet in sage-combinat-widgets
    #graphs.GridGraph._widget_ = sage_combinat_widgets.DominosWidget
    #graphs.AztecDiamondGraph._widget_ = sage_combinat_widgets.DominosWidget
