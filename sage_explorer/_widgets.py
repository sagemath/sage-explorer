"""
Defining standard widgets for some Sage classes
"""

import traitlets
from ipywidgets import Box, HTML
from sage.misc.bindable_class import BindableClass
from sage.all import SAGE_TMP, SageObject, plot, plot3d
import sage.all
from os.path import join as path_join

# Workaround:
# Tableau is lazy imported by default, and lazy import objects don't yet have a
# __setattr__ method (see #25898). This forces a normal import.

import sage.misc.classcall_metaclass
from six import add_metaclass
class MetaHasTraitsClasscallMetaclass (traitlets.traitlets.MetaHasTraits, sage.misc.classcall_metaclass.ClasscallMetaclass):
    pass
@add_metaclass(MetaHasTraitsClasscallMetaclass)
class BindableWidgetClass(BindableClass):
    pass

class PlotWidget(Box, BindableWidgetClass):
    r"""A widget for plotting any plottable object"""
    value = traitlets.Instance(SageObject)
    plot = traitlets.Instance(SageObject)
    name = traitlets.Unicode()

    def __init__(self, obj, figsize=4, name=None):
        r"""
        Which is the specialized widget class name for viewing this object (if any)

        TESTS::

            sage: from sage_explorer._widgets import PlotWidget
            sage: w = PlotWidget(sin)
            sage: w.name
            'sin'
            sage: len(w.children)
            1
            sage: w = PlotWidget(list(cremona_curves(srange(35)))[0])
            sage: w.name
            'Elliptic Curve defined by y^2 + y = x^3 - x^2 - 10*x - 20 over Rational Field'
            sage: x, y = var('x y')
            sage: g(x,y) = x**2 + y**2
            sage: w = PlotWidget(g)
            sage: w.name
            '(x, y) |--> x^2 + y^2'
        """
        super(PlotWidget, self).__init__()
        self.value = obj
        if not name:
            name = repr(obj)
        self.name = name
        svgfilename = path_join(SAGE_TMP, '%s.svg' % name)
        pngfilename = path_join('.', '%s.png' % name)
        if hasattr(obj, 'number_of_arguments') and obj.number_of_arguments() == 2:
            if type(figsize) == type(()):
                if len(figsize) == 2:
                    urange, vrange = figsize
                elif len(figsize) == 1:
                    urange, vrange = figsize, figsize
            elif str(figsize).isnumeric():
                urange = vrange = (-float(figsize)/2, float(figsize)/2)
            self.plot = plot3d(obj, urange, vrange)
        else:
            try:
                self.plot = plot(obj, figsize=figsize)
            except:
                try:
                    self.plot = obj.plot()
                except:
                    self.plot = plot(obj)
        try:
            self.plot.save(svgfilename)
            self.children = [HTML(open(svgfilename, 'rb').read())]
        except:
            self.plot.save(pngfilename)
            self.children = [HTML('<img title="' + self.name  + ' Plot" src="' + pngfilename + '">')]

sage.schemes.curves.curve.Curve_generic._widget_ = PlotWidget

# Crystals can be slow / infinite to plot; one heuristic would be to plot the
# crystal on its first 10/20 elements.
# For now it would be best to only set this for Crystals.Finite, but it does
# not yet have a ParentMethods
sage.categories.crystals.Crystals.ParentMethods._widget_ = PlotWidget
sage.combinat.posets.poset_examples.Posets().Finite().ParentMethods._widget_ = PlotWidget
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
    sage.combinat.tableau.Tableau._widget_ = sage_combinat_widgets.GridViewWidget
    sage.combinat.skew_tableau.SkewTableau._widget_ = sage_combinat_widgets.GridViewWidget
    sage.combinat.partition.Partition._widget_ = sage_combinat_widgets.grid_view_widget.PartitionGridViewWidget
    sage.combinat.skew_partition.SkewPartition._widget_ = sage_combinat_widgets.grid_view_widget.PartitionGridViewWidget
    #sage.graphs.graph.Graph._widget_ = sage_combinat_widgets.GridViewWidget # FIXME only GridGraph and AztecDiamondGraph
    #sage.graphs.AztecDiamondGraph._widget_ = sage_combinat_widgets.GridViewWidget
    sage.matrix.matrix2._widget_ = sage_combinat_widgets.GridViewWidget
