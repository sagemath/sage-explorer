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
import re, warnings
from abc import abstractmethod
from cysignals.alarm import alarm, cancel_alarm
from cysignals.signals import AlarmInterrupt
from inspect import isclass
from collections import deque
from ipywidgets import Accordion, Box, Button, Combobox, Dropdown, GridBox, HBox, HTML, HTMLMath, Label, Layout, Text, Textarea, VBox
from traitlets import Any, Dict, Instance, Integer, Unicode, dlink, link, observe
with warnings.catch_warnings():
    warnings.filterwarnings("ignore", category=DeprecationWarning)
    from ipyevents import Event
from .explored_member import ExploredMember, _eval_in_main, get_members, get_properties

title_layout = Layout(width='100%', padding='12px')
css_lines = []
css_lines.append(".visible {visibility: visible; display: table}")
css_lines.append(".invisible {visibility: hidden; display: none}")
css_lines.append(".title-level2 {font-size: 150%}")
css_lines.append(".separator {width: 1em}")
css_lines.append('.explorer-title {background-color: teal; background-image: url("data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAB4AAAAeCAQAAACROWYpAAAABGdBTUEAALGPC/xhBQAAACBjSFJNAAB6JgAAgIQAAPoAAACA6AAAdTAAAOpgAAA6mAAAF3CculE8AAAAAmJLR0QA/4ePzL8AAAAHdElNRQfjCBQVGx7629/nAAAB60lEQVQ4y5WUQU8aQRSAv0UPGDcaJYKaCISj6VFJ6skfoEc5EUhIvWniTzFpjyb2ZJB/UBtMf0BvwA0WIfFAemqRSGJ2xwPDMLuz227nXd68ed/uvDfvPYhaZTwEAo9ylEsiEs5iAWCRjQOvs6ntCiEabLIeBqe4pkFR7mwfbEvtgDqf2QreIMVXXARP1MhQosEYIWVMgxJpKjgIPO5I6+gat7jKtcOrAufySos/UveoswGwDMASuyoAm/2Q3CT5oHSLjOTkOsQx/hYlQ46C365oUf5NJpybF9uh5XN6o0uTJl3efPYOuyZcYqq59LkkS5IkWS7oaydTSn7QYpWGDz32nR/78HvsWfVZlNmjQIGiKgWXK74E7nXBNUtSf+EnDg4D1PsupEveCCpPz/BzEyGtMWBk2EYMDFsiuqtirASeYcuRMWwZcobNW6ZqJCzPiZGwUw3WEjZ/qvv/f6rFMoskxwor5P5VJAA7tAPl2aNJk16gPFtsm3CNSazGeKEaRIs8xW5Jh0Md3eAhNioQfJtNklmRuDyr9x7TZmoENaXDROqCEa5+OB+AfSqkOQsZgNt8YigHYMj8vOW7isbmUcGPqnw+8oN6SP0RHPo3Cr7RrFukFht9Cv72fcoJ0eCX7hLdVUOETM8wyuUdTAVXcgNG490AAAAldEVYdGRhdGU6Y3JlYXRlADIwMTktMDgtMjBUMTk6Mjc6MzArMDI6MDCNIxYDAAAAJXRFWHRkYXRlOm1vZGlmeQAyMDE5LTA4LTIwVDE5OjI3OjMwKzAyOjAw/H6uvwAAAABJRU5ErkJggg=="); background-repeat: no-repeat; background-position: right;background-origin: content-box; border-radius: 4px}')
css_lines.append(".explorer-table {border-collapse: collapse}")
css_lines.append(".explorer-flexrow {padding:0; display:flex; flex-flow:row wrap; width:99%}")
css_lines.append(".explorer-flexitem {flex-grow:1}")
css_lines.append(".explorable-value {background-color: #eee; border-radius: 4px; padding: 4px}\n.explorable-value:hover {cursor: pointer}")
css = HTML("<style>%s</style>" % '\n'.join(css_lines))

try:
    ip = get_ipython()
    ip.display_formatter.format(css)
    oi = ip.inspector
except:
    pass # We are in the test environment

TIMEOUT = 15 # in seconds
MAX_LEN_HISTORY = 50


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
    """
    if isclass(obj):
        return
    if hasattr(obj, "_widget_"):
        return obj._widget_()
    if hasattr(obj, 'plot'):
        from ._widgets import PlotWidget
        return PlotWidget(obj)
    else:
        return

def math_repr(obj):
    r"""
    When Sage LaTeX implementation
    applies well to MathJax, use it.

    TESTS::
        sage: from sage_explorer.sage_explorer import math_repr
        sage: math_repr(42)
        '$42$'
        sage: math_repr(ZZ)
        '$\\Bold{Z}$'
    """
    if not obj:
        return ''
    if hasattr(obj, '_latex_'):
        s = obj._latex_()
        if 'tikz' not in s and 'raisebox' not in s:
            return "${}$" . format(s)
    return obj.__str__()


class Title(Label):
    r"""A title of various levels

    For HTML display
    """
    def __init__(self, value='', level=1):
        super(Title, self).__init__()
        self.value = value
        self.add_class('title-level%d' % level)


class MathTitle(HTMLMath):
    r"""A title of various levels

    For HTML display
    """
    def __init__(self, value='', level=1):
        super(MathTitle, self).__init__(value)
        self.value = math_repr(value)
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


class HelpButton(Button):
    r"""
    """
    def __init__(self, obj=None, target=None):
        super(HelpButton, self).__init__(description='?')
        self.add_class("separator")
        self.set_target(obj, target)

    def set_target(self, obj, target):
        def open_help(event):
            if obj and target:
                target.content = obj.__doc__
        click_event = Event(
            source=self,
            watched_events=['click']
        )
        click_event.on_dom_event(open_help) # Display `obj` help on click


class ExplorableHistory(deque):

    def __init__(self, obj, initial_name=None, previous_history=[]):
        super(ExplorableHistory, self).__init__(previous_history)
        if obj:
            self.append(obj)
        self.initial_name = self.get_initial_name(value=obj)

    @staticmethod
    def get_initial_name(value=None, test_sh_hist=[]):
        r"""Attempt to deduce the widget value variable name
        from notebook input history.
        In case it is not found, or not a string, set to `Hist[0]`.

        TESTS::
            sage: from sage_explorer.sage_explorer import ExplorableHistory
            sage: h = ExplorableHistory(42)
            sage: h.get_initial_name()
            'Hist[0]'
            sage: import __main__
            sage: eval(compile('x=42','<string>', 'exec'))
            sage: x
            42
            sage: h.get_initial_name(test_sh_hist=["w = explore(42)", "w"])
            'Hist[0]'
            sage: h.get_initial_name(test_sh_hist=["x=42", "w = explore(x)", "w"])
            'x'
            sage: h.get_initial_name(test_sh_hist=["x=42", "w = explore(x)", "explore(43)", "w"])
            'x'
        """
        initial_name = "Hist[0]"
        try:
            sh_hist = get_ipython().history_manager.input_hist_parsed[-50:]
        except:
            sh_hist = test_sh_hist # We are in the test environment
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
                        if _eval_in_main(initial_name_candidate) == value:
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
            [('Hist[0]', 0)]
            sage: for i in range(2): h.push(i)
            sage: h.make_menu_options()
            [('Hist[0]', 0), ('Hist[1]', 1), ('Hist[2]', 2)]
        """
        first_label = self.initial_name or "Hist[0]"
        return [(first_label, 0)] + [("Hist[{}]" . format(i+1), i+1) for i in range(self.__len__()-1)]

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


class ExplorableValue(HTMLMath):
    r"""
    A repr string with a link to a Sage object.

    TESTS::
        sage: from sage_explorer.sage_explorer import ExplorableValue
        sage: ev = ExplorableValue(42)
    """
    explorable = Any() # Some computed math object
    new_val = Any() # Overall value. Will be changed when explorable is clicked. `value` being reserved by ipywidgets.

    def __init__(self, explorable, initial_value=None):
        self.explorable = explorable
        if initial_value:
            self.new_val = initial_value
        super(ExplorableValue, self).__init__(layout=Layout(margin='1px'))
        self.add_class('explorable-value')
        self.reset()
        click_event = Event(
            source=self,
            watched_events=['click', 'keyup']
        )
        def set_new_val(event):
            if event['type'] == 'click' or event['key'] == 'Enter':
                self.new_val = self.explorable
        click_event.on_dom_event(set_new_val) # Handle clicking


    def reset(self):
        r"""
        `explorable` has changed: compute HTML value.
        """
        self.value = math_repr(self.explorable)


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
        self.explorable = explorable or ''
        if initial_value:
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
            else:
                children.append(Separator('{'))
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
        elif self.explorable: # treated as a single value
            ev = ExplorableValue(self.explorable, initial_value=self.new_val)
            self.explorables.append(ev)
            dlink((ev, 'new_val'), (self, 'new_val')) # Propagate click
            children.append(ev)
        self.children = children

    def switch_visibility(self, visibility):
        r"""
        Display/hide cell with CSS.
        """
        if visibility:
            self.remove_class('invisible')
            self.add_class('visible')
        else:
            self.remove_class('visible')
            self.add_class('invisible')


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
            children=(MathTitle('', 2),),
            layout=Layout(padding='5px 10px')
        )
        self.reset()
        self.donottrack = False
        self.add_class("explorer-title")

    @observe('value')
    def value_changed(self, change):
        if self.donottrack:
            return
        self.value = change.new
        self.reset()

    def reset(self):
        self.content = math_repr(self.value)
        self.children[0].value = "Exploring: {}" . format(self.content)


class ExplorerDescription(ExplorerComponent):
    r"""The sage explorer object description
    """
    content = Unicode('')

    def __init__(self, obj, help_target=None):
        super(ExplorerDescription, self).__init__(
            obj,
            children=(
                HTMLMath(),
                HelpButton(obj, help_target)
            )
        )
        self.add_class("explorer-description")
        if help_target:
            self.set_help_target(help_target)
        dlink((self, 'content'), (self.children[0], 'value'))

    def set_help_target(self, target):
        self.children[1].set_target(self.value, target)

    def reset(self):
        if self.value.__doc__:
            self.content = [l for l in self.value.__doc__.split("\n") if l][0].strip()
        else:
            self.content = ''


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
        self.reset()

    def reset(self):
        children = []
        self.explorables = []
        for p in get_properties(self.value):
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
        self.reset()

    def reset(self):
        w = _get_visual_widget(self.value)
        if w:
            self.children = (w,)
        else:
            if hasattr(self.value, '__ascii_art__'):
                self.children = (
                    Textarea(
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
    _history_len = Integer()
    _history_index = Integer()

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
            children=(Dropdown(
                layout=Layout(width='5em', padding='0', margin='0')
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
        else:
            self.children[0].disabled = True

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

    def __init__(self, obj, help_target=None):
        super(ExplorerMethodSearch, self).__init__(
            obj,
            children=(
                Combobox(
                    placeholder="Enter method name"
                ),)
        )
        self.reset()
        if help_target:
            self.set_help_target(help_target)
        def method_changed(change):
            selected_method = change.new
            if selected_method in self.members_dict:
                self.explored = self.members_dict[selected_method]
        # we do not link directly for not all names deserve a computation
        self.children[0].observe(method_changed, names='value')

    def reset(self):
        r"""
        Setup the combobox.
        """
        if isclass(self.value):
            cls = self.value
        else:
            cls = self.value.__class__
        self.members = get_members(cls) # Here, we both have a list and a dict
        self.members_dict = {m.name: m for m in self.members}
        self.children[0].options=[m.name for m in self.members]
        self.children[0].value = ''
        self.explored = ExploredMember('')

    def set_help_target(self, target):
        if not target:
            return
        def open_help(event):
            if event['key'] == '?' and self.explored:
                if not hasattr(self.explored, 'doc'):
                    self.explored.compute_doc()
                target.content = self.explored.doc
        click_event = Event(
            source=self,
            watched_events=['keyup']
        )
        click_event.on_dom_event(open_help) # Display `obj` help on click


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
        super(ExplorerArgs, self).__init__(
            obj,
            children=(Text(
                '',
                placeholder="Enter arguments",
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
                    self.children[0].placeholder = "Enter arguments"
            else:
                self.children[0].value = ''
                self.children[0].placeholder = ''
                self.children[0].disabled = True
        self.observe(explored_changed, names='explored')
        dlink((self.children[0], 'value'), (self, 'content'))

    def reset(self):
        self.children[0].value = ''
        self.children[0].disabled = False
        self.children[0].placeholder = "Enter arguments"


class ExplorerRunButton(Button):
    r"""
    A button for running methods in the explorer.

    TESTS::
        sage: from sage_explorer.sage_explorer import ExplorerRunButton
        sage: b = ExplorerRunButton()
    """
    def __init__(self):
        super(ExplorerRunButton, self).__init__(
            description = 'Run!',
            tooltip = 'Run the method with specified arguments',
            layout = Layout(width='4em', right='0')
        )


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
                change.owner.switch_visibility(True)
            else:
                change.owner.switch_visibility(False)
        self.output.observe(output_changed, names='explorable') # display/hide output
        self.error = HTML("")
        self.error.add_class("ansi-red-fg")
        super(ExplorerOutput, self).__init__(
            obj,
            children=(self.output, self.error),
            layout = Layout(padding='2px 50px 2px 2px')
        )
        self.reset()

    def reset(self):
        self.output.new_val = self.value
        self.output.explorable = None
        self.output.switch_visibility(False)
        self.error.value = ''
        dlink((self.output, 'new_val'), (self, 'value')) # propagate if output is clicked

    def set_output(self, obj):
        self.output.explorable = obj
        self.output.value = '${}$' .format(math_repr(obj))
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
            children=(HTMLMath(),),
            layout=Layout(width='99%', padding='0', border='1px solid grey')
        )
        dlink((self, 'content'), (self.children[0], 'value'))
        def explored_changed(change):
            explored = change.new
            if explored.name:
                if not hasattr(explored, 'doc'):
                    explored.compute_doc()
                self.content = explored.doc
            else:
                self.content = ''
        self.observe(explored_changed, names='explored')

    def reset(self):
        self.content = ''

    @observe('value')
    def value_changed(self, change):
        r"""
        Value has changed.

        TESTS::
            sage: from sage_explorer.sage_explorer import ExplorerHelp
            sage: h = ExplorerHelp("Some initial value")
            sage: h.value = 42
            sage: h.content
            ''
        """
        self.reset()


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
            children=(Textarea(
                rows = 1,
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

    def evaluate(self, l=None):
        r"""
        Evaluate the code cell
        `l` being a dictionary of locals.

        TESTS::
            sage: from sage_explorer.sage_explorer import ExplorerCodeCell
            sage: c = ExplorerCodeCell(42)
            sage: c.content = "1 + 2"
            sage: c.evaluate()
            sage: c.new_val
            3
        """
        g = globals() # the name space used by the usual Jupyter cells
        l = l or {"_": self.value} #, "__explorer__": self, "Hist": self._history}
        local_names = ["_", "__explorer__", "Hist"]
        code = compile(self.content, '<string>', 'eval')
        result = eval(code, g, l)
        if result is None: # the code may have triggered some assignments
            self.content = "result is None"
            for name, value in l.items():
                if name not in local_names:
                    g[name] = value
        else:
            self.content = "OK"
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
    """Sage Explorer in Jupyter Notebook"""

    value = Any()
    _history = Instance(ExplorableHistory)
    _history_len = Integer()
    _history_index = Integer()
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
        if 'runbutton' in self.components:
            def compute_selected_method(button=None):
                method_name = self.searchbox.explored.name
                args = self.argsbox.content
                try:
                    if AlarmInterrupt:
                        alarm(TIMEOUT)
                    out = _eval_in_main("__obj__.{}({})".format(method_name, args), locals={"__obj__": self.value})
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
            self.runbutton.on_click(compute_selected_method)
            enter_event = Event(source=self.runbutton, watched_events=['keyup'])
            def run_button(event):
                if event['key'] == 'Enter':
                    compute_selected_method()
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
        if 'codebox' in self.components:
            def launch_evaluation(event):
                if event['key'] == 'Enter' and (event['shiftKey'] or event['ctrlKey']):
                    self.codebox.evaluate(l = {"_": self.value, "__explorer__": self, "Hist": self._history})
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
        self.focuslist.append(self.titlebox)
        propsvbox = VBox([self.descriptionbox, self.propsbox])
        for ev in self.propsbox.explorables:
            self.focuslist.append(ev)
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
        self.focuslist.append(self.outputbox)
        self.focuslist.append(self.codebox)
        self.focuslist.append(self.helpbox)
        bottom = VBox([middleflex, self.outputbox, self.codebox, self.helpbox])
        self.children = (top, bottom)

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
