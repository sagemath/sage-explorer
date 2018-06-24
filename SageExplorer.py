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
from ipywidgets import Layout, VBox, HBox, Text, Label, HTML, Select, Textarea, Accordion, Tab
import traitlets
from inspect import getdoc, getmembers, ismethod, isbuiltin
from sage.combinat.rooted_tree import LabelledRootedTree

cell_layout = Layout(width='3em',height='2em', margin='0',padding='0')
box_layout = Layout()
css = HTML("<style></style>")
try:
    display(css)
except:
    pass # We are not in a notebook


def class_hierarchy(c):
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
    return LabelledRootedTree([ class_hierarchy(b) for b in c.__bases__], label=c)


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
        self.members = [x for x in getmembers(obj) if not x[0].startswith('_') and not 'deprecated' in str(type(x[1])).lower()]
        ct = class_hierarchy(obj.__class__)
        #print ct
        basemembers = {}
        globbasemembers = []
        traversal = ct.pre_order_traversal_iter()
        while 1:
            next = traversal.next()
            if not next:
                break
            c = next.label()
            basemembers[c] = []
            for m in self.members:
                if m[0] in [x[0] for x in getmembers(c)]:
                    basemembers[c].append(m)
                    if c != obj.__class__ and not m in globbasemembers:
                        globbasemembers.append(m)
        self.attributes = [x for x in self.members if not ismethod(x[1]) and not isbuiltin(x[1])]
        self.methods = [x for x in self.members if ismethod(x[1])]
        self.builtins = [x for x in self.members if isbuiltin(x[1])]
        menus = []
        menus.append(Select(rows=12, options = [('Object methods:', None)] + [x for x in self.methods if not x in globbasemembers]))
        menus.append(Select(rows=12, options = [('Parent methods:', None)] + [x for x in self.methods if x in globbasemembers]))
        menus.append(Select(rows=12, options = [('Builtins:', None)] + self.builtins))
        self.title = Label(str(obj.parent()))
        self.visual = Textarea(obj._repr_diagram())
        self.top = HBox([self.title, self.visual])
        self.menus = Accordion(menus)
        self.menus.set_title(0, 'Object methods')
        self.menus.set_title(1, 'Parent methods')
        self.menus.set_title(2, 'Builtins')
        self.outtab = VBox([Text(), HTML()])
        self.doctab = HTML()
        self.main = Tab((self.outtab, self.doctab))
        self.bottom = HBox([self.menus, self.main])
        self.children = [self.top, self.bottom]
        self.compute()

    def compute(self):
        """Get some attributes, depending on the object
        Create links between menus and output tabs"""
        # FIXME attributes
        def menu_on_change(change):
            self.doctab.value = change.new.__doc__
        for menu in self.menus.children:
            menu.observe(menu_on_change, names='value')

    def get_object(self):
        return self.obj

    def set_object(self, obj):
        self.obj = obj
        self.compute()
