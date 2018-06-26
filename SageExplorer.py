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
from ipywidgets import Layout, VBox, HBox, Text, Label, HTML, Select, Textarea, Accordion, Tab, Button
import traitlets
from inspect import getdoc, getsource, getmembers, ismethod, isbuiltin, getargspec, getmro
from sage.combinat.rooted_tree import LabelledRootedTree

cell_layout = Layout(width='3em',height='2em', margin='0',padding='0')
box_layout = Layout()
css = HTML("<style></style>")
try:
    display(css)
except:
    pass # We are not in a notebook


def to_html(s):
    r"""Display nicely formatted HTML string
    INPUT: string s
    OUPUT: string
    """
    from sage.misc.sphinxify import sphinxify
    return sphinxify(s)

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
    return LabelledRootedTree([class_hierarchy(b) for b in c.__bases__], label=c)

def method_origin(obj, name):
    """Return class where method 'name' is actually defined"""
    c0 = obj.__class__
    ct = class_hierarchy(c0)
    traversal = ct.pre_order_traversal_iter()
    ret = c0
    while 1:
        next = traversal.next()
        if not next:
            break
        c = next.label()
        if c == c0:
            continue
        if not name in [x[0] for x in getmembers(c)]:
            continue
        for x in getmembers(c):
            if x[0] == name:
                if x[1] == getattr(c0, name):
                    ret = c
    return ret

def method_origins(obj, names):
    """Return class where methods in list 'names' are actually defined
    INPUT: object 'obj', list of method names
    """
    c0 = obj.__class__
    ct = class_hierarchy(c0)
    traversal = ct.pre_order_traversal_iter()
    # Initialisation
    ret = {}
    for name in names:
        ret[name] = c0
    while 1:
        next = traversal.next()
        if not next:
            break
        c = next.label()
        if c == c0:
            continue
        for name in names:
            if not name in [x[0] for x in getmembers(c)]:
                continue
            for x in getmembers(c):
                if x[0] == name:
                    if x[1] == getattr(c0, name):
                        ret[name] = c
    return ret


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
        origins = method_origins(self.obj, [x[0] for x in self.members])
        bases = []
        basemembers = {}
        print obj.__class__
        for c in getmro(obj.__class__):
            bases.append(c)
            basemembers[c] = []
        for name in origins:
            basemembers[origins[name]].append(name)
        for c in basemembers:
            if not basemembers[c]:
                bases.remove(c)
            else:
                print c, len(basemembers[c])
        self.attributes = [x for x in self.members if not ismethod(x[1]) and not isbuiltin(x[1])]
        self.methods = [x for x in self.members if ismethod(x[1])]
        self.builtins = [x for x in self.members if isbuiltin(x[1])]
        menus = []
        for i in range(len(bases)):
            c = bases[i]
            menus.append(Select(rows=12, options = [("{c}:".format(c=c), None)] + [x for x in self.methods if x[0] in basemembers[c]]))
        menus.append(Select(rows=12, options = [('Builtins:', None)] + self.builtins))
        self.menus = Accordion(menus)
        for i in range(len(bases)):
            c = bases[i]
            self.menus.set_title(i, str(c))
        self.menus.set_title(len(bases), 'Builtins')
        self.title = Label(str(obj.parent()))
        self.visual = Textarea(obj._repr_diagram())
        self.top = HBox([self.title, self.visual])
        self.inputs = HBox()
        self.gobutton = Button(description='Run!', tooltip='Run the function or method, with specified arguments')
        self.output = HTML()
        self.worktab = VBox((self.inputs, self.gobutton, self.output))
        self.doctab = HTML()
        self.main = Tab((self.worktab, self.doctab))
        self.main.set_title(0, 'Main')
        self.main.set_title(1, 'Help')
        self.bottom = HBox((self.menus, self.main))
        self.children = (self.top, self.bottom)
        self.compute()

    def compute(self):
        """Get some attributes, depending on the object
        Create links between menus and output tabs"""
        # FIXME attributes
        # FIXME compute list of methods here
        def menu_on_change(change):
            selected_func = change.new
            self.doctab.value = to_html(selected_func.__doc__)
            inputs = []
            for argname in getargspec(selected_func).args:
                if argname in ['self']:
                    continue
                inputs.append(Text(placeholder=argname))
            self.inputs.children = inputs
        for menu in self.menus.children:
            menu.observe(menu_on_change, names='value')

    def get_object(self):
        return self.obj

    def set_object(self, obj):
        self.obj = obj
        self.compute()
