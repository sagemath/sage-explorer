# -*- coding: utf-8 -*-
r"""
Sage-Explorer: interactive exploration of SageMath objects in Jupyter

See :class:`SageExplorer`.

AUTHORS:
- Odile Bénassy, Nicolas Thiéry

"""
import re, os, warnings, yaml
from abc import abstractmethod
from cysignals.alarm import alarm, cancel_alarm
from cysignals.signals import AlarmInterrupt
from inspect import isclass, ismodule
from collections import deque
from ipywidgets import Box, Button, Combobox, Dropdown, GridBox, HBox, HTML, HTMLMath, Label, Layout, Text, Textarea, ToggleButton, VBox
from traitlets import Any, Bool, Dict, HasTraits, Instance, Int, Unicode, dlink, link, observe
try:
    from sage.misc.sphinxify import sphinxify
    assert sphinxify is not None
except:
    sphinxify = str
try:
    from sage.repl.rich_output import get_display_manager
    DISPLAY_MODE = get_display_manager().preferences.text
except:
    DISPLAY_MODE = 'plain'
with warnings.catch_warnings():
    warnings.filterwarnings("ignore", category=DeprecationWarning)
    from ipyevents import Event
from .explored_member import ExploredMember, _eval_in_main, get_members, get_properties
import sage_explorer._sage_catalog as sage_catalog
from ._sage_catalog import sage_catalogs
try:
    from singleton_widgets import ButtonSingleton, ComboboxSingleton, DropdownSingleton, HTMLMathSingleton, TextSingleton, TextareaSingleton, ToggleButtonSingleton
except:
    ButtonSingleton, ComboboxSingleton, DropdownSingleton, HTMLMathSingleton, TextSingleton, TextareaSingleton, ToggleButtonSingleton = Button, Combobox, Dropdown, HTMLMath, Text, Textarea, ToggleButton

title_layout = Layout(width='100%', padding='12px')
css_lines = []
css_lines.append(".visible {visibility: visible; display: table}")
css_lines.append(".invisible {visibility: hidden; display: none}")
css_lines.append(".title-level2 {font-size: 150%}")
css_lines.append(".separator {width: 1em}")
css_lines.append('.explorer-title {background-color: #005858; background-image: url("data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAB4AAAAeCAQAAACROWYpAAAABGdBTUEAALGPC/xhBQAAACBjSFJNAAB6JgAAgIQAAPoAAACA6AAAdTAAAOpgAAA6mAAAF3CculE8AAAAAmJLR0QA/4ePzL8AAAAHdElNRQfjCBQVGx7629/nAAAB60lEQVQ4y5WUQU8aQRSAv0UPGDcaJYKaCISj6VFJ6skfoEc5EUhIvWniTzFpjyb2ZJB/UBtMf0BvwA0WIfFAemqRSGJ2xwPDMLuz227nXd68ed/uvDfvPYhaZTwEAo9ylEsiEs5iAWCRjQOvs6ntCiEabLIeBqe4pkFR7mwfbEvtgDqf2QreIMVXXARP1MhQosEYIWVMgxJpKjgIPO5I6+gat7jKtcOrAufySos/UveoswGwDMASuyoAm/2Q3CT5oHSLjOTkOsQx/hYlQ46C365oUf5NJpybF9uh5XN6o0uTJl3efPYOuyZcYqq59LkkS5IkWS7oaydTSn7QYpWGDz32nR/78HvsWfVZlNmjQIGiKgWXK74E7nXBNUtSf+EnDg4D1PsupEveCCpPz/BzEyGtMWBk2EYMDFsiuqtirASeYcuRMWwZcobNW6ZqJCzPiZGwUw3WEjZ/qvv/f6rFMoskxwor5P5VJAA7tAPl2aNJk16gPFtsm3CNSazGeKEaRIs8xW5Jh0Md3eAhNioQfJtNklmRuDyr9x7TZmoENaXDROqCEa5+OB+AfSqkOQsZgNt8YigHYMj8vOW7isbmUcGPqnw+8oN6SP0RHPo3Cr7RrFukFht9Cv72fcoJ0eCX7hLdVUOETM8wyuUdTAVXcgNG490AAAAldEVYdGRhdGU6Y3JlYXRlADIwMTktMDgtMjBUMTk6Mjc6MzArMDI6MDCNIxYDAAAAJXRFWHRkYXRlOm1vZGlmeQAyMDE5LTA4LTIwVDE5OjI3OjMwKzAyOjAw/H6uvwAAAABJRU5ErkJggg=="); background-repeat: no-repeat; background-position: right;background-origin: content-box; border-radius: 4px}')
css_lines.append(".explorer-title DIV {color: seashell; padding-bottom: 2px}") # (light teal=#46C6C6)
css_lines.append(".explorer-table {border-collapse: collapse}")
css_lines.append(".explorer-flexrow {padding:0; display:flex; flex-flow:row wrap; width:99%}")
css_lines.append(".explorer-flexitem {flex-grow:1}")
css_lines.append(".explorable-value {background-color: #eee; border-radius: 4px; padding: 4px}\n.explorable-value:hover {cursor: pointer}")
global_css_code = HTML("<style>%s</style>" % '\n'.join(css_lines))

TIMEOUT = 0.5 # in seconds
MAX_LEN_HISTORY = 50
CONFIG_PROPERTIES = yaml.load(open(os.path.join(os.path.dirname(__file__),'properties.yml')), yaml.SafeLoader)


def iscatalog(obj):
    return obj == sage_catalog or obj in sage_catalogs

def _get_name(obj, standalone=False):
    if hasattr(obj, '_name'):
        return obj._name
    if hasattr(obj, 'name'):
        try:
            return obj.name()
        except:
            pass
    if hasattr(obj, '__name__'):
        return obj.__name__
    return _math_repr(obj, standalone)

def _get_visual_widget(obj):
    r"""
    Which is the specialized widget class name for viewing this object (if any)

    TESTS::

        sage: from sage.all import *
        sage: from sage_explorer._widgets import *
        sage: from sage_explorer.sage_explorer import _get_visual_widget
        sage: p = Partition([3,3,2,1])
        sage: _get_visual_widget(p).__class__
        <class 'sage_combinat_widgets.grid_view_widget.GridViewWidget'>
        sage: f(x) = x^2
        sage: w = _get_visual_widget(f)
        sage: w.name
        'x |--> x^2'
   """
    if isclass(obj) or ismodule(obj) or iscatalog(obj):
        return
    if hasattr(obj, "_widget_"):
        return obj._widget_()
    if (hasattr(obj, 'number_of_arguments') and obj.number_of_arguments() < 2) \
       or (hasattr(obj, 'plot') and not hasattr(obj, 'number_of_arguments')):
        from ._widgets import PlotWidget
        return PlotWidget(obj)

def _math_repr(obj, display_mode=None, standalone=False):
    r"""
    When Sage LaTeX implementation
    applies well to MathJax, use it.

    INPUT:

                - ``obj`` -- an object to be represented
                - ``display_mode`` -- string values of %display magic
                - ``standalone`` -- a boolean

    OUTPUT: a (unicode) string

    TESTS::

        sage: from sage_explorer.sage_explorer import _math_repr
        sage: _math_repr(42, display_mode='latex')
        '$42$'
        sage: _math_repr(ZZ, display_mode='latex')
        '$\\Bold{Z}$'
        sage: from sage.combinat.tableau import Tableau
        sage: t = Tableau([[1, 2], [3], [4]])
        sage: _math_repr(t)
        '[[1, 2], [3], [4]]'
        sage: _math_repr(t, display_mode='unicode_art', standalone=True)
        '<pre>┌───┬───┐\n│ 1 │ 2 │\n├───┼───┘\n│ 3 │\n├───┤\n│ 4 │\n└───┘</pre>'
        sage: _math_repr(t, display_mode='unicode_art', standalone=False)
        '[[1, 2], [3], [4]]'
        sage: _math_repr(0)
        '0'
    """
    if obj is None:
        return ''
    if not display_mode:
        try:
            display_mode = get_display_manager().preferences.text
        except:
            display_mode = DISPLAY_MODE
    if display_mode=='latex' and hasattr(obj, '_latex_'):
        try:
            s = obj._latex_()
        except:
            s = str(obj) # signature is sometimes different
        if 'tikz' not in s and 'raisebox' not in s:
            return "${}$" . format(s)
    if display_mode=='unicode_art' and hasattr(obj, '_unicode_art_'):
        try:
            s = obj._unicode_art_()
        except:
            pass
        else:
            if standalone: # for ExplorableValue
                return "<pre>{}</pre>" . format(obj._unicode_art_())
            else: # for widget labels: back to plain representation
                pass
    # not display_mode or display_mode=='plain'
    if hasattr(obj, '__name__') and obj.__name__ and not obj.__name__.startswith('<'):
        return obj.__name__
    if hasattr(obj, '__str__') and obj.__str__() and not obj.__str__().startswith('<'):
        s = obj.__str__()
    else:
        s = obj.__doc__.strip()
    if '\n' in str(s): # for limited size widget labels
        return s[:s.find('\n')]
    else:
        return s

def switch_visibility(widget, visibility):
    r"""
    Display/hide a widget with CSS.
    """
    if visibility:
        widget.remove_class('invisible')
        widget.add_class('visible')
    else:
        widget.remove_class('visible')
        widget.add_class('invisible')


class Title(Label):
    r"""A title of various levels

    For HTML display
    """
    def __init__(self, value='', level=1):
        super(Title, self).__init__()
        self.value = value
        self.add_class('title-level%d' % level)


class MathTitle(HTMLMathSingleton):
    r"""A title of various levels

    For HTML display
    """
    def __init__(self, value='', level=1):
        super(MathTitle, self).__init__(value)
        self.value = _math_repr(value)
        self.add_class("title-level%d" % level)


class Separator(Label):
    r"""
    A separator with a letter ot symbol in it.
    """

    def __init__(self, s):
        super(Separator, self).__init__(
            s,
            layout=Layout(padding='0 4px')
        )
        self.add_class("separator")


class HelpButton(ToggleButtonSingleton):
    r"""
    """
    def __init__(self, obj=None, target=None):
        super(HelpButton, self).__init__(
            description='?',
            _tooltip="Click for full documentation"
        )
        self.add_class("separator")
        self.click_event = Event(
            source=self,
            watched_events=['click']
        )
        self.set_target(obj, target)

    def set_focusable(self, focusable):
        r"""
        For compatibility.
        """
        if focusable is True:
            self.allow_focus()
        else:
            self.disallow_focus()

    def set_target(self, obj, target):
        def open_help(event):
            if obj and target:
                if self.value:
                    target.content = obj.__doc__
                    switch_visibility(target, True)
                else:
                    target.reset()
        self.click_event._dom_handlers.callbacks.clear() # Remove previous handler
        self.click_event.on_dom_event(open_help) # Display `obj` help on click


class ExplorableHistory(deque):

    def __init__(self, obj=None, initial_name=None, previous_history=[]):
        super(ExplorableHistory, self).__init__(previous_history)
        if obj is not None:
            self.append(obj)
        self.initial_name = self.get_initial_name(value=obj)

    @staticmethod
    def get_initial_name(value=None, test_sh_hist=[]):
        r"""Attempt to deduce the widget value variable name
        from notebook input history.
        In case it is not found, or not a string, set to `Hist[0]`.

        TESTS::

            sage: from sage_explorer.sage_explorer import ExplorableHistory
            sage: h = ExplorableHistory()
            sage: h.get_initial_name(value=42) is None
            True
            sage: import __main__
            sage: eval(compile('x=42','<string>', 'exec'))
            sage: x
            42
            sage: h.get_initial_name(value=42, test_sh_hist=["w = explore(42)", "w"]) is None
            True
            sage: h.get_initial_name(value=42, test_sh_hist=["x=42", "w = explore(x)", "w"])
            'x'
            sage: h.get_initial_name(value=42, test_sh_hist=["x=42", "w = explore(x)", "explore(43)", "w"])
            'x'
        """
        initial_name = None
        try:
            sh_hist = get_ipython().history_manager.input_hist_parsed[-50:]
            test_locs = {}
        except:
            sh_hist = test_sh_hist # We are in the test environment
            test_locs = {'x': 42}
        sh_hist.reverse()
        for l in sh_hist:
            if 'explore' in l:
                m = re.search(r'explore[ ]*\([ ]*([^)]+)\)', l)
                if m:
                    initial_name_candidate = m.group(1).strip()
                    try:
                        if initial_name_candidate[0].isdigit():
                            continue
                    except:
                        if not value:
                            return initial_name_candidate
                    try:
                        if _eval_in_main(initial_name_candidate, locals=test_locs) == value:
                            initial_name = initial_name_candidate
                            break
                    except:
                        pass
        return initial_name

    def push(self, obj):
        r"""
        Push the history, ie append
        an object and increment index.

        TESTS::

            sage: from sage_explorer.sage_explorer import ExplorableHistory
            sage: h = ExplorableHistory(42)
            sage: h.push("An object")
            sage: h
            ExplorableHistory([42, 'An object'])
        """
        self.append(obj)
        self.truncate(MAX_LEN_HISTORY)

    def pop(self, n=1):
        r"""
        Pop the history, ie pop the list
        and decrement index.

        TESTS::

            sage: from sage_explorer.sage_explorer import ExplorableHistory
            sage: h = ExplorableHistory("A first value")
            sage: h.push(42)
            sage: h.pop()
            42
            sage: h
            ExplorableHistory(['A first value'])
            sage: h.pop()
            Traceback (most recent call last):
            ...
            Exception: No more history!
            sage: h = ExplorableHistory(1)
            sage: for i in range(2,6): h.push(i)
            sage: h.pop(4)
            2
            sage: h
            ExplorableHistory([1])
        """
        for i in range(n):
            val = super(ExplorableHistory, self).pop()
            if not self:
                raise Exception("No more history!")
        return val

    def get_item(self, i=None):
        r"""
        Pop the history, ie pop the list
        and decrement index.

        TESTS::

            sage: from sage_explorer.sage_explorer import ExplorableHistory
            sage: h = ExplorableHistory("A first value")
            sage: h.push(42)
            sage: h.get_item(1)
            42
            sage: h.get_item(0)
            'A first value'
            sage: h.get_item()
            42
        """
        if i is None:
            return self[-1]
        return self.__getitem__(i)

    def make_menu_options(self):
        r"""
        Truncate the history, ie pop values
        from the start, until list becomes small enough.

        TESTS::

            sage: from sage_explorer.sage_explorer import ExplorableHistory
            sage: h = ExplorableHistory("A first value")
            sage: h.make_menu_options()
            [('Hist[0]: A first value', 0)]
            sage: for i in range(2): h.push(i)
            sage: h.make_menu_options()
            [('Hist[0]: A first value', 0), ('Hist[1]: 0', 1), ('Hist[2]: 1', 2)]
        """
        def make_option(label, i):
            return ("{}: {}".format(label, _get_name(self[i])), i)
        first_label = self.initial_name or "Hist[0]"
        return [make_option(first_label, 0)] + \
            [make_option("Hist[{}]". format(i+1), i+1) for i in range(self.__len__()-1)]

    def truncate(self, max=MAX_LEN_HISTORY):
        r"""
        Truncate the history, ie pop values
        from the start, until list becomes small enough.

        TESTS::

            sage: from sage_explorer.sage_explorer import ExplorableHistory
            sage: h = ExplorableHistory("A first value")
            sage: for i in range(55): h.push(i)
            sage: len(h)
            50
            sage: h.truncate(10)
            sage: h
            ExplorableHistory([45, 46, 47, 48, 49, 50, 51, 52, 53, 54])
        """
        shift = self.__len__() - max
        if shift < 1:
            return
        for i in range(shift):
            self.popleft()


class ExplorableValue(HTMLMathSingleton):
    r"""
    A repr string with a link to a Sage object.

    TESTS::

        sage: from sage_explorer.sage_explorer import ExplorableValue
        sage: v = ExplorableValue(42)
        sage: v.new_val
        sage: e = {'type': 'click'}
        sage: v.click_event._dom_handlers.callbacks[0](e)
        sage: v.new_val
        42
    """
    explorable = Any() # Some computed math object
    new_val = Any() # Overall value. Will be changed when explorable is clicked. `value` being reserved by ipywidgets.

    def __init__(self, explorable, display=None, initial_value=None):
        if type(explorable) is type(int(1)): # a hack for non-Sage integers
            from sage.rings.integer import Integer
            self.explorable = Integer(explorable)
        else:
            self.explorable = explorable
        if initial_value is not None:
            self.new_val = initial_value
        super(ExplorableValue, self).__init__(layout=Layout(margin='1px'))
        self.add_class('explorable-value')
        self._tooltip = "Click to explore this value"
        self.reset(display)
        self.click_event = Event(
            source=self,
            watched_events=['click', 'keyup']
        )
        def set_new_val(event):
            r"""
            Check event type and key,
            then copy `explorable` to `new_val`.

            INPUT:

                - ``event`` -- a dictionary
            """
            if event['type'] == 'click' or event['key'] == 'Enter':
                self.new_val = self.explorable
        self.click_event.on_dom_event(set_new_val) # Handle clicking


    def reset(self, display):
        r"""
        `explorable` has changed: compute HTML value.
        """
        if display:
            self.value = display
        else:
            self.value = _get_name(self.explorable, standalone=True)


class ExplorableCell(Box):
    r"""
    A text box that contains one or several explorable value(s).

    TESTS::

        sage: from sage_explorer.sage_explorer import ExplorableCell
        sage: c = ExplorableCell(42)
        sage: len(c.children)
        1
        sage: c = ExplorableCell(ZZ)
        sage: len(c.children)
        1
        sage: c = ExplorableCell([42, 'a string', ZZ])
        sage: len(c.children)
        7
    """
    explorable = Any() # can be a single value or a list or a tuple
    new_val = Any() # when [one of] the value(s) is clicked

    def __init__(self, explorable, initial_value=None, **kws):
        r"""
        A text box to display explorable value(s).
        """
        self.explorable = explorable
        if initial_value is not None:
            self.new_val = initial_value
        super(ExplorableCell, self).__init__(**kws)
        self.reset()

    def reset(self):
        r"""
        `explorable` has changed: compute all content.
        """
        children = []
        self.explorables = []
        if type(self.explorable) in [type([]), type(()), set, frozenset]:
            if type(self.explorable) == type([]):
                children.append(Separator('['))
            elif type(self.explorable) == type(()):
                children.append(Separator('('))
            else: # Here, make both the set and its elements explorable
                ev = ExplorableValue(
                    self.explorable,
                    display='{',
                    initial_value=self.new_val
                )
                dlink((ev, 'new_val'), (self, 'new_val'))
                children.append(ev)
            for e in self.explorable:
                ev = ExplorableValue(e, initial_value=self.new_val)
                dlink((ev, 'new_val'), (self, 'new_val')) # Propagate click
                self.explorables.append(ev)
                children.append(ev)
                children.append(Separator(','))
            children.pop()
            if type(self.explorable) == type([]):
                children.append(Separator(']'))
            elif type(self.explorable) == type(()):
                children.append(Separator(')'))
            else:
                children.append(Separator('}'))
        elif self.explorable is not None: # treated as a single value
            ev = ExplorableValue(self.explorable, initial_value=self.new_val)
            self.explorables.append(ev)
            dlink((ev, 'new_val'), (self, 'new_val')) # Propagate click
            children.append(ev)
        self.children = children

    def set_focusable(self, focusable):
        r"""
        For compatibility.
        """
        if focusable is True:
            for ev in self.explorables:
                ev.allow_focus()
        elif focusable is False:
            for ev in self.explorables:
                ev.disallow_focus()


class ExplorerComponent(Box):
    r"""
    Common methods to all components.

    TESTS::

        sage: from sage_explorer.sage_explorer import ExplorerComponent
        sage: c = ExplorerComponent("Initial value")
        sage: c.value = 42
    """
    value = Any()

    def __init__(self, obj, **kws):
        r"""
        Common methods to all components.

        TESTS::

            sage: from sage_explorer.sage_explorer import ExplorerComponent
            sage: c = ExplorerComponent("Initial value")
            sage: c.value = 42
        """
        self.donottrack = True
        self.value = obj
        super(ExplorerComponent, self).__init__(**kws)
        self.reset()
        self.donottrack = False

    def set_focusable(self, focusable):
        if hasattr(self, 'allow_focus'): # a Singleton
            if focusable is True:
                self.allow_focus()
            elif focusable is False:
                self.disallow_focus()
        elif hasattr(self, 'children'):
            for child in self.children:
                if hasattr(child, 'allow_focus'):
                    if focusable is True:
                        child.allow_focus()
                    elif focusable is False:
                        child.disallow_focus()

    @abstractmethod
    def reset(self):
        r"""
        Reset component when `value` is changed.

        TESTS::

            sage: from sage_explorer.sage_explorer import ExplorerComponent
            sage: c = ExplorerComponent("Initial value")
            sage: c.value = 42
        """
        pass

    @observe('value')
    def value_changed(self, change):
        r"""
        What to do when the value has been changed.

        INPUT:

            - ``change`` -- a change Bunch

        TESTS::

            sage: from sage_explorer.sage_explorer import ExplorerComponent
            sage: obj = Tableau([[1, 2, 5, 6], [3], [4]])
            sage: new_obj = 42
            sage: p = ExplorerComponent(obj)
            sage: p.value = new_obj

        """
        if self.donottrack:
            return
        old_val = change.old
        new_val = change.new
        actually_changed = (id(new_val) != id(old_val))
        if actually_changed:
            self.reset()


class ExplorerTitle(ExplorerComponent):
    r"""The sage explorer title bar
    """
    content = Unicode('')

    def __init__(self, obj):
        self.donottrack = True
        super(ExplorerTitle, self).__init__(
            obj,
            children=(
                MathTitle('', 2),
                global_css_code),
            layout=Layout(padding='5px 10px')
        )
        self.donottrack = False
        self.add_class("explorer-title")

    def reset(self):
        if _get_name(self.value):
            self.content = _get_name(self.value)
        else:
            self.content = '{}' . format(_get_name(self.value))
        self.children[0].value = "Exploring: {}" . format(self.content)


class ExplorerDescription(ExplorerComponent):
    r"""The sage explorer object description
    """
    content = Unicode('')

    def __init__(self, obj, help_target=None):
        self.help_target = None
        super(ExplorerDescription, self).__init__(
            obj,
            children=(
                HTMLMathSingleton(),
                HelpButton(obj, help_target)
            )
        )
        self.add_class("explorer-description")
        if help_target:
            self.set_help_target(help_target)
        dlink((self, 'content'), (self.children[0], 'value'))

    def set_help_target(self, target):
        self.help_target = target
        self.children[1].set_target(self.value, target)
        def open_help(event):
            if event['key'] in ['?', 'Enter'] and self.value and target:
                target.content = self.value.__doc__
                switch_visibility(target, True)
                self.children[1].value = True
        keyboard_event = Event(
            source=self.children[0],
            watched_events=['keyup']
        )
        keyboard_event.on_dom_event(open_help) # Display `self.value` help on '?'/'Enter'

    def reset(self):
        if self.value.__doc__:
            self.content = [l for l in self.value.__doc__.split("\n") if l][0].strip()
        else:
            self.content = ''
        if self.help_target:
            self.set_help_target(self.help_target) # re-recreate help button handler


class ExplorerProperties(ExplorerComponent, GridBox):
    r"""
    Display object properties as a table.

    TESTS::

        sage: from sage_explorer.sage_explorer import ExplorerProperties
        sage: p = ExplorerProperties(42)
    """
    def __init__(self, obj):
        super(ExplorerProperties, self).__init__(
            obj,
            layout=Layout(border='1px solid #eee', width='100%', grid_template_columns='auto auto')
        )
        self.add_class("explorer-table")

    def reset(self):
        children = []
        self.explorables = []
        for p in get_properties(self.value, Settings.properties):
            explorable = getattr(self.value, p.name).__call__()
            children.append(Box((Label(p.prop_label),), layout=Layout(border='1px solid #eee')))
            e = ExplorableCell(explorable, initial_value=self.value)
            self.explorables.append(e)
            dlink((e, 'new_val'), (self, 'value')) # Propagate explorable if clicked
            children.append(e)
        self.children = children


class ExplorerVisual(ExplorerComponent):
    r"""
    The sage explorer visual representation
    """
    def __init__(self, obj):
        super(ExplorerVisual, self).__init__(
            obj,
            layout = Layout(right='0')
        )

    def reset(self):
        w = _get_visual_widget(self.value)
        if hasattr(w, 'disallow_inside_focus'):
            w.disallow_inside_focus()
        if w:
            self.children = (w,)
        else:
            if hasattr(self.value, '__ascii_art__'):
                self.children = (
                    TextareaSingleton(
                        repr(self.value._ascii_art_()),
                        rows=8
                    ),)
            else:
                self.children = ()
        if self.children:
            dlink((self.children[0], 'value'), (self, 'value'))


class ExplorerHistory(ExplorerComponent):
    r"""
    A text input to give a name to a math object
    """
    _history = Instance(ExplorableHistory)
    _history_len = Int()
    _history_index = Int()

    def __init__(self, obj, history=None):
        r"""
        Which is the specialized widget class name for viewing this object (if any)

        TESTS::

            sage: from sage_explorer.sage_explorer import ExplorerHistory, ExplorableHistory
            sage: h = ExplorerHistory('Initial value')
            sage: h._history
            ExplorableHistory(['Initial value'])
            sage: h._history.push(42)
            sage: h._history = ExplorableHistory(43, previous_history=list(h._history))
            sage: h._history
            ExplorableHistory(['Initial value', 42, 43])
        """
        self.donottrack = True
        self._history = history or ExplorableHistory(obj)
        super(ExplorerHistory, self).__init__(
            obj,
            children=(DropdownSingleton(
                layout=Layout(width='7em', padding='0', margin='0')
            ),),
            layout=Layout(padding='0')
        )
        self.donottrack = False
        # User input
        def dropdown_selection(change):
            if self.donottrack:
                return
            self.donottrack = True
            self._history_index = change.new
            self.value = self._history.get_item(change.new)
            self.donottrack = False
        self.children[0].observe(dropdown_selection, names='value')

    def reset(self):
        r"""
        Value has changed.
        """
        self.compute_dropdown()

    def compute_dropdown(self):
        r"""
        History has changed
        """
        self.children[0].options = self._history.make_menu_options()
        self.children[0].value = self._history_index
        if self._history_len > 1:
            self.children[0].disabled = False
            self.children[0]._tooltip = 'Click to show history'
        else:
            self.children[0].disabled = True
            self.children[0]._tooltip = ''

    @observe('_history_len')
    def history_changed(self, change):
        r"""
        _history_len was changed by means of explorer navigation (click)
        """
        if self.donottrack:
            return
        self.donottrack = True
        self.compute_dropdown()
        self.donottrack = False


class ExplorerMethodSearch(ExplorerComponent):
    r"""
    A widget to search a method

    TESTS::

        sage: from sage_explorer.sage_explorer import ExplorerMethodSearch
        sage: s = ExplorerMethodSearch(42)
    """
    explored = Instance(ExploredMember) # to share with ExplorerArgs and ExplorerHelp

    def __init__(self, obj, help_target=None, menu_type="combo"):
        if menu_type == "dropdown":
            menu_widget_class = DropdownSingleton
        else:
            menu_widget_class = ComboboxSingleton
        super(ExplorerMethodSearch, self).__init__(
            obj,
            children=(
                menu_widget_class(
                    placeholder="Enter name ; use '?' for help"
                ),)
        )
        if help_target:
            self.set_help_target(help_target)
        def method_changed(change):
            selected_method = change.new
            if selected_method in self.members_dict:
                self.explored = self.members_dict[selected_method]
        # we do not link directly for not all names deserve a computation
        self.children[0].observe(method_changed, names='value')

    def set_display(self, s):
        self.children[0].value = s

    def reset(self):
        r"""
        Setup the combobox.
        """
        if isclass(self.value) or ismodule(self.value) or iscatalog(self.value):
            cls = self.value
        else:
            cls = self.value.__class__
        self.members = get_members(cls, Settings.properties) # Here, we both have a list and a dict
        self.members_dict = {m.name: m for m in self.members}
        self.children[0].options=[m.name for m in self.members]
        try:
            self.children[0].value = '' # case Combobox
        except:
            self.children[0].value = None # case Dropdown
        self.explored = ExploredMember('')

    def set_help_target(self, target):
        if not target:
            return
        def open_help(event):
            if event['key'] == '?' and self.explored:
                if not hasattr(self.explored, 'doc'):
                    self.explored.compute_doc()
                target.content = self.explored.doc
                switch_visibility(target, True)
        click_event = Event(
            source=self,
            watched_events=['keyup']
        )
        click_event.on_dom_event(open_help) # Display `explored` help on click


class ExplorerArgs(ExplorerComponent):
    r"""
    A text box to input method arguments
    """
    content = Unicode('')
    explored = Instance(ExploredMember) # shared by ExplorerMethodSearch

    def __init__(self, obj=None):
        r"""
        A text box to input method arguments.

        TESTS::

            sage: from sage_explorer.sage_explorer import ExplorerArgs
            sage: a = ExplorerArgs(42)
        """
        self.default_placeholder = "Enter arguments ; for example: 3,7,pi=3.14"
        super(ExplorerArgs, self).__init__(
            obj,
            children=(TextSingleton(
                '',
                layout=Layout(width="100%")
            ),)
        )
        self.add_class("explorer-flexitem")
        def explored_changed(change):
            explored = change.new
            if not explored.name:
                self.reset()
                return
            if not hasattr(explored, 'args'):
                explored.compute_argspec()
            args, defaults = explored.args, explored.defaults
            if args and args != ['self']:
                self.children[0].disabled = False
                if defaults:
                    self.children[0].placeholder = str(defaults)
                else:
                    self.children[0].placeholder = self.default_placeholder
            else:
                self.children[0].value = ''
                self.children[0].placeholder = ''
                self.children[0].disabled = True
        self.observe(explored_changed, names='explored')
        dlink((self.children[0], 'value'), (self, 'content'))

    def reset(self):
        self.children[0].value = ''
        self.children[0].disabled = False
        self.children[0].placeholder = self.default_placeholder


class ExplorerRunButton(ButtonSingleton):
    r"""
    A button for running methods in the explorer.

    TESTS::

        sage: from sage_explorer.sage_explorer import ExplorerRunButton
        sage: b = ExplorerRunButton()
    """
    def __init__(self):
        super(ExplorerRunButton, self).__init__(
            description = 'Run!',
            tooltip = 'Evaluate the method with the specified arguments',
            layout = Layout(width='4em', right='0')
        )

    def set_focusable(self, focusable):
        r"""
        For compatibility.
        """
        if focusable is True:
            self.allow_focus()
        elif focusable is False:
            self.disallow_focus()


class ExplorerOutput(ExplorerComponent):
    r"""
    A text box to output method results.

    TESTS::

        sage: from sage_explorer.sage_explorer import ExplorerOutput
        sage: o = ExplorerOutput(42)
    """
    def __init__(self, obj=None, explorable=None):
        r"""
        A text box to output method results.
        """
        self.output = ExplorableCell(explorable, initial_value=obj)
        self.output.add_class('invisible')
        def output_changed(change):
            change.owner.reset()
            if change.new:
                switch_visibility(change.owner, True)
            else:
                switch_visibility(change.owner, False)
        self.output.observe(output_changed, names='explorable') # display/hide output
        self.error = HTML("")
        self.error.add_class("ansi-red-fg")
        super(ExplorerOutput, self).__init__(
            obj,
            children=(self.output, self.error),
            layout = Layout(padding='2px 50px 2px 2px')
        )

    def reset(self):
        self.output.new_val = self.value
        self.output.explorable = None
        switch_visibility(self.output, False)
        self.error.value = ''
        dlink((self.output, 'new_val'), (self, 'value')) # propagate if output is clicked

    def set_output(self, obj):
        self.output.explorable = obj
        self.output.value = _get_name(obj)
        self.error.value = ''
        #self.output.switch_visibility(True)

    def set_error(self, err):
        self.output.explorable = None
        self.output.value = ''
        self.error.value = '<span class="ansi-red-fg">Error: {}</span>' .format(err)


class ExplorerHelp(ExplorerComponent):
    r"""
    An expandable box for object or method help text.

    TESTS::

        sage: from sage_explorer.sage_explorer import ExplorerHelp
        sage: h = ExplorerHelp(42)
    """
    content = Unicode('')
    explored = Instance(ExploredMember) # shared by ExplorerMethodSearch

    def __init__(self, obj):
        r"""
        A box for object or method help text.
        """
        super(ExplorerHelp, self).__init__(
            obj,
            children=(HTMLMathSingleton(),),
            layout=Layout(width='99%', padding='0', border='1px solid grey')
        )
        def explored_changed(change):
            explored = change.new
            if explored.name:
                if not hasattr(explored, 'doc'):
                    explored.compute_doc()
                self.content = explored.doc
                switch_visibility(self, True)
            else:
                self.content = ''
                switch_visibility(self, False)
        self.observe(explored_changed, names='explored')

    def reset(self):
        self.donottrack = False
        try:
            self.content = sphinxify(self.value.__doc__)
        except:
            self.content = "Cannot retrieve help!"
        switch_visibility(self, False)

    @observe('content')
    def content_changed(self, change):
        r"""
        Actually display the docstring
        """
        if self.donottrack:
            return
        if change.new:
            formatted_content = sphinxify(change.new)
            if 'text/html' in formatted_content and formatted_content['text/html']:
                self.children[0].value = formatted_content['text/html']
            elif 'text/plain' in formatted_content:
                self.children[0].value = formatted_content['text/plain']
            else: # case sphinxify=str
                self.children[0].value = formatted_content
        else:
            self.children[0].value = ''


class ExplorerCodeCell(ExplorerComponent):
    r"""
    A box containing a code cell.

    TESTS::

        sage: from sage_explorer.sage_explorer import ExplorerCodeCell
        sage: cc = ExplorerCodeCell(42)
    """
    content = Unicode('')
    new_val = Any()

    def __init__(self, obj, standalone=False):
        super(ExplorerCodeCell, self).__init__(
            obj,
            children=(TextareaSingleton(
                placeholder="Enter code ; shift-enter to evaluate",
                description_tooltip="Special values: Use '_' for your object, 'Hist' for our history\nand '__explorer__' for the current explorer.\nExamples:\n    3*_ + 1 + Hist[1]",
                rows = 0,
                layout=Layout(border='1px solid #eee', width='99%')
            ),)
        )
        link((self.children[0], 'value'), (self, 'content'))
        self.run_event = Event(
            source=self.children[0],
            watched_events=['keyup']
        )
        def launch_evaluation(event):
            if event['key'] == 'Enter' and (event['shiftKey'] or event['ctrlKey']):
                self.evaluate()
                #self.children[0].value = str(self.new_val)
        if standalone: # actually we want to trigger that from the explorer
            self.run_event.on_dom_event(launch_evaluation)

    def reset(self):
        self.content = ''
        self.new_val = None

    def evaluate(self, l=None, o=None, e=None):
        r"""
        Evaluate the code cell
        `l` being a dictionary of locals.

        INPUT:

            * `l` -- a locals dictionary ; defaults to {"_": self.value}
            * `o` -- an output widget
            * `e` -- an error output widget

        TESTS::

            sage: from sage_explorer.sage_explorer import ExplorerCodeCell
            sage: c = ExplorerCodeCell(42)
            sage: c.content = "1 + 2"
            sage: c.evaluate()
            sage: c.new_val
            3
        """
        g = globals() # the name space used by the usual Jupyter cells
        l = l or {"_": self.value}
        local_names = l.keys()
        code = compile(self.content, '<string>', 'eval')
        try:
            result = eval(code, g, l)
        except Exception as err:
            if e:
                e.set_error(err)
            else:
                self.content = "Evaluation error: %s" % err
                self.add_class("error")
            return
        if result is None: # the code may have triggered some assignments
            self.content = "result is None"
            for name, value in l.items():
                if name not in local_names:
                    g[name] = value
        elif o: # output somewhere else
            o.set_output(result)
            self.reset()
        else: # output here
            self.content = str(result)
            self.new_val = result


"""
DEFAULT_COMPONENTS = [
    ExplorerTitle,
    ExplorerDescription,
    ExplorerProperties,
    ExplorerVisual,
    ExplorerHistory,
    ExplorerMethodSearch,
    ExplorerArgs,
    ExplorerRunButton,
    ExplorerOutput,
    ExplorerHelp,
    ExplorerCodeCell
]"""
DEFAULT_COMPONENTS = {
    'titlebox': ExplorerTitle,
    'descriptionbox': ExplorerDescription,
    'propsbox': ExplorerProperties,
    'visualbox': ExplorerVisual,
    'histbox': ExplorerHistory,
    'searchbox': ExplorerMethodSearch,
    'argsbox': ExplorerArgs,
    'runbutton': ExplorerRunButton,
    'outputbox': ExplorerOutput,
    'helpbox': ExplorerHelp,
    'codebox': ExplorerCodeCell
    }

class SageExplorer(VBox):
    r"""
    Sage-Explorer: interactive exploration of SageMath objects in Jupyter

    INPUT:

    - `o` -- an object

    OUTPUT: a Jupyter widget

    Running `explore(o)` opens an interactive page displaying `o`
    together with contextual information:
    - rich display(s) of the object (e.g. LaTeX formula, picture, or
      interactive widget depending on availability;
    - a selection of properties, that is relevant invariants or
      related objects;
    - a list of operations (methods) available for the object
    - documentation.

    Following the metaphor of a web browser, the user can then
    visually explore SageMath by navigating between objects along
    properties or method calls.

    EXAMPLES:

    Explore various objects::

        sage: from sage_explorer import explore

        sage: explore(SymmetricGroup(3))
        SageExplorer(...)

        sage: explore(Partition([3,2,1,1]))
        SageExplorer(...)

        sage: explore(graphs.PetersenGraph())
        SageExplorer(...)

    Explore Sage's catalog of graphs::

        sage: explore(graphs)
        SageExplorer(...)

    Explore Sage as a whole, starting from Sage's catalog of
    catalogs::

        sage: explore()
        SageExplorer(...)

    The selection of properties is made based on the semantic of
    ``o``, typically encoded in its category and class. For example, a
    finite (enumerated) set will have its cardinality displayed; a
    field its characteristics. This can be viewed and configured using
    the explorer's settings::

        sage: explore.settings.properties
        ...
         'cardinality': [{'in': 'EnumeratedSets.Finite'}],
        ...

    This adds the property ``number of vertices`` to Sage's graphs::

        sage: explore.settings.add_property('num_verts',
        ....:                               clsname='Graph',
        ....:                               label='number of vertices')
        sage: explore(graphs.PetersenGraph())
        SageExplorer(...)

    Users are most welcome to suggest additions to the default
    configuration, e.g. by contacting the authors or posting an issue
    on `Sage-Explorer's GitHub repository <https://github.com/sagemath/sage-explorer>`_.
    """

    value = Any()
    _history = Instance(ExplorableHistory)
    _history_len = Int()
    _history_index = Int()
    components = Dict() # A list of widgets ; really a trait ?

    def __init__(self, obj=None, components=DEFAULT_COMPONENTS, test_mode=False):
        """
        TESTS::

            sage: from sage_explorer.sage_explorer import SageExplorer
            sage: t = StandardTableaux(15).random_element()
            sage: widget = SageExplorer(t, test_mode=True)
            sage: type(widget.value)
            <class 'sage.combinat.tableau.StandardTableaux_all_with_category.element_class'>
            sage: len(widget._history)
            1
        """
        self.test_mode = test_mode
        self.donottrack = True # Prevent any interactivity while creating the widget
        super(SageExplorer, self).__init__()
        if obj is None:
            obj = sage_catalog
        self.value = obj
        self._history = ExplorableHistory(obj) #, initial_name=self.initial_name)
        self._history_len = 1 # Needed to activate history propagation
        self._history_index = 0
        self.components = components
        if not test_mode:
            self.create_components()
            self.implement_interactivity()
            self.draw()
        self.donottrack = False

    def __repr__(self):
        r"""
        A readable representation string.

        TESTS::

            sage: from sage_explorer import explore
            sage: explore(42)
            SageExplorer(42)
        """
        return "SageExplorer({})" . format(self.value)

    def reset(self):
        self.donottrack = True
        for name in self.components:
            if name not in ['runbutton', 'codebox']:
                setattr(getattr(self, name), 'value', self.value)
        self.donottrack = False

    def create_components(self):
        r"""
        Create all components for the explorer.

        TESTS::

            sage: from sage_explorer import SageExplorer
            sage: e = SageExplorer(42)
            sage: e.create_components()
        """
        for name in self.components:
            if name == 'runbutton':
                setattr(self, name, self.components[name].__call__())
            elif name == 'histbox':
                setattr(self, name, self.components[name].__call__(
                    self.value,
                    history=self._history
                ))
            else:
                setattr(self, name, self.components[name].__call__(self.value))

    def implement_interactivity(self):
        r"""
        Implement links and observers on explorer components.

        TESTS::

            sage: from sage_explorer import SageExplorer
            sage: e = SageExplorer(42)
            sage: e.create_components()
            sage: e.implement_interactivity()
        """
        if self.test_mode:
            self.donottrack = True # Prevent any interactivity while installing the links
        if 'descriptionbox' in self.components and 'helpbox' in self.components:
            self.descriptionbox.set_help_target(self.helpbox)
        if 'propsbox' in self.components:
            dlink((self.propsbox, 'value'), (self, 'value')) # Handle the clicks on property values
        if 'visualbox' in self.components:
            dlink((self.visualbox, 'value'), (self, 'value')) # Handle the visual widget changes
        if 'histbox' in self.components:
            dlink((self, '_history_len'), (self.histbox, '_history_len')) # Propagate clicked navigation
            link((self.histbox, '_history_index'), (self, '_history_index')) # Handle history selection and propagate clicked navigation
            def handle_history_selection(change):
                self.donottrack = True # so we do not push history
                self.value = self._history.get_item(self._history_index)
                self.reset()
                self.donottrack = False
            self.observe(handle_history_selection, names='_history_index')
        if 'searchbox' in self.components and 'argsbox' in self.components:
            dlink((self.searchbox, 'explored'), (self.argsbox, 'explored'))
        if 'searchbox' in self.components and 'argsbox' in self.components and 'outputbox' in self.components:
            def compute_selected_member(button=None):
                member_name = self.searchbox.explored.name
                member_type = self.searchbox.explored.member_type
                args = self.argsbox.content
                try:
                    if AlarmInterrupt:
                        alarm(TIMEOUT)
                    if 'attribute' in member_type:
                        out = _eval_in_main("__obj__.{}" . format(member_name), locals={"__obj__": self.value})
                    else:
                        out = _eval_in_main("__obj__.{}({})".format(member_name, args), locals={"__obj__": self.value})
                    if AlarmInterrupt:
                        cancel_alarm()
                except AlarmInterrupt:
                    self.outputbox.set_error("Timeout!")
                    return
                except Exception as e:
                    if AlarmInterrupt:
                        cancel_alarm()
                    self.outputbox.set_error(e)
                    return
                self.outputbox.set_output(out)
                self.searchbox.set_display(member_name) # avoid any trailing '?'
                if 'helpbox' in self.components:
                    self.helpbox.reset() # empty help box
        if 'runbutton' in self.components:
            self.runbutton.on_click(compute_selected_member)
            enter_event = Event(source=self.runbutton, watched_events=['keyup'])
            def run_button(event):
                if event['key'] == 'Enter':
                    compute_selected_member()
            enter_event.on_dom_event(run_button)
        if 'outputbox' in self.components:
            dlink((self.outputbox, 'value'), (self, 'value')) # Handle the clicks on output values
            #def new_clicked_value(change):
            #    self.push_value(change.new)
            #self.outputbox.observe(new_clicked_value, names='value')
            enter_output_event = Event(source=self.outputbox, watched_events=['keyup'])
            def enter_output(event):
                if event['key'] == 'Enter' and self.outputbox.output.explorable:
                    self.value = self.outputbox.output.explorable
            enter_output_event.on_dom_event(enter_output) # Enter-key triggered shortcut on all the output line
        if 'searchbox' in self.components and 'helpbox' in self.components:
            self.searchbox.set_help_target(self.helpbox)
            def empty_helpbox(change):
                self.helpbox.reset()
            self.searchbox.observe(empty_helpbox, names='explored')
        if 'codebox' in self.components:
            def launch_evaluation(event):
                if event['key'] == 'Enter' and (event['shiftKey'] or event['ctrlKey']):
                    locs = {"_": self.value, "__explorer__": self, "Hist": list(self._history)}
                    if self._history.initial_name:
                        locs[self._history.initial_name] = self._history[0]
                    self.codebox.evaluate(l=locs, o=self.outputbox, e=self.outputbox)
            self.codebox.run_event.on_dom_event(launch_evaluation)
        if self.test_mode:
            self.donottrack = False

    def draw(self):
        r"""
        Setup Sage explorer visual display.

        TESTS::

            sage: from sage_explorer import SageExplorer
            sage: e = SageExplorer(42)
            sage: e.create_components()
            sage: e.implement_interactivity()
            sage: e.draw()
            sage: len(e.focuslist)
            10
        """
        self.focuslist = [] # Will be used to allocate focus to successive components
        self.focuslist.append(self.descriptionbox.children[1])
        propsvbox = VBox([self.descriptionbox, self.propsbox])
        for ec in self.propsbox.explorables:
            self.focuslist.append(ec)
        self.focuslist.append(self.visualbox)
        propsvbox.add_class('explorer-flexitem')
        topflex = HBox(
            (propsvbox, Separator(' '), self.visualbox),
            layout=Layout(margin='10px 0')
        )
        topflex.add_class("explorer-flexrow")
        top = VBox(
            (self.titlebox, topflex)
        )
        self.focuslist.append(self.histbox)
        self.focuslist.append(self.searchbox)
        self.focuslist.append(self.argsbox)
        self.focuslist.append(self.runbutton)
        middleflex = HBox([
            self.histbox,
            Separator('.'),
            self.searchbox,
            Separator('('),
            self.argsbox,
            Separator(')'),
            self.runbutton
        ])
        middleflex.add_class("explorer-flexrow")
        self.focuslist.append(self.codebox)
        self.focuslist.append(self.outputbox.output)
        self.focuslist.append(self.helpbox)
        bottom = VBox([middleflex, self.codebox, self.outputbox, self.helpbox])
        self.children = (top, bottom)
        self.distribute_focus()

    def distribute_focus(self):
        for c in self.focuslist:
            c.set_focusable(True)

    @observe('_history_index')
    def history_selection(self, change):
        if self.donottrack:
            return
        self.donottrack = True
        self.value = self._history.get_item(change.new)
        self.donottrack = False

    @observe('value')
    def value_changed(self, change):
        r"""
        What to do when the value has been changed.
        (Do not use this function if the value change
        was made by a history selection).

        INPUT:

            - ``change`` -- a change Bunch

        TESTS::

            sage: from sage_explorer import SageExplorer
            sage: t = Tableau([[1, 2, 5, 6], [3], [4]])
            sage: new_t = Tableau([[1, 2, 7, 6], [3], [4]])
            sage: e = SageExplorer(t)
            sage: e._history
            ExplorableHistory([[[1, 2, 5, 6], [3], [4]]])
            sage: from traitlets import Bunch
            sage: e.value_changed(Bunch({'name': 'value', 'old': t, 'new': new_t, 'owner': e, 'type': 'change'}))
            sage: e._history
            ExplorableHistory([[[1, 2, 5, 6], [3], [4]], [[1, 2, 7, 6], [3], [4]]])
            sage: e._history_index = int(0)
            sage: e.value = 42
            sage: e._history
            ExplorableHistory([[[1, 2, 5, 6], [3], [4]], 42])
            sage: e._history_index
            1
            sage: e._history_len
            2
        """
        if self.donottrack:
            return
        old_val = change.old
        new_val = change.new
        actually_changed = (id(new_val) != id(old_val))
        if not actually_changed:
            return
        self.donottrack = True
        need_to_cut = (self._history_len > self._history_index + 1)
        if need_to_cut: # First click navigation after a history selection
            shift = self._history_len - self._history_index - 1
            self._history.pop(shift)
        self._history.push(new_val)
        self._history_len = len(self._history)
        self._history_index += 1
        self.reset()
        self.donottrack = False

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
        self.value = obj # If value has changed, will call the observer

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


class ExplorerSettings(HasTraits):
    r"""
    Explorer settings. Used as a singleton.
    """
    show_tooltips = Bool(True) # Does the user actually want to see the explanatory tooltips?
    properties = Dict() # A dictionary of property -> list of context dictionaries

    def __init__(self, *args, **kwargs):
        r"""
        Init ExplorerSettings with optional argument `config`.

        TESTS::
            sage: from sage_explorer.sage_explorer import ExplorerSettings
            sage: ES = ExplorerSettings()
            sage: ES.show_tooltips
            True
            sage: type(ES.properties)
            <type 'dict'>
            sage: ES.properties['conjugate']
            [{'in': 'Partitions()'}, {'in': 'Tableaux()'}]
        """
        super(HasTraits, self).__init__(*args, **kwargs)
        if not 'config' in kwargs:
            config = CONFIG_PROPERTIES
        self.load_properties(config=config)

    def tooltips_visibility(self, visibility):
        r"""
        Switch tooltips visibility
        """
        self.show_tooltips = visibility

    def load_properties(self, config=CONFIG_PROPERTIES):
        r"""
        Parse properties flat list
        to make it a dictionary
        property name -> list of contexts

        INPUT:

                - ``config`` -- a dictionary 'properties' -> list of dictionaries

        TESTS::
            sage: from sage_explorer.sage_explorer import ExplorerSettings
            sage: ES = ExplorerSettings()
            sage: ES.load_properties()
            sage: ES.properties['base_ring']
            [{'when': 'has_base'}]
        """
        properties = {}
        for context in config['properties']:
            propname = context['property']
            if propname not in properties:
                properties[propname] = []
            properties[propname].append({
                key:val for key, val in context.items() if key!='property'
            })
        self.properties = properties

    def add_property(self, propname, clsname=None, predicate=None, label=None):
        r"""
        Add/modify a context for `propname` for class `clsname`
        in `properties` dictionary.

        INPUT:

                - ``propname`` -- a string
                - ``clsname`` -- a string
                - ``predicate`` -- a function
                - ``label`` -- a string

        TESTS::
            sage: from sage_explorer.sage_explorer import ExplorerSettings
            sage: ES = ExplorerSettings()
            sage: ES.load_properties()
            sage: ES.add_property('cardinality', clsname='frozenset')
            sage: ES.properties['cardinality']
            [{'in': 'EnumeratedSets.Finite'}, {'isinstance': 'frozenset'}]
            sage: ES.add_property('cardinality', predicate=Groups().Finite().__contains__)
            sage: len(ES.properties['cardinality'])
            3
            sage: ES.add_property('__abs__')
            sage: ES.properties['__abs__']
            [{}]
            sage: ES.remove_property('__abs__')
            sage: ES.properties['__abs__']
            []
            sage: ES.add_property('__abs__', predicate=lambda x:False)
            sage: 'predicate' in ES.properties['__abs__'][0]
            True
        """
        properties = self.properties
        if not propname in properties:
            properties[propname] = []
        context = {}
        if clsname:
            context['isinstance'] = clsname
        if predicate:
            context['predicate'] = predicate
        if label:
            context['label'] = label
        properties[propname].append(context)

    def remove_property(self, propname, clsname=None, predicate=None):
        r"""
        Remove property in context defined by `clsname` and `predicate`
        for `propname` in `properties` dictionary.

        INPUT:

                - ``propname`` -- a string
                - ``clsname`` -- a string
                - ``predicate`` -- a string

        TESTS::
            sage: from sage_explorer.sage_explorer import ExplorerSettings
            sage: ES = ExplorerSettings()
            sage: ES.load_properties()
            sage: ES.add_property('cardinality', clsname='frozenset')
            sage: ES.properties['cardinality']
            [{'in': 'EnumeratedSets.Finite'}, {'isinstance': 'frozenset'}]
            sage: ES.remove_property('cardinality', clsname='EnumeratedSets.Finite')
            sage: ES.properties['cardinality']
            [{'isinstance': 'frozenset'}]
        """
        properties = self.properties
        if not propname in properties:
            return
        for context in properties[propname]:
            found = True
            if clsname and ('isinstance' in properties[propname]) \
               and properties[propname]['isinstance'] != clsname:
                found = False
                continue
            if predicate and ('predicate' in properties[propname]) \
               and properties[propname]['predicate'] != predicate:
                found = False
                continue
            if found:
                properties[propname].remove(context)
                return

Settings = ExplorerSettings()
SageExplorer.settings = Settings
