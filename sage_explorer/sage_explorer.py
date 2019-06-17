# -*- coding: utf-8 -*-
r"""
Sage Explorer in Jupyter Notebook

EXAMPLES ::
from sage.combinat.tableau import StandardTableaux
from SageExplorer import *
t = StandardTableaux(15).random_element()
widget = SageExplorer(t)
display(t)

AUTHORS:
- Odile Bénassy, Nicolas Thiéry

"""
import re
from ipywidgets import Layout, Box, VBox, HBox, Text, Label, HTML, Select, Textarea, Accordion, Tab, Button
from traitlets import Any
from inspect import getargspec, getmembers, getmro, isclass, isfunction, ismethod, ismethoddescriptor, isabstract
try: # Are we in a Sage environment?
    import sage.all
    from sage.misc.sageinspect import sage_getargspec as getargspec
    from sage.misc.sphinxify import sphinxify
except:
    pass
try: # Avoid python3 deprecation warning.
    from inspect import getfullargspec as getargspec
except:
    pass
try:
    from cysignals.alarm import alarm, cancel_alarm, AlarmInterrupt
except:
    AlarmInterrupt = None
import yaml, os, six, operator as OP
from IPython.core import display

# CSS
back_button_layout = Layout(width='7em')
justified_h_layout = Layout(justify_content='space-between')
main_h_layout = Layout(justify_content='flex-start')
css_lines = []
css_lines.append(".container {width:100% !important;}")
css_lines.append(".invisible {display: none; width: 0; height: 0}")
css_lines.append(".visible {display: table}")
css_lines.append(".title-level1 {font-size: 150%;color: purple}")
css_lines.append(".title-level2 {font-size: 120%;color: red}")
css_lines.append(".lightborder {width: 100%; border: 1px solid #CCC; margin: 3px; padding: 3px}")
css_lines.append(".titlebox {max-width: 65%}")
css_lines.append(".visualbox {min-height: 100px; max-height: 400px; min-width: 300px; padding: 15px; margin: auto; display: table}")
css_lines.append(".tabs {width: 100%}")
css_lines.append(".widget-text .widget-label, .widget-box .widget-button {width: auto}")
css_lines.append("UL {list-style-type: none; padding-left:0;}")
css = HTML("<style>%s</style>" % '\n'.join(css_lines))

try:
    ip = get_ipython()
    for base in getmro(ip.__class__):
        """If we are in a notebook, we will find 'notebook' in those names"""
        if 'otebook' in base.__name__:
            ip.display_formatter.format(css)
            break
except:
    pass # We are in the test environment

import __main__
def eval_in_main(s):
    """
    Evaluate the expression `s` in the global scope

    TESTS::
        sage: from sage_explorer.sage_explorer import eval_in_main
        sage: from sage.combinat.tableau import Tableaux
        sage: eval_in_main("Tableaux")
        <class 'sage.combinat.tableau.Tableaux'>
    """
    try:
        return eval(s, sage.all.__dict__)
    except:
        return eval(s, __main__.__dict__)

TIMEOUT = 15 # in seconds
EXCLUDED_MEMBERS = ['__init__', '__repr__', '__str__']
OPERATORS = {'==' : OP.eq, '<' : OP.lt, '<=' : OP.le, '>' : OP.gt, '>=' : OP.ge}
CONFIG_PROPERTIES = yaml.load(open(os.path.join(os.path.dirname(__file__),'properties.yml')), yaml.SafeLoader)

def to_html(s):
    r"""Display nicely formatted HTML string
    INPUT: string s
    OUPUT: string

    TESTS::
        sage: from sage_explorer.sage_explorer import to_html
        sage: from sage.combinat.partition import Partition
        sage: Partition.cells.__doc__[:100]
        '\n        Return the coordinates of the cells of ``self``.\n\n        EXAMPLES::\n\n            sage: Par'
        sage: to_html(Partition.cells.__doc__)[:100]
        '<div class="docstring">\n    \n  <blockquote>\n<div><p>Return the coordinates of the cells of <code cla'
    """
    s = str(s)
    try:
        return sphinxify(s)
    except:
        return s

def member_origins(obj, names):
    """Return class where methods in list 'names' are actually defined
    INPUT: object 'obj', list of method names

    TESTS::
        sage: from sage_explorer.sage_explorer import member_origins
        sage: from sage.combinat.partition import Partition
        sage: p = Partition([3,3,2,1])
        sage: member_origins(p, ['add_cell', '_reduction'])
        ({'_reduction': <class 'sage.combinat.partition.Partitions_all_with_category.element_class'>,
          'add_cell': <class 'sage.combinat.partition.Partition'>},
         {'_reduction': [<class 'sage.categories.infinite_enumerated_sets.InfiniteEnumeratedSets.element_class'>,
           <class 'sage.categories.enumerated_sets.EnumeratedSets.element_class'>,
           <class 'sage.categories.sets_cat.Sets.Infinite.element_class'>,
           <class 'sage.categories.sets_cat.Sets.element_class'>,
           <class 'sage.categories.sets_with_partial_maps.SetsWithPartialMaps.element_class'>,
           <class 'sage.categories.objects.Objects.element_class'>],
          'add_cell': []})
    """
    c0 = obj
    if not isclass(c0):
        c0 = obj.__class__
    # Initialisation
    origins, overrides = {}, {}
    for name in names:
        origins[name] = c0
        overrides[name] = []
    for c in c0.__mro__[1:]:
        for name in names:
            if not name in [x[0] for x in getmembers(c)]:
                continue
            for x in getmembers(c):
                if x[0] == name:
                    if x[1] == getattr(c0, name):
                        origins[name] = c
                    else:
                        overrides[name].append(c)
    return origins, overrides

def pretty_name(s):
    r"""
    Transform a name for lisibility on the interface.

    TESTS::
        sage: from sage_explorer.sage_explorer import pretty_name
        sage: pretty_name("EnumeratedSet_all_with_category")
        'Enumerated Set all with category'
    """
    initial, follow = s[0], s[1:].replace('_', ' ')
    while 1:
        m = re.search('(?<! )[A-Z]', follow)
        if not m:
            break
        follow = follow.replace(m.group(), " " + m.group())
    return initial + follow

def extract_classname(c, element_ok=False):
    """Extract proper class name from class
    INPUT: class c
    OUTPUT: string

    TESTS::
    >> c = <class 'sage.combinat.tableau.StandardTableau'>
    >> extract_classname(c)
    Standard Tableau
    >> c = <class 'sage.combinat.tableau.StandardTableaux_all_with_category.element_class'>
    >> extract_classname(c)
    Element of Standard Tableaux all with category
    """
    s = str(c.__name__)
    #if ('element_class' in s or 'parent_class' in s) and not element_ok:
    #    s = str(c.__bases__[0])
    if s.endswith('>'):
        s = s[:-1]
        s = s.strip()
    if s.endswith("'"):
        s = s [:-1]
        s = s.strip()
    if not '.' in s:
        return pretty_name(s)
    parent, last = s.split('.')[-2], s.split('.')[-1]
    if last == 'parent_class':
        return pretty_name(parent)
    if last == 'element_class':
        parent = re.sub('s$|s ', '', parent)
        parent = re.sub(' $', '', parent)
        if re.match('^[AEIOUaeiou]', parent):
            return 'Element of an ' + pretty_name(parent)
        return 'Element of a ' + pretty_name(parent)
    return pretty_name(last)

def get_widget(obj):
    r"""
    Which is the specialized widget class name for viewing this object (if any)

    TESTS::
        sage: from sage.all import *
        sage: from sage_explorer._widgets import *
        sage: from sage_explorer.sage_explorer import get_widget
        sage: p = Partition([3,3,2,1])
        sage: get_widget(p).__class__
        <class 'sage_combinat_widgets.grid_view_widget.GridViewWidget'>
    """
    if isclass(obj):
        return
    if hasattr(obj, "_widget_"):
        return obj._widget_()
    else:
        return

def property_label(obj, funcname):
    r"""
    Test whether this method, for this object,
    will be calculated at opening and displayed on this widget
    If True, return a label.

    INPUT: object obj, method name funcname
    OUTPUT: String or None

    TESTS::
        sage: from sage.all import *
        sage: from sage_explorer.sage_explorer import property_label
        sage: st = StandardTableaux(3).an_element()
        sage: sst = SemistandardTableaux(3).an_element()
        sage: property_label(sst, "is_standard")
        'Is Standard'
        sage: property_label(st, "is_standard")
        sage: property_label(st, "parent")
        'Element of'
    """
    if not funcname in CONFIG_PROPERTIES.keys():
        return
    config = CONFIG_PROPERTIES[funcname]
    if 'isinstance' in config.keys():
        """Test isinstance"""
        if not isinstance(obj, eval_in_main(config['isinstance'])):
            return
    if 'not isinstance' in config.keys():
        """Test not isinstance"""
        if isinstance(obj, eval_in_main(config['not isinstance'])):
            return
    if 'in' in config.keys():
        """Test in"""
        try:
            if not obj in eval_in_main(config['in']):
                return
        except:
            return # The error is : descriptor 'category' of 'sage.structure.parent.Parent' object needs an argument
    if 'not in' in config.keys():
        """Test not in"""
        if obj in eval_in_main(config['not in']):
            return
    def test_when(funcname, expected, operator=None, complement=None):
        if funcname == 'isclass': # FIXME Prendre les premières valeurs de obj.getmembers pour le test -> calculer cette liste avant ?
            res = eval_in_main(funcname)(obj)
        else:
            res = getattr(obj, funcname)
        if operator and complement:
            res = operator(res, eval_in_main(complement))
        return (res == expected)
    def split_when(s):
        when_parts = config['when'].split()
        funcname = when_parts[0]
        if len(when_parts) > 2:
            operatorsign, complement = when_parts[1], when_parts[2]
        elif len(when_parts) > 1:
            operatorsign, complement = when_parts[1][0], when_parts[1][1:]
        if operatorsign in OPERATORS.keys():
            operator = OPERATORS[operatorsign]
        else:
            operator = "not found"
        return funcname, operator, complement
    if 'when' in config.keys():
        """Test when predicate(s)"""
        if isinstance(config['when'], six.string_types):
            when = [config['when']]
        elif isinstance(config['when'], (list,)):
            when = config['when']
        else:
            return
        for predicate in when:
            if not ' ' in predicate:
                if not hasattr(obj, predicate):
                    return
                if not test_when(predicate, True):
                    return
            else:
                funcname, operator, complement = split_when(predicate)
                if not hasattr(obj, funcname):
                    return
                if operator == "not found":
                    return
                if not test_when(funcname, True, operator, complement):
                    return
    if 'not when' in config.keys():
        """Test not when predicate(s)"""
        if isinstance(config['not when'], six.string_types):
            nwhen = [config['not when']]
            if not test_when(config['not when'],False):
                return
        elif isinstance(config['not when'], (list,)):
            nwhen = config['not when']
        else:
            return
        for predicate in nwhen:
            if not ' ' in predicate:
                if not test_when(predicate, False):
                    return
            else:
                funcname, operator, complement = split_when(predicate)
                if not test_when(funcname, False, operator, complement):
                    return
    if 'label' in config.keys():
        return config['label']
    return ' '.join([x.capitalize() for x in funcname.split('_')])

def display_property(label, res):
    return '%s: `%s <http://www.opendreamkit.org>`_' % (label, res)

def append_widget(cont, w):
    """Append widget w to container widget cont"""
    children = list(cont.children)
    children.append(w)
    cont.children = children

def replace_widget_hard(cont, w1, w2):
    """Within container widget cont, replace widget w1 with widget w2"""
    children = list(cont.children)
    for i in range(len(children)):
        if children[i] == w1:
            children[i] = w2
    cont.children = children

def replace_widget_w_css(w1, w2):
    """Replace widget w1 with widget w2"""
    w1.remove_class('visible')
    w1.add_class('invisible')
    w2.remove_class('invisible')
    w2.add_class('visible')

class Title(Label):
    r"""A title of various levels

    For HTML display
    """
    def __init__(self, value='', level=1):
        super(Title, self).__init__()
        self.value = value
        self.add_class('title-level%d' % level)

class ExploredMember(object):
    r"""
    A member of the explored object: method, attribute ..
    """
    vocabulary = ['name', 'member', 'parent', 'member_type', 'doc', 'origin', 'overrides', 'privacy', 'prop_label', 'args', 'defaults']

    def __init__(self, name, **kws):
        r"""
        A method or attribute.
        Must have a name.

        TESTS::
            sage: from sage_explorer.sage_explorer import ExploredMember
            sage: from sage.combinat.partition import Partition
            sage: p = Partition([3,3,2,1])
            sage: m = ExploredMember('conjugate', parent=p)
            sage: m.name
            'conjugate'
        """
        self.name = name
        for arg in kws:
            try:
                assert arg in self.vocabulary
            except:
                raise ValueError("Argument '%s' not in vocabulary." % arg)
            setattr(self, arg, kws[arg])

    def compute_member(self, parent=None):
        r"""
        Get method or attribute value, given the name.

        TESTS::
            sage: from sage_explorer.sage_explorer import ExploredMember
            sage: from sage.combinat.partition import Partition
            sage: p = Partition([3,3,2,1])
            sage: m = ExploredMember('conjugate', parent=p)
            sage: m.compute_member()
            sage: m.member
            <bound method Partitions_all_with_category.element_class.conjugate of [3, 3, 2, 1]>
        """
        if hasattr(self, 'member') and not parent:
            return
        if not parent and hasattr(self, 'parent'):
            parent = self.parent
        if not parent:
            return
        self.parent = parent
        self.member = getattr(parent, self.name)
        self.doc = self.member.__doc__

    def compute_doc(self, parent=None):
        r"""
        Get method or attribute documentation, given the name.

        TESTS::
            sage: from sage_explorer.sage_explorer import ExploredMember
            sage: from sage.combinat.partition import Partition
            sage: p = Partition([3,3,2,1])
            sage: m = ExploredMember('conjugate', parent=p)
            sage: m.compute_doc()
            sage: m.doc[:100]
            '\n        Return the conjugate partition of the partition ``self``. This\n        is also called the a'
        """
        if hasattr(self, 'member'):
            self.doc = self.member.__doc__
        else:
            self.compute_member(parent)

    def compute_member_type(self, parent=None):
        r"""
        Get method or attribute value, given the name.

        TESTS::
            sage: from sage_explorer.sage_explorer import ExploredMember
            sage: from sage.combinat.partition import Partition
            sage: p = Partition([3,3,2,1])
            sage: m = ExploredMember('conjugate', parent=p)
            sage: m.compute_member_type()
            sage: assert 'method' in m.member_type
        """
        if not hasattr(self, 'member'):
            self.compute_member(parent)
        if not hasattr(self, 'member'):
            raise ValueError("Cannot determine the type of a non existent member.")
        m = re.match("<(type|class) '([.\\w]+)'>", str(type(self.member)))
        if m and ('method' in m.group(2)):
            self.member_type = m.group(2)
        else:
            self.member_type = "attribute (%s)" % str(type(self.member))

    def compute_privacy(self):
        r"""
        Compute member privacy, if any.

        TESTS::
            sage: from sage_explorer.sage_explorer import ExploredMember
            sage: from sage.combinat.partition import Partition
            sage: p = Partition([3,3,2,1])
            sage: m = ExploredMember('__class__', parent=p)
            sage: m.compute_privacy()
            sage: m.privacy
            'python_special'
            sage: m = ExploredMember('_doccls', parent=p)
            sage: m.compute_privacy()
            sage: m.privacy
            'private'
        """
        if not self.name.startswith('_'):
            self.privacy = None
            return
        if self.name.startswith('__') and self.name.endswith('__'):
            self.privacy = 'python_special'
        elif self.name.startswith('_') and self.name.endswith('_'):
            self.privacy = 'sage_special'
        else:
            self.privacy = 'private'

    def compute_origin(self, parent=None):
        r"""
        Determine in which base class 'origin' of class 'parent'
        this member is actually defined, and also return the list
        of overrides if any.

        TESTS::
            sage: from sage_explorer.sage_explorer import ExploredMember
            sage: from sage.combinat.partition import Partition
            sage: p = Partition([3,3,2,1])
            sage: m = ExploredMember('_reduction', parent=p)
            sage: m.compute_origin()
            sage: m.origin, m.overrides
            (<class 'sage.combinat.partition.Partitions_all_with_category.element_class'>,
             [<class 'sage.categories.infinite_enumerated_sets.InfiniteEnumeratedSets.element_class'>,
              <class 'sage.categories.enumerated_sets.EnumeratedSets.element_class'>,
              <class 'sage.categories.sets_cat.Sets.Infinite.element_class'>,
              <class 'sage.categories.sets_cat.Sets.element_class'>,
              <class 'sage.categories.sets_with_partial_maps.SetsWithPartialMaps.element_class'>,
              <class 'sage.categories.objects.Objects.element_class'>])
        """
        if not parent:
            if not hasattr(self, 'parent'):
                raise ValueError("Cannot compute origin without a parent.")
            parent = self.parent
        self.parent = parent
        if isclass(parent):
            parentclass = parent
        else:
            parentclass = parent.__class__
        origin, overrides = parentclass, []
        for c in parentclass.__mro__[1:]:
            if not self.name in [x[0] for x in getmembers(c)]:
                continue
            for x in getmembers(c):
                if x[0] == self.name:
                    if x[1] == getattr(parentclass, self.name):
                        origin = c
                    else:
                        overrides.append(c)
        self.origin, self.overrides = origin, overrides

    def compute_argspec(self, parent=None):
        r"""
        If this member is a method: compute its args and defaults.

        TESTS::
            sage: from sage_explorer.sage_explorer import ExploredMember
            sage: from sage.combinat.partition import Partition
            sage: p = Partition([3,3,2,1])
            sage: m = ExploredMember('add_cell', parent=p)
            sage: m.compute_member()
            sage: m.compute_argspec()
            sage: m.args, m.defaults
            (['self', 'i', 'j'], (None,))
        """
        args = None
        defaults = None
        try:
            argspec = getargspec(self.member)
            if hasattr(argspec, 'args'):
                self.args = argspec.args
            if hasattr(argspec, 'defaults'):
                self.defaults = argspec.defaults
        except:
            pass

    def compute_property_label(self, config):
        r"""
        Retrieve the property label, if any, from configuration 'config'.

        TESTS::
            sage: from sage_explorer.sage_explorer import ExploredMember
            sage: from sage.combinat.partition import Partition
            sage: F = GF(7)
            sage: m = ExploredMember('polynomial', parent=F)
            sage: m.compute_property_label({'polynomial': {'in': 'Fields.Finite'}})
            sage: m.prop_label
            'Polynomial'
        """
        self.prop_label = None
        if not self.name in config.keys():
            return
        if not hasattr(self, 'parent'):
            raise ValueError("Cannot compute property label without a parent.")
        myconfig = config[self.name]
        if 'isinstance' in myconfig.keys():
            """Test isinstance"""
            if not isinstance(self.parent, eval_in_main(myconfig['isinstance'])):
                return
        if 'not isinstance' in myconfig.keys():
            """Test not isinstance"""
            if isinstance(self.parent, eval_in_main(myconfig['not isinstance'])):
                return
        if 'in' in myconfig.keys():
            """Test in"""
            try:
                if not self.parent in eval_in_main(myconfig['in']):
                    return
            except:
                return # The error is : descriptor 'category' of 'sage.structure.parent.Parent' object needs an argument
        if 'not in' in myconfig.keys():
            """Test not in"""
            if self.parent in eval_in_main(myconfig['not in']):
                return
        def test_when(funcname, expected, operator=None, complement=None):
            if funcname == 'isclass': # FIXME Prendre les premières valeurs de obj.getmembers pour le test -> calculer cette liste avant ?
                res = eval_in_main(funcname)(self.parent)
            else:
                res = getattr(self.parent, funcname).__call__()
            if operator and complement:
                res = operator(res, eval_in_main(complement))
            return (res == expected)
        def split_when(s):
            when_parts = myconfig['when'].split()
            funcname = when_parts[0]
            if len(when_parts) > 2:
                operatorsign, complement = when_parts[1], when_parts[2]
            elif len(when_parts) > 1:
                operatorsign, complement = when_parts[1][0], when_parts[1][1:]
            if operatorsign in OPERATORS.keys():
                operator = OPERATORS[operatorsign]
            else:
                operator = "not found"
            return funcname, operator, complement
        if 'when' in myconfig.keys():
            """Test when predicate(s)"""
            if isinstance(myconfig['when'], six.string_types):
                when = [myconfig['when']]
            elif isinstance(myconfig['when'], (list,)):
                when = myconfig['when']
            else:
                return
            for predicate in when:
                if not ' ' in predicate:
                    if not hasattr(self.parent, predicate):
                        return
                    if not test_when(predicate, True):
                        return
                else:
                    funcname, operator, complement = split_when(predicate)
                    if not hasattr(self.parent, funcname):
                        return
                    if operator == "not found":
                        return
                    if not test_when(funcname, True, operator, complement):
                        return
        if 'not when' in myconfig.keys():
            """Test not when predicate(s)"""
            if isinstance(myconfig['not when'], six.string_types):
                nwhen = [myconfig['not when']]
            if not test_when(myconfig['not when'],False):
                return
            elif isinstance(myconfig['not when'], (list,)):
                nwhen = myconfig['not when']
            else:
                return
            for predicate in nwhen:
                if not ' ' in predicate:
                    if not test_when(predicate, False):
                        return
                else:
                    funcname, operator, complement = split_when(predicate)
                    if not test_when(funcname, False, operator, complement):
                        return
        if 'label' in myconfig.keys():
            self.prop_label = myconfig['label']
        else:
            self.prop_label = ' '.join([x.capitalize() for x in self.name.split('_')])

def make_catalog_menu_options(catalog):
    r"""Turn catalog into usable menu options

    Parse the list of names in the catalog module,
    keep only real catalog objects,
    try to apply those that are functions
    and turn the list into menu option tuples.

    INPUT:
    - `catalog` -- a module

    OUTPUT:
    - `options` -- a list of tuples (name, value)

    TESTS::
        sage: from sage_explorer.sage_explorer import make_catalog_menu_options
        sage: from sage.monoids import all as monoids_catalog
        sage: members = make_catalog_menu_options(monoids_catalog)
        sage: members[0][0], members[0][1].member_type
        ('AlphabeticStrings', "attribute (<type 'function'>)")
    """
    members = []
    if type(catalog) == type([]):
        members += [(str(x), x) for x in catalog]
    for name in sorted(dir(catalog)):
        member = getattr(catalog, name)
        if not name[0].isupper():
            continue
        members.append(ExploredMember(name, member=member))
    for m in members:
        m.compute_member_type()
        m.compute_doc()
    return [(m.name, m) for m in members]

class SageExplorer(VBox):
    """Sage Explorer in Jupyter Notebook"""

    value = Any()

    def __init__(self, obj=None):
        """
        TESTS::

            sage: from sage_explorer.sage_explorer import SageExplorer
            sage: S = StandardTableaux(15)
            sage: t = S.random_element()
            sage: widget = SageExplorer(t)
        """
        super(SageExplorer, self).__init__()
        self.title = Title()
        self.propsbox = VBox() # Will be a VBox full of HBoxes, one for each property
        self.titlebox = VBox()
        self.titlebox.add_class('titlebox')
        self.titlebox.children = [self.title, self.propsbox]
        self.visualbox = Box()
        self.visualtext = Textarea('', rows=8)
        self.visualwidget = None
        self.visualbox.add_class('visualbox')
        self.visualbox.children = [self.visualtext]
        self.top = HBox([self.titlebox, self.visualbox], layout=justified_h_layout)
        self.menus = Accordion(selected_index=None)
        self.menusbox = VBox([Title("Menus", 2), self.menus])
        self.inputs = HBox()
        self.gobutton = Button(description='Run!', tooltip='Run the function or method, with specified arguments')
        self.output = HTML()
        self.worktab = VBox((self.inputs, self.gobutton, self.output))
        self.doc = HTML()
        self.doctab = HTML() # For the method docstring
        self.tabs = Tab((self.worktab, self.doctab)) # Will be used when a method is selected
        self.tabs.add_class('tabs')
        self.tabs.set_title(0, 'Call')
        self.tabs.set_title(1, 'Help')
        self.main = Box((self.doc, self.tabs))
        self.tabs.add_class('invisible') # Hide tabs at first display
        self.bottom = HBox((self.menusbox, self.main), layout=main_h_layout)
        self.menusbox.add_class('lightborder')
        self.main.add_class('lightborder')
        self.titlebox.add_class('lightborder')
        self.children = (self.top, self.bottom)
        self.history = []
        self.set_value(obj)

    def init_selected_menu_value(self):
        r"""
        From a menu selection, compute display elements for the widgets.

        TESTS::
            sage: from sage_explorer.sage_explorer import SageExplorer, ExploredMember
            sage: from sage.monoids.string_monoid import AlphabeticStrings
            sage: e = SageExplorer()
            sage: m = ExploredMember('AlphabeticStrings', member=AlphabeticStrings)
            sage: e.selected_menu_value = m
            sage: e.init_selected_menu_value()
            sage: str(e.doctab.value[:100])
            '<div class="docstring">\n    \n  <blockquote>\n<div><p>Returns the string monoid on generators A-Z:\n<sp'
        """
        if self.value:
            """If we are exploring an object, all menu items are functions"""
            self.init_selected_func()
            return
        """We are on the catalogs page"""
        selected_obj = self.selected_menu_value # An ExplorerMember
        if not hasattr(selected_obj, 'member_type'):
            selected_obj.compute_member_type()
        if not hasattr(selected_obj, 'doc'):
            selected_obj.compute_doc()
        if 'function' in selected_obj.member_type or 'method' in selected_obj.member_type:
            self.doctab.value = to_html(selected_obj.doc)
            if not hasattr(selected_obj, 'args'):
                try:
                    selected_obj.member = selected_obj.member()
                except:
                    pass
            elif hasattr(selected_obj, 'defaults') and len(selected_obj.defaults) == len(selected_obj.args):
                try:
                    selected_obj.member = selected_obj.member(selected_obj.defaults)
                except:
                    pass
            return
        if 'class' in selected_obj.member_type:
            self.doc.value = to_html(selected_obj.doc)
            self.doctab.value = ''
            self.inputs.children = []
            self.tabs.remove_class('visible')
            self.tabs.add_class('invisible')
            self.doc.remove_class('invisible')
            self.doc.add_class('visible')
            return

    def init_selected_func(self):
        r"""
        From a menu selection, compute display elements for the widgets.

        TESTS::
            sage: from sage_explorer.sage_explorer import SageExplorer, ExploredMember
            sage: from sage.combinat.partition import Partition
            sage: p = Partition([3,3,2,1])
            sage: e = SageExplorer(p)
            sage: m = ExploredMember('conjugate', parent=p)
            sage: e.selected_menu_value = m
            sage: e.init_selected_func()
            sage: str(e.doctab.value[:100]) # For Python3 compatibility
            '<div class="docstring">\n    \n  <blockquote>\n<div><p>Return the conjugate partition of the partition '
        """
        self.output.value = ''
        func = self.selected_menu_value # An ExplorerMember
        if not hasattr(func, 'doc'):
            func.compute_doc()
        if not hasattr(func, 'origin'):
            func.compute_origin()
        self.doctab.value = to_html(func.doc)
        if func.overrides:
            self.doctab.value += to_html("Overrides:")
            self.doctab.value += to_html(', '.join([extract_classname(x, element_ok=True) for x in func.overrides]))
        inputs = []
        if not hasattr(func, 'args'):
            func.compute_argspec()
        try:
            shift = 0
            for i in range(len(func.args)):
                argname = func.args[i]
                if argname in ['self']:
                    shift = 1
                    continue
                default = ''
                if func.defaults and len(func.defaults) > i - shift and func.defaults[i - shift]:
                    default = func.defaults[i - shift]
                inputs.append(Text(description=argname, placeholder=str(default)))
        except:
            print (func, "attr?")
            print (func.args, func.defaults)
        self.inputs.children = inputs
        self.doc.remove_class('visible')
        self.doc.add_class('invisible')
        self.tabs.remove_class('invisible')
        self.tabs.add_class('visible')

    def get_title(self):
        r"""
        Get explorer general title.

        TESTS:
            sage: from sage_explorer import SageExplorer
            sage: from sage.combinat.partition import Partition
            sage: p = Partition([3,3,2,1])
            sage: e = SageExplorer(p)
            sage: e.get_title()
            'Exploring: [3, 3, 2, 1]'
        """
        return "Exploring: %s" % repr(self.value)

    def get_members(self):
        r"""
        Get all members for object self.value.

        OUTPUT: List of `Member` named tuples.

        TESTS::
            sage: from sage_explorer import SageExplorer
            sage: from sage.combinat.partition import Partition
            sage: p = Partition([3,3,2,1])
            sage: e = SageExplorer(p)
            sage: e.get_members()
            sage: e.members[2].name, e.members[2].privacy
            ('__class__', 'python_special')
            sage: e.members[68].name, e.members[68].origin, e.members[68].privacy
            ('_doccls', <class 'sage.combinat.partition.Partitions_all_with_category.element_class'>, 'private')
            sage: e.members[112].name, e.members[112].overrides, e.members[112].prop_label
            ('_reduction',
             [<class 'sage.categories.infinite_enumerated_sets.InfiniteEnumeratedSets.element_class'>,
              <class 'sage.categories.enumerated_sets.EnumeratedSets.element_class'>,
              <class 'sage.categories.sets_cat.Sets.Infinite.element_class'>,
              <class 'sage.categories.sets_cat.Sets.element_class'>,
              <class 'sage.categories.sets_with_partial_maps.SetsWithPartialMaps.element_class'>,
              <class 'sage.categories.objects.Objects.element_class'>],
             None)
            sage: e = SageExplorer(Partition)
            sage: e.get_members()
        """
        if isclass(self.value):
            c0 = self.value
        else:
            c0 = self.value.__class__
        self.valueclass = c0
        members = []
        for name, member in getmembers(c0):
            if isabstract(member) or 'deprecated' in str(type(member)).lower():
                continue
            m = ExploredMember(name, member=member, parent=self.value)
            m.compute_member_type()
            m.compute_origin()
            m.compute_privacy()
            m.compute_property_label(CONFIG_PROPERTIES)
            members.append(m)
        self.members = members

    def get_attributes(self):
        r"""
        Get all attributes for object self.value.

        OUTPUT: List of `Attribute` named tuples.

        TESTS::
            sage: from sage_explorer import SageExplorer
            sage: from sage.combinat.partition import Partition
            sage: p = Partition([3,3,2,1])
            sage: e = SageExplorer(p)
            sage: e.get_attributes()
            sage: e.attributes[0].name, e.attributes[0].privacy
            ('__class__', 'python_special')
            sage: e.attributes[30].name, e.attributes[30].origin, e.attributes[30].privacy
            ('_doccls', <class 'sage.combinat.partition.Partitions_all_with_category.element_class'>, 'private')
            sage: e.attributes[33].name, e.attributes[33].overrides, e.attributes[33].prop_label
            ('_reduction',
             [<class 'sage.categories.infinite_enumerated_sets.InfiniteEnumeratedSets.element_class'>,
              <class 'sage.categories.enumerated_sets.EnumeratedSets.element_class'>,
              <class 'sage.categories.sets_cat.Sets.Infinite.element_class'>,
              <class 'sage.categories.sets_cat.Sets.element_class'>,
              <class 'sage.categories.sets_with_partial_maps.SetsWithPartialMaps.element_class'>,
              <class 'sage.categories.objects.Objects.element_class'>],
             None)
            sage: e.attributes[35].name, e.attributes[35].overrides, e.attributes[34].prop_label
            ('young_subgroup', [<class 'sage.combinat.partition.Partition'>], None)
        """
        if not hasattr(self, 'members'):
            self.get_members()
        attributes = []
        for m in self.members:
            if m.member_type.startswith('attribute'):
                attributes.append(m)
        self.attributes = attributes

    def get_methods(self):
        r"""
        Get all methods specifications for object self.value.

        TESTS::
            sage: from sage_explorer import SageExplorer
            sage: from sage.combinat.partition import Partition
            sage: p = Partition([3,3,2,1])
            sage: e = SageExplorer(p)
            sage: e.get_methods()
            sage: e.methods[54].name, e.methods[54].member_type, e.methods[54].privacy
            ('_latex_coeff_repr', 'method_descriptor', 'private')
            sage: e.methods[99].name, e.methods[99].args, e.methods[99].origin
            ('add_cell', ['self', 'i', 'j'], <class 'sage.combinat.partition.Partition'>)
            sage: e.methods[106].name, e.methods[106].args, e.methods[106].defaults
            ('arm_lengths', ['self', 'flat'], (False,))
            sage: e = SageExplorer(Partition)
            sage: e.get_methods()
        """
        if not hasattr(self, 'members'):
            self.get_members()
        methods = []
        for m in self.members:
            if not 'method' in m.member_type:
                continue
            m.compute_argspec()
            methods.append(m)
        self.methods = methods

    def compute(self):
        """Get some properties, depending on the object
        Create links between menus and output tabs"""
        obj = self.value
        if obj is None:
            self.make_index()
            return
        if isclass(obj):
            c0 = obj
        else:
            c0 = obj.__class__
        if not hasattr(self, 'objclass') or c0 != self.objclass:
            self.objclass = c0
            self.get_members()
            self.get_attributes()
            self.get_methods()
        self.classname = extract_classname(c0, element_ok=False)
        self.title.value = self.get_title()
        replace_widget_w_css(self.tabs, self.doc)
        visualwidget = get_widget(obj)
        if visualwidget:
            # Reset if necessary, then replace with visualbox
            self.visualbox.children = [self.visualtext]
            self.visualwidget = visualwidget
            def graphical_change(change):
                self.set_value(change.new)
            self.visualwidget.observe(graphical_change, names='value')
            replace_widget_hard(self.visualbox, self.visualtext, self.visualwidget)
        else:
            try:
                self.visualtext.value = repr(obj._ascii_art_())
            except:
                self.visualtext.value = repr(obj)
            if self.visualwidget:
                replace_widget_hard(self.visualbox, self.visualwidget, self.visualtext)
                self.visualwidget = None
        attributes_as_properties = [m for m in self.attributes if m.prop_label]
        methods_as_properties = [m for m in self.methods if m.prop_label]
        attributes = [m for m in self.attributes if not m in attributes_as_properties and not m.name in EXCLUDED_MEMBERS and not m.privacy in ['private', 'sage_special']]
        methods = [m for m in self.methods if not m in methods_as_properties and not m.name in EXCLUDED_MEMBERS and not m.privacy in ['private', 'sage_special']]
        props = [Title('Properties', 2)] # a list of HBoxes, to become self.propsbox's children
        # Properties
        for p in attributes_as_properties + methods_as_properties:
            try:
                value = p.member(obj)
            except:
                print ("Warning: Error in finding method %s" % p.name)
                value = None
            button = self.make_new_page_button(value)
            b_label = p.prop_label
            if type(value) is type(True):
                b_label += '?'
            else:
                b_label += ':'
            props.append(HBox([
                Label(b_label),
                button
            ]))
        if len(self.history) > 1:
            self.propsbox.children = props + [self.make_back_button()]
        else:
            self.propsbox.children = props
        # Object doc
        self.doc.value = to_html(obj.__doc__) # Initialize to object docstring
        # Methods (sorted by definition classes)
        self.selected_menu_value = c0
        bases = []
        basemembers = {}
        for c in getmro(c0):
            bases.append(c)
            basemembers[c] = []
        for m in methods:
            basemembers[m.origin].append(m.name)
        for c in basemembers:
            if not basemembers[c]:
                bases.remove(c)
        menus = []
        for i in range(len(bases)):
            c = bases[i]
            menus.append(Select(rows=12, options = [(m.name, m) for m in methods if m.name in basemembers[c]]
            ))
        self.menus.children = menus
        for i in range(len(bases)):
            c = bases[i]
            self.menus.set_title(i, extract_classname(c))
        def menu_on_change(change):
            self.selected_menu_value = change.new
            self.init_selected_menu_value()
        for menu in self.menus.children:
            menu.observe(menu_on_change, names='value')
        def compute_selected_method(button):
            args = []
            for i in self.inputs.children:
                try:
                    arg = i.value or i.placeholder
                    evaled_arg = eval_in_main(arg)
                    if not arg:
                        self.output.value = to_html("Argument '%s' is empty!" % i.description)
                        return
                    args.append(evaled_arg)
                except:
                    self.output.value = to_html("Could not evaluate argument '%s'" % i.description)
                    return
            try:
                if AlarmInterrupt:
                    alarm(TIMEOUT)
                out = self.selected_menu_value.member(obj, *args)
                if AlarmInterrupt:
                    cancel_alarm()
            except AlarmInterrupt:
                self.output.value = to_html("Timeout!")
            except Exception as e:
                self.output.value = to_html(e)
                return
            self.output.value = to_html(out)
        self.gobutton.description = 'Run!'
        self.gobutton.on_click(compute_selected_method)

    def make_back_button(self):
        r"""
        Make a button for getting back to the previous object.

        TESTS::
            sage: from sage_explorer import SageExplorer
            sage: from sage.combinat.partition import Partition
            sage: p1 = Partition([3,3,2,1])
            sage: p2 = Partition([5,3,2])
            sage: e = SageExplorer(p1)
            sage: e.make_back_button()
            sage: e.set_value(p2)
            sage: e.make_back_button()
            Button(description=u'Back', icon=u'history', layout=Layout(width=u'7em'), style=ButtonStyle(), tooltip=u'Go back to previous object page')
        """
        if len(self.history) <= 1:
            return
        button = Button(description='Back', icon='history', tooltip="Go back to previous object page", layout=back_button_layout)
        button.on_click(lambda event: self.pop_value()) # No back button in this new (previous object) page
        return button

    def make_new_page_button(self, obj):
        r"""
        Make a button for fetching a new explorer with value `obj`.

        TESTS::
            sage: from sage_explorer import SageExplorer
            sage: from sage.combinat.partition import Partition
            sage: p1 = Partition([3,3,2,1])
            sage: p2 = Partition([5,3,2])
            sage: e = SageExplorer(p1)
            sage: e.make_new_page_button(p2)
            Button(description=u'[5, 3, 2]', style=ButtonStyle(), tooltip=u'Will close current explorer and open a new one')
        """
        button = Button(description=str(obj), tooltip="Will close current explorer and open a new one")
        button.on_click(lambda b:self.set_value(obj))
        return button

    def display_new_value(self, obj):
        r"""
        A callback for the navigation button.
        """
        self.visualbox.children[0].value = str(obj)

    def get_value(self):
        r"""
        Return math object currently explored.

        TESTS::
            sage: from sage_explorer.sage_explorer import SageExplorer
            sage: from sage.combinat.partition import Partition
            sage: p = Partition([3,3,2,1])
            sage: e = SageExplorer(p)
            sage: e.get_value()
            [3, 3, 2, 1]
        """
        return self.value

    def set_value(self, obj):
        r"""
        Set new math object `obj` to the explorer.

        TESTS::
            sage: from sage_explorer.sage_explorer import SageExplorer
            sage: from sage.combinat.partition import Partition
            sage: p = Partition([3,3,2,1])
            sage: e = SageExplorer(p)
            sage: e.get_value()
            [3, 3, 2, 1]
            sage: from sage.combinat.tableau import Tableau
            sage: t = Tableau([[1,2,3,4], [5,6]])
            sage: e.set_value(t)
            sage: e.get_value()
            [[1, 2, 3, 4], [5, 6]]
        """
        self.history.append(obj)
        self.value = obj
        self.compute()

    def pop_value(self):
        r"""
        Set again previous math object to the explorer.

        TESTS::
            sage: from sage_explorer.sage_explorer import SageExplorer
            sage: from sage.combinat.partition import Partition
            sage: p = Partition([3,3,2,1])
            sage: e = SageExplorer(p)
            sage: from sage.combinat.tableau import Tableau
            sage: t = Tableau([[1,2,3,4], [5,6]])
            sage: e.set_value(t)
            sage: e.get_value()
            [[1, 2, 3, 4], [5, 6]]
            sage: e.pop_value()
            sage: e.get_value()
            [3, 3, 2, 1]
        """
        if self.history:
            self.history.pop()
        if self.history:
            self.value = self.history[-1]
        else:
            self.value = None
        self.compute()

    def make_index(self):
        try:
            from ._catalogs import catalogs
        except:
            print("To build the index page, we need some catalogs.")
            catalogs = []
        self.selected_object = None
        self.title.value = "Sage Explorer"
        self.visualbox.children = [Title("Index Page")]
        self.tabs.remove_class('invisible')
        self.tabs.add_class('visible')
        self.gobutton.description = 'Go!'
        menus = []
        for label, catalog in catalogs:
            menu = Select(rows=12, options=make_catalog_menu_options(catalog))
            menus.append(menu)
        self.menus.children = menus
        for i, (label, _) in enumerate(catalogs):
            self.menus.set_title(i, label)
        def menu_on_change(change):
            self.selected_object = change.new
            self.display_new_value(self.selected_object.name)
            self.doctab.value = to_html(change.new.doc)
            self.gobutton.on_click(lambda b:self.set_value(self.selected_object.member))
        for menu in self.menus.children:
            menu.observe(menu_on_change, names='value')
