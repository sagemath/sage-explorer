# -*- coding: utf-8 -*-
r"""
Sage Explorer in Jupyter Notebook

EXAMPLES ::
from SageExplorer import *
S = StandardTableaux(15)
t = S.random_element()
widget = SageExplorer(t)
display(t)

AUTHORS:
- Odile Bénassy, Nicolas Thiéry

"""
from ipywidgets import Layout, VBox, HBox, Text, Label, HTML, Select, Textarea
import traitlets
from inspect import getdoc, getmembers, getclasstree, ismethod

cell_layout = Layout(width='3em',height='2em', margin='0',padding='0')
box_layout = Layout()
css = HTML("<style></style>")
try:
    display(css)
except:
    pass # We are not in a notebook


def hierarchy(c):
    r"""Compute parental hierarchy tree for class c
    INPUT: class
    OUTPUT: LabelledRootedTree of its parents
    EXAMPLES::
    sage: var('X')
    sage: P = 2*X^2 + 3*X + 4
    sage: hierarchy(P.__class__)
    <type 'sage.symbolic.expression.Expression'>[<type 'sage.structure.element.CommutativeRingElement'>[<type 'sage.structure.element.RingElement'>[<type 'sage.structure.element.ModuleElement'>[<type 'sage.structure.element.Element'>[<type 'sage.structure.sage_object.SageObject'>[<type 'object'>[]]]]]]]
    sage: P = Partitions(7)[3]
    sage: hierarchy(P.__class__)
    <class 'sage.combinat.partition.Partitions_n_with_category.element_class'>[<class 'sage.combinat.partition.Partition'>[<class 'sage.combinat.combinat.CombinatorialElement'>[<class 'sage.combinat.combinat.CombinatorialObject'>[<type 'sage.structure.sage_object.SageObject'>[<type 'object'>[]]], <type 'sage.structure.element.Element'>[<type 'sage.structure.sage_object.SageObject'>[<type 'object'>[]]]]], <class 'sage.categories.finite_enumerated_sets.FiniteEnumeratedSets.element_class'>[<class 'sage.categories.enumerated_sets.EnumeratedSets.element_class'>[<class 'sage.categories.sets_cat.Sets.element_class'>[<class 'sage.categories.sets_with_partial_maps.SetsWithPartialMaps.element_class'>[<class 'sage.categories.objects.Objects.element_class'>[<type 'object'>[]]]]], <class 'sage.categories.finite_sets.FiniteSets.element_class'>[<class 'sage.categories.sets_cat.Sets.element_class'>[<class 'sage.categories.sets_with_partial_maps.SetsWithPartialMaps.element_class'>[<class 'sage.categories.objects.Objects.element_class'>[<type 'object'>[]]]]]]]
    """
    # return getclasstree(c)
    return LabelledRootedTree([ hierarchy(b) for b in c.__bases__], label=c)



class SageExplorer(VBox):
    """Sage Explorer in Jupyter Notebook"""

    def __init__(self, obj):
        """
        TESTS::

        sage: S = StandardTableaux(15)
        sage: t = S.random_element()
        sage: widget = SageExplorer(t)
        sage: widget.compute()
        """
        super(SageExplorer, self).__init__()
        self.obj = obj
        self.title = Label(str(type(obj)))
        self.visual = Textarea(obj._repr_diagram())
        self.top = HBox([self.title, self.visual])
        self.methods = Select(options = [('Object methods:', None)] + [x for x in getmembers(obj) if not x[0].startswith('_') and ismethod(x[1])])
        self.output = HTML(getdoc(obj))
        self.bottom = HBox([self.methods, self.output])
        self.children = [ self.top, self.bottom ]

    def compute(self):
        pass

    def get_object(self):
        return self.obj

    def set_object(self, obj):
        self.obj = obj
        self.compute()
