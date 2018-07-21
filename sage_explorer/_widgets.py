"""Defining standard widgets for some Sage classes"""

from sage.all import *
try:
    import sage_combinat_widgets
except:
    pass

sage.schemes.curves.curve.Curve_generic._widget_ = 'PlotWidget'
Crystals()._widget_ = 'PlotWidget'
Tableau._widget_ = 'sage_combinat_widgets.TableauWidget'
SemistandardTableau._widget_ = 'sage_combinat_widgets.SemistandardTableauWidget'
StandardTableau._widget_ = 'sage_combinat_widgets.StandardTableauWidget'
Partition._widget_ = 'sage_combinat_widgets.PartitionWidget'
graphs.GridGraph._widget_ = 'sage_combinat_widgets.DominosWidget'
graphs.AztecDiamondGraph._widget_ = 'sage_combinat_widgets.DominosWidget'
