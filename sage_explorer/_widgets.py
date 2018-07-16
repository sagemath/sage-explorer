"""Defining standard widgets for some Sage classes"""

from sage.all import *
try:
    from sage_combinat_widgets import *
except:
    pass

sage.schemes.curves.curve.Curve_generic._widget_ = 'PlotWidget'
Tableau._widget_ = 'sage_combinat_widgets.TableauWidget'
SemistandardTableau._widget_ = 'sage-combinat-widgets.SemistandardTableauWidget'
StandardTableau._widget_ = 'sage-combinat-widgets.StandardTableauWidget'
Partition._widget_ = 'sage-combinat-widgets.PartitionWidget'
graphs.GridGraph._widget_ = 'sage-combinat-widgets.DominosWidget'
graphs.AztecDiamondGraph._widget_ = 'sage-combinat-widgets.DominosWidget'
