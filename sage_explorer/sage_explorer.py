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
from ipywidgets import Layout, Box, VBox, HBox, Text, Label, HTML, Select, Textarea, Accordion, Tab, Button
import traitlets
from inspect import getargspec, getmembers, getmro, isclass, isfunction, ismethod, ismethoddescriptor
from cysignals.alarm import alarm, cancel_alarm, AlarmInterrupt
from sage.misc.sageinspect import sage_getargspec
from sage.misc.bindable_class import BindableClass
from sage.all import SAGE_TMP, plot, SageObject
import yaml, os, six, operator as OP
from os.path import join as path_join
from ._catalogs import catalogs
from IPython.core import display
import sage.all

back_button_layout = Layout(width='7em')
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
ip = get_ipython()
for base in getmro(ip.__class__):
    """If we are in a notebook, we will find 'notebook' in those names"""
    if 'otebook' in base.__name__:
        ip.display_formatter.format(css)
        break

import __main__
def eval_in_main(s):
    """
    Evaluate the expression `s` in the global scope

        sage: from sage_explorer.sage_explorer import eval_in_main
        sage: eval_in_main("Tableaux")
        <class 'sage.combinat.tableau.Tableaux'>
    """
    return eval(s, sage.all.__dict__)

TIMEOUT = 15 # in seconds
EXCLUDED_MEMBERS = ['__init__', '__repr__', '__str__']
OPERATORS = {'==' : OP.eq, '<' : OP.lt, '<=' : OP.le, '>' : OP.gt, '>=' : OP.ge}
CONFIG_ATTRIBUTES = yaml.load(open(os.path.join(os.path.dirname(__file__),'attributes.yml')))

def to_html(s):
    r"""Display nicely formatted HTML string
    INPUT: string s
    OUPUT: string
    """
    s = str(s)
    from sage.misc.sphinxify import sphinxify
    return sphinxify(s)

def method_origins(obj, names):
    """Return class where methods in list 'names' are actually defined
    INPUT: object 'obj', list of method names
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

def extract_classname(c, element_ok=False):
    """Extract proper class name from class
    INPUT: class c
    OUTPUT: string

    TESTS::
    >> s = <class 'sage.combinat.tableau.StandardTableau'>
    >> extract_classname(s)
    StandardTableau
    >> s = <class 'sage.combinat.tableau.StandardTableaux_all_with_category.element_class'>
    >> extract_classname(s)
    StandardTableau
    """
    s = str(c.__name__)
    if ('element_class' in s or 'parent_class' in s) and not element_ok:
        s = str(c.__bases__[0])
    if s.endswith('>'):
        s = s[:-1]
        s = s.strip()
    if s.endswith("'"):
        s = s [:-1]
        s = s.strip()
    ret = s.split('.')[-1]
    if ret == 'element_class':
        return '.'.join(s.split('.')[-2:])
    return ret

def get_widget(obj):
    """Which is the specialized widget class name for viewing this object (if any)"""
    if hasattr(obj, "_widget_"):
        return obj._widget_()
    else:
        return

def attribute_label(obj, funcname):
    """Test whether this method, for this object,
    will be calculated at opening and displayed on this widget
    If True, return a label.
    INPUT: object obj, method name funcname
    OUTPUT: String or None

    EXAMPLES::

        sage: from sage.all import *
        sage: from sage_explorer.sage_explorer import attribute_label
        sage: st = StandardTableaux(3).an_element()
        sage: sst = SemistandardTableaux(3).an_element()
        sage: attribute_label(sst, "is_standard")
        'Is Standard'
        sage: attribute_label(st, "is_standard")
        sage: attribute_label(st, "parent")
        'Element of'
    """
    if not funcname in CONFIG_ATTRIBUTES.keys():
        return
    config = CONFIG_ATTRIBUTES[funcname]
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

def display_attribute(label, res):
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
    """
    options = [('----', None)]
    if type(catalog) == type([]):
        return options + [(str(x), x) for x in catalog]

    # TODO: move this logic into menu_on_change to be more lazy and only
    # actually construct an object if the user clicks on it. This makes
    # the startup somewhat slow.
    for key in sorted(dir(catalog)):
        value = getattr(catalog, key)
        if not key[0].isupper():
            continue
        if isfunction(value):
            if not getargspec(value).args:
                try:
                    value = value()
                except:
                    pass
            elif getargspec(value).defaults and len(getargspec(value).defaults) == len(getargspec(value).args):
                try:
                    value = value(*getargspec(value).defaults)
                except:
                    pass
        options.append((key, value))
    return options

import sage.misc.classcall_metaclass
class MetaHasTraitsClasscallMetaclass (traitlets.traitlets.MetaHasTraits, sage.misc.classcall_metaclass.ClasscallMetaclass):
    pass
class BindableWidgetClass(BindableClass):
    __metaclass__ = MetaHasTraitsClasscallMetaclass

class PlotWidget(Box, BindableWidgetClass):
    def __init__(self, obj, figsize=4, name=None):
        super(PlotWidget, self).__init__()
        self.obj = obj
        if not name:
            name = repr(obj)
        filename = path_join(SAGE_TMP, '%s.svg' % name)
        plot(obj, figsize=figsize).save(filename)
        self.name = name
        self.value = open(filename, 'rb').read()
        self.children = [HTML(self.value)]


class SageExplorer(VBox):
    """Sage Explorer in Jupyter Notebook"""

    def __init__(self, obj=None):
        """
        TESTS::

            sage: from sage_explorer.sage_explorer import SageExplorer
            sage: S = StandardTableaux(15)
            sage: t = S.random_element()
            sage: widget = SageExplorer(t)
        """
        super(SageExplorer, self).__init__()
        self.title = Label()
        self.title.add_class('title')
        self.propsbox = VBox() # Will be a VBox full of HBoxes, one for each attribute
        self.titlebox = VBox()
        self.titlebox.add_class('titlebox')
        self.titlebox.children = [self.title, self.propsbox]
        self.visualbox = Box()
        self.visualtext = Textarea('', rows=8)
        self.visualwidget = None
        self.visualbox.add_class('visualbox')
        self.visualbox.children = [self.visualtext]
        self.top = HBox([self.titlebox, self.visualbox])
        self.menus = Accordion()
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
        self.set_object(obj)

    def init_selected_method(self):
        self.output.value = ''
        func = self.selected_func
        if isclass(func):
            self.doc.value = to_html(func.__doc__)
            self.doctab.value = ''
            self.inputs.children = []
            self.tabs.remove_class('visible')
            self.tabs.add_class('invisible')
            self.doc.remove_class('invisible')
            self.doc.add_class('visible')
            return
        self.doctab.value = to_html(func.__doc__)
        if self.overrides[func.__name__]:
            self.doctab.value += to_html("Overrides:")
            self.doctab.value += to_html(', '.join([extract_classname(x, element_ok=True) for x in self.overrides[func.__name__]]))
        inputs = []
        try:
            argspec = sage_getargspec(func)
            argnames, defaults = sage_getargspec(func).args, sage_getargspec(func).defaults
            shift = 0
            for i in range(len(argspec.args)):
                argname = argnames[i]
                if argname in ['self']:
                    shift = 1
                    continue
                default = ''
                if defaults and len(defaults) > i - shift and defaults[i - shift]:
                    default = argspec.defaults[i - shift]
                inputs.append(Text(description=argname, placeholder=str(default)))
        except:
            print (func, "attr?")
            print (argspec)
        self.inputs.children = inputs
        self.doc.remove_class('visible')
        self.doc.add_class('invisible')
        self.tabs.remove_class('invisible')
        self.tabs.add_class('visible')

    def compute(self):
        """Get some attributes, depending on the object
        Create links between menus and output tabs"""
        obj = self.obj
        if obj is None:
            self.make_index()
            return
        if isclass(obj):
            c0 = obj
        else:
            c0 = obj.__class__
        self.classname = extract_classname(c0, element_ok=False)
        self.title.value = repr(obj) #"Exploring: %s" % repr(obj)
        replace_widget_w_css(self.tabs, self.doc)
        visualwidget = get_widget(obj)
        if visualwidget:
            # Reset if necessary, then replace with visualbox
            self.visualbox.children = [self.visualtext]
            self.visualwidget = visualwidget
            replace_widget_hard(self.visualbox, self.visualtext, self.visualwidget)
        else:
            try:
                self.visualtext.value = repr(obj._ascii_art_())
            except:
                self.visualtext.value = repr(obj)
            if self.visualwidget:
                replace_widget_hard(self.visualbox, self.visualwidget, self.visualtext)
                self.visualwidget = None
        self.members = [x for x in getmembers(c0) if not x[0] in EXCLUDED_MEMBERS and (not x[0].startswith('_') or x[0].startswith('__')) and not 'deprecated' in str(type(x[1])).lower()]
        self.methods = [x for x in self.members if ismethod(x[1]) or ismethoddescriptor(x[1])]
        methods_as_attributes = [] # Keep track of these directly displayed methods, so you can excluded them from the menus
        props = [] # a list of HBoxes, to become self.propsbox's children
        for x in self.methods:
            try:
                attr_label = attribute_label(obj, x[0])
            except:
                print ("Warning: Error in calculating property_label for method %s" % x[0])
                attr_label = None
            if attr_label:
                methods_as_attributes.append(x)
                try:
                    value = getattr(obj, x[0])()
                except:
                    print ("Warning: Error in finding method %s" % x[0])
                    value = None
                if isinstance(value, SageObject):
                    button = self.make_new_page_button(value)
                    props.append(HBox([
                        Label(attribute_label(obj, x[0])+':'),
                        button
                    ]#, layout=hbox_justified_layout
                    ))
                elif type(value) is type(True):
                    props.append(HBox([
                        Label(attribute_label(obj, x[0])+'?'),
                        Label(str(value))
                    ]))
                else:
                    props.append(HBox([
                        Label(attribute_label(obj, x[0])+':'),
                        Label(str(value))
                    ]))
        if len(self.history) > 1:
            self.propsbox.children = props + [self.make_back_button()]
        else:
            self.propsbox.children = props
        self.doc.value = to_html(obj.__doc__) # Initialize to object docstring
        self.selected_func = c0
        origins, overrides = method_origins(c0, [x[0] for x in self.methods if not x in methods_as_attributes])
        self.overrides = overrides
        bases = []
        basemembers = {}
        for c in getmro(c0):
            bases.append(c)
            basemembers[c] = []
        for name in origins:
            basemembers[origins[name]].append(name)
        for c in basemembers:
            if not basemembers[c]:
                bases.remove(c)
            else:
                pass
                #print c, len(basemembers[c])
        menus = []
        for i in range(len(bases)):
            c = bases[i]
            menus.append(Select(rows=12,
                                options = [('----', c)] + [x for x in self.methods if x[0] in basemembers[c]]
            ))
        self.menus.children = menus
        for i in range(len(bases)):
            c = bases[i]
            self.menus.set_title(i, extract_classname(c))
        def menu_on_change(change):
            self.selected_func = change.new
            self.init_selected_method()
        for menu in self.menus.children:
            menu.observe(menu_on_change, names='value')
        def compute_selected_method(button):
            args = []
            for i in self.inputs.children:
                try:
                    arg = i.value or i.placeholder
                    if not arg:
                        self.output.value = to_html("Argument '%s' is empty!" % i.description)
                        return
                    args.append(arg)
                except:
                    self.output.value = to_html("Could not evaluate argument '%s'" % i.description)
                    return
            try:
                alarm(TIMEOUT)
                out = self.selected_func(obj, *args)
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
        if len(self.history) <= 1:
            return
        button = Button(description='Back', icon='history', tooltip="Go back to previous object page", layout=back_button_layout)
        button.on_click(lambda event: self.pop_object()) # No back button in this new (previous object) page
        return button

    def make_new_page_button(self, obj):
        button = Button(description=str(obj), tooltip="Will close current explorer and open a new one")
        button.on_click(lambda b:self.set_object(obj))
        return button

    def display_new_value(self, obj):
        """A callback for the navigation button."""
        self.visualbox.children[0].value = str(obj)

    def get_object(self):
        return self.obj

    def set_object(self, obj):
        self.history.append(obj)
        self.obj = obj
        self.compute()

    def pop_object(self):
        if self.history:
            self.history.pop()
        if self.history:
            self.obj = self.history[-1]
        else:
            self.obj = None
        self.compute()

    def make_index(self):
        self.selected_object = None
        self.title.value = "Sage Explorer"
        self.visualbox.children = [Label("Index Page")]
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
            self.display_new_value(self.selected_object)
            self.doctab.value = to_html(change.new.__doc__)
            #self.gobutton.on_click(lambda b:self.display_new_value(self.selected_object))
            self.gobutton.on_click(lambda b:self.set_object(self.selected_object))
        for menu in self.menus.children:
            menu.observe(menu_on_change, names='value')
