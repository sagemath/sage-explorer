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
from inspect import getdoc, getsource, getmembers, getmro, ismethod, isfunction, ismethoddescriptor, isclass
from cysignals.alarm import alarm, cancel_alarm, AlarmInterrupt
from sage.misc.sageinspect import sage_getargspec
from sage.combinat.posets.posets import Poset

cell_layout = Layout(width='3em',height='2em', margin='0',padding='0')
box_layout = Layout()
css_lines = []
css_lines.append(".invisible {display: none; width: 0; height: 0}")
css_lines.append(".visible {display: table}")
css = HTML("<style>%s</style>"% '\n'.join(css_lines))
try:
    display(css)
except:
    pass # We are not in a notebook

TIMEOUT = 15 # in seconds
EXCLUDED_MEMBERS = ['__init__', '__repr__', '__str__']

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

def extract_classname(c, element_ok=True):
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
    if 'element_class' in s and not element_ok:
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


class TestBox(Box):
    """Test de l'objet Box"""
    def __init__(self):
        super(TestBox, self).__init__()
        self.elt1 = HTML("OK1")
        self.elt2 = Tab((HTML("OK2"), HTML("OK3")))
        self.children = [self.elt1, self.elt2]
        self.switch()

    def switch(self, state=0):
        if state:
            self.elt1.remove_class('visible')
            self.elt1.add_class('invisible')
            self.elt2.remove_class('invisible')
            self.elt2.add_class('visible')
            print "Should be OK2"
            return
        self.elt1.remove_class('invisible')
        self.elt1.add_class('visible')
        self.elt2.remove_class('visible')
        self.elt2.add_class('invisible')


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
        c0 = obj.__class__
        self.classname = extract_classname(c0, element_ok=False)
        self.selected_func = c0
        self.members = [x for x in getmembers(c0) if not x[0] in EXCLUDED_MEMBERS and (not x[0].startswith('_') or x[0].startswith('__')) and not 'deprecated' in str(type(x[1])).lower()]
        self.methods = [x for x in self.members if ismethod(x[1]) or ismethoddescriptor(x[1])]
        origins, overrides = method_origins(c0, [x[0] for x in self.methods])
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
                print c, len(basemembers[c])
        menus = []
        for i in range(len(bases)):
            c = bases[i]
            menus.append(Select(rows=12,
                                options = [('----', c)] + [x for x in self.methods if x[0] in basemembers[c]]
            ))
        self.menus = Accordion(menus)
        for i in range(len(bases)):
            c = bases[i]
            self.menus.set_title(i, extract_classname(c))
        self.title = Label(self.classname)
        self.visual = Textarea(repr(obj._ascii_art_()))
        self.top = HBox([self.title, self.visual])
        self.inputs = HBox()
        self.gobutton = Button(description='Run!', tooltip='Run the function or method, with specified arguments')
        self.output = HTML()
        self.worktab = VBox((self.inputs, self.gobutton, self.output))
        self.doc = HTML(to_html(self.obj.__doc__)) # Initialize to object docstring
        self.doctab = HTML() # For the method docstring
        self.tabs = Tab((self.worktab, self.doctab)) # Will be used when a method is selected
        self.tabs.set_title(0, 'Main')
        self.tabs.set_title(1, 'Help')
        self.main = Box((self.doc, self.tabs))
        self.tabs.add_class('invisible') # Hide tabs at first display
        self.bottom = HBox((self.menus, self.main))
        self.children = (self.top, self.bottom)
        self.compute()

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
            self.doctab.value += to_html(', '.join([extract_classname(x) for x in self.overrides[func.__name__]]))
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
            print func, "attr?"
            print argspec
        self.inputs.children = inputs
        self.doc.remove_class('visible')
        self.doc.add_class('invisible')
        self.tabs.remove_class('invisible')
        self.tabs.add_class('visible')

    def compute(self):
        """Get some attributes, depending on the object
        Create links between menus and output tabs"""
        # FIXME attributes
        # FIXME compute list of methods here
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
                out = self.selected_func(self.obj, *args)
                cancel_alarm()
            except AlarmInterrupt:
                self.output.value = to_html("Timeout!")
            except Exception as e:
                self.output.value = to_html(e)
                return
            self.output.value = to_html(out)
        self.gobutton.on_click(compute_selected_method)

    def get_object(self):
        return self.obj

    def set_object(self, obj):
        self.obj = obj
        self.compute()
