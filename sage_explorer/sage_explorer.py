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
from ipywidgets import Accordion, Box, Button, Combobox, DOMWidget, Dropdown, GridBox, HBox, HTML, HTMLMath, Label, Layout, Text, Textarea, VBox
from ipywidgets.widgets.widget_description import DescriptionStyle
from traitlets import Any, Bool, Dict, Instance, Integer, Unicode, dlink, link, observe
from ipywidgets.widgets.trait_types import InstanceDict, Color
with warnings.catch_warnings():
    warnings.filterwarnings("ignore", category=DeprecationWarning)
    from ipyevents import Event
from .explored_member import _eval_in_main, get_members, get_properties

title_layout = Layout(width='100%', padding='12px')
css_lines = []
css_lines.append(".visible {visibility: visible; display: inline}")
css_lines.append(".invisible {visibility: hidden; display: none}")
css_lines.append(".title-level2 {font-size: 150%}")
css_lines.append('.explorer-title {background-color: teal; background-image: url("data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAB4AAAAeCAQAAACROWYpAAAABGdBTUEAALGPC/xhBQAAACBjSFJNAAB6JgAAgIQAAPoAAACA6AAAdTAAAOpgAAA6mAAAF3CculE8AAAAAmJLR0QA/4ePzL8AAAAHdElNRQfjCBQVGx7629/nAAAB60lEQVQ4y5WUQU8aQRSAv0UPGDcaJYKaCISj6VFJ6skfoEc5EUhIvWniTzFpjyb2ZJB/UBtMf0BvwA0WIfFAemqRSGJ2xwPDMLuz227nXd68ed/uvDfvPYhaZTwEAo9ylEsiEs5iAWCRjQOvs6ntCiEabLIeBqe4pkFR7mwfbEvtgDqf2QreIMVXXARP1MhQosEYIWVMgxJpKjgIPO5I6+gat7jKtcOrAufySos/UveoswGwDMASuyoAm/2Q3CT5oHSLjOTkOsQx/hYlQ46C365oUf5NJpybF9uh5XN6o0uTJl3efPYOuyZcYqq59LkkS5IkWS7oaydTSn7QYpWGDz32nR/78HvsWfVZlNmjQIGiKgWXK74E7nXBNUtSf+EnDg4D1PsupEveCCpPz/BzEyGtMWBk2EYMDFsiuqtirASeYcuRMWwZcobNW6ZqJCzPiZGwUw3WEjZ/qvv/f6rFMoskxwor5P5VJAA7tAPl2aNJk16gPFtsm3CNSazGeKEaRIs8xW5Jh0Md3eAhNioQfJtNklmRuDyr9x7TZmoENaXDROqCEa5+OB+AfSqkOQsZgNt8YigHYMj8vOW7isbmUcGPqnw+8oN6SP0RHPo3Cr7RrFukFht9Cv72fcoJ0eCX7hLdVUOETM8wyuUdTAVXcgNG490AAAAldEVYdGRhdGU6Y3JlYXRlADIwMTktMDgtMjBUMTk6Mjc6MzArMDI6MDCNIxYDAAAAJXRFWHRkYXRlOm1vZGlmeQAyMDE5LTA4LTIwVDE5OjI3OjMwKzAyOjAw/H6uvwAAAABJRU5ErkJggg=="); background-repeat: no-repeat; background-position: right;background-origin: content-box; border-radius: 4px}')
css_lines.append(".explorer-table {border-collapse: collapse}")
css_lines.append(".explorer-flexrow {padding:0; display:flex; flex-flow:row wrap; width:99%}")
css_lines.append(".explorer-flexitem {flex-grow:1}")
css_lines.append(".explorable-value {background-color: #eee; border-radius: 4px; padding: 4px}\n.explorable-value:hover {cursor: pointer}")
css = HTML("<style>%s</style>" % '\n'.join(css_lines))

try:
    ip = get_ipython()
    ip.display_formatter.format(css)
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
    else:
        return

def math_repr(obj):
    r"""
    When Sage LaTeX implementation
    applies well to MathJax, use it.

    TESTS::
        sage: from sage.all import *
        sage: from sage_explorer.sage_explorer import math_repr
        sage: t = Tableau([[1,2], [3]])
        sage: math_repr(t.cocharge())
        '$1$'
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


class ExplorableHistory(deque):
    def __init__(self, obj, initial_name=None, previous_history=[]):
        super(ExplorableHistory, self).__init__(previous_history)
        if obj:
            self.append(obj)
        self.initial_name = self.get_initial_name(value=obj)
        self.current_index = len(previous_history)

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

    def get_index(self):
        r"""
        Get current object history index.

        TESTS::
            sage: from sage_explorer.sage_explorer import ExplorableHistory
            sage: h = ExplorableHistory(42)
            sage: h.get_index()
            0
        """
        return self.current_index

    def set_index(self, i):
        r"""
        Set current object history index.

        TESTS::
            sage: from sage_explorer.sage_explorer import ExplorableHistory
            sage: h = ExplorableHistory(42)
            sage: h.set_index(2)
            sage: h.get_index()
            2
        """
        self.current_index = i

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
        self.current_index = self.__len__()
        self.append(obj)
        self.truncate(MAX_LEN_HISTORY)

    def pop(self):
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
            sage: h.current_index
            0
            sage: h.pop()
            Traceback (most recent call last):
            ...
            Exception: No more history!
        """
        val = super(ExplorableHistory, self).pop()
        if self.current_index < 1:
            raise Exception("No more history!")
        self.current_index -= 1
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
            return self[self.current_index]
        return self.__getitem__(i)

    def get_current_item(self):
        r"""
        Get current history item.

        TESTS::
            sage: from sage_explorer.sage_explorer import ExplorableHistory
            sage: h = ExplorableHistory("A first value")
            sage: h.push(42)
            sage: h.get_current_item()
            42
            sage: h
            ExplorableHistory(['A first value', 42])
            sage: h.current_index
            1
        """
        return self.get_item()

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
        self.current_index = self.current_index - shift


class ExplorableValue(HTMLMath):
    r"""
    A repr string with a link to a Sage object.

    TESTS:
        sage: from sage_explorer.sage_explorer import ExplorableValue
        sage: ev = ExplorableValue("original val", explorable=42)
    """
    explorable = Any() # Some computed math object
    new_val = Any() # Overall value. Will be changed when explorable is clicked

    def __init__(self, obj, explorable):
        self.new_val = obj
        self.explorable = explorable
        super(ExplorableValue, self).__init__(math_repr(explorable), layout=Layout(margin='1px'))
        self.add_class('explorable-value')
        self.clc = Event(source=self, watched_events=['click'])
        def set_new_val(event):
            self.new_val = self.explorable
        self.clc.on_dom_event(set_new_val)

    def switch_visibility(self, visibility):
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
        self.compute()
        self.donottrack = False

    @abstractmethod
    def compute(self):
        r"""
        Common methods to all components.

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

        TESTS ::

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
            self.compute()


class ExplorerTitle(ExplorerComponent):
    r"""The sage explorer title bar
    """
    content = Unicode('')

    def __init__(self, obj):
        super(ExplorerTitle, self).__init__(
            obj,
            children=(MathTitle('', 2),),
            layout=Layout(padding='5px 10px')
        )
        self.compute()
        self.add_class("explorer-title")

    def compute(self):
        self.content = math_repr(self.value)
        self.children[0].value = "Exploring: {}" . format(self.content)


class ExplorerDescription(ExplorerComponent):
    r"""The sage explorer object description
    """
    content = Unicode('')

    def __init__(self, obj):
        super(ExplorerDescription, self).__init__(
            obj,
            children=(HTMLMath(),)
        )
        self.compute()
        dlink((self, 'content'), (self.children[0], 'value'))
        self.add_class("explorer-description")

    def compute(self):
        if self.value.__doc__:
            self.content = [l for l in self.value.__doc__.split("\n") if l][0].strip()
        else:
            self.content = ''


class ExplorerProperties(ExplorerComponent, GridBox):
    r"""
    Display object properties as a table.
    """
    def __init__(self, obj):
        super(ExplorerProperties, self).__init__(
            obj,
            layout=Layout(border='1px solid #eee', width='100%', grid_template_columns='auto auto')
        )
        self.add_class("explorer-table")
        self.compute()

    def compute(self):
        children = []
        for p in get_properties(self.value):
            explorable = getattr(self.value, p.name).__call__()
            children.append(Box((Label(p.prop_label),), layout=Layout(border='1px solid #eee')))
            ev = ExplorableValue(self.value, explorable)
            dlink((ev, 'new_val'), (self, 'value')) # Propagate explorable if clicked
            children.append(Box((ev,), layout=Layout(border='1px solid #eee')))
        self.children = children


class ExplorerVisual(ExplorerComponent):
    r"""
    The sage explorer visual representation
    """
    new_val = Any() # holds visual widget value

    def __init__(self, obj):
        super(ExplorerVisual, self).__init__(
            obj,
            layout = Layout(right='0')
        )
        self.compute()

    def compute(self):
        w = _get_visual_widget(self.value)
        if w:
            self.children = [w]
        else:
            if hasattr(self.value, '__ascii_art__'):
                l = repr(self.value._ascii_art_())
            else:
                l = repr(self.value)
                self.children = [Textarea(l, rows=8)]
        dlink((self.children[0], 'value'), (self, 'new_val'))


class ExplorerHistory(ExplorerComponent):
    r"""
    A text input to give a name to a math object
    """
    new_val = Any() # Use selection ?
    _history = Instance(ExplorableHistory)

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
        self.compute()
        self.donottrack = False
        # User input
        def dropdown_selection(change):
            if self.donottrack:
                return
            self.donottrack = True
            self.new_val = self._history.get_item(change.new)
            self._history = ExplorableHistory( # Seems to be necessary in order to 'change' _history
                None,
                initial_name=self._history.initial_name,
                previous_history=self._history
            )
            self._history.set_index(change.new)
            self.donottrack = False
        self.children[0].observe(dropdown_selection, names='value')

    def compute(self):
        self.children[0].options = self._history.make_menu_options()
        self.children[0].value = self._history.current_index

    @observe('_history')
    def history_changed(self, change):
        if self.donottrack:
            return
        #print("ok ")
        self.donottrack = True
        self.compute()
        self.donottrack = False


class ExplorerMethodSearch(ExplorerComponent):
    r"""
    A widget to search a method
    """
    content = Unicode('')
    no_args = Bool(False)
    args_placeholder = Unicode("Enter arguments")

    def __init__(self, obj):
        c = Combobox(
            placeholder="Enter method name"
        )
        super(ExplorerMethodSearch, self).__init__(
            obj,
            children=(c,)
        )
        self.compute()
        def method_changed(change):
            selected_method = change.new
            if selected_method in self.members_dict:
                self.content = selected_method
                args, defaults = self.get_argspec()
                if (not args or args == ['self']) and not self.no_args:
                    self.no_args = True
                if (args and args != ['self']) and self.no_args:
                    self.no_args = False
                if defaults:
                    self.args_placeholder = str(defaults)
                else:
                    self.args_placeholder = "Enter arguments"
        c.observe(method_changed, names='value')

    def compute(self):
        self.get_members()
        self.children[0].options=[m.name for m in self.members]

    def get_members(self):
        if isclass(self.value):
            cls = self.value
        else:
            cls = self.value.__class__
        self.members = get_members(cls)
        self.members_dict = {m.name: m for m in self.members}

    def get_member(self):
        if self.content in self.members_dict:
            return self.members_dict[self.content].member

    def get_doc(self):
        if self.content in self.members_dict:
            return self.members_dict[self.content].member.__doc__

    def get_argspec(self):
        if self.content in self.members_dict:
            m = self.members_dict[self.content]
            if not hasattr(m, 'args'):
                m.compute_argspec()
            return m.args, m.defaults

class ExplorerArgs(ExplorerComponent):
    r"""
    A text box to input method arguments
    """
    content = Unicode('')
    no_args = Bool(False)

    def __init__(self, obj=None):
        r"""
        A text box to input method arguments.

        TESTS::
            sage: from sage_explorer.sage_explorer import ExplorerArgs
            sage: a = ExplorerArgs()
            sage: a.value = 'some arguments'
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
        def disable(change):
            if change.new == True:
                change.owner.value = ""
                change.owner.placeholder = ""
            elif change.new == False:
                change.owner.placeholder = "Enter arguments"
        self.children[0].observe(disable, names='disabled')
        dlink((self, 'no_args'), (self.children[0], 'disabled'))
        link((self, 'content'), (self.children[0], 'value'))

    def compute(self):
        self.content = ''
        self.no_args = False


class ExplorerRunButton(Button):
    r"""
    A button for running methods in the explorer.
    """
    def __init__(self):
        super(ExplorerRunButton, self).__init__(
            description = 'Run!',
            tooltip = 'Run the method with specified arguments',
            layout = Layout(width='4em', right='0')
        )


class ExplorerOutput(ExplorerComponent):
    r"""
    A text box to output method results
    """
    new_val = Any() # output value

    def __init__(self, obj=None):
        r"""
        Common methods to all components.

        TESTS::
            sage: from sage_explorer.sage_explorer import ExplorerOutput
            sage: c = ExplorerOutput("Initial value")
            sage: c.value = 42
        """
        self.output = ExplorableValue(obj, '')
        self.output.add_class('invisible')
        def output_changed(change):
            if change.new:
                change.owner.switch_visibility(True)
                #change.owner.value = '${}$' .format(math_repr(change.new))
            else:
                change.owner.switch_visibility(False)
        self.output.observe(output_changed, names='value')
        self.clc = Event(source=self.output, watched_events=['click'])
        def propagate_click(event):
            self.value = self.new_val
        self.clc.on_dom_event(propagate_click)
        self.error = HTML("")
        self.error.add_class("ansi-red-fg")
        super(ExplorerOutput, self).__init__(
            obj,
            children=(self.output, self.error),
            layout = Layout(padding='2px 50px 2px 2px')
        )

    def compute(self):
        self.new_val = None
        self.output.value = ''
        self.output.switch_visibility(False)
        self.error.value = ''


class ExplorerHelp(ExplorerComponent, Accordion):
    r"""
    Contains help, or output + help as expandable
    Contains MathJax
    """
    content = Unicode('')

    def __init__(self, obj):
        r"""
        A box for object or method help text.

        TESTS::
            sage: from sage_explorer.sage_explorer import ExplorerHelp
            sage: h = ExplorerHelp(42)
            sage: h.content = "Some help text"
            sage: h._titles
            {'0': 'Some help text'}
        """
        super(ExplorerHelp, self).__init__(
            obj,
            children=(HTMLMath(),),
            selected_index=None,
            layout=Layout(width='99%', padding='0')
        )
        def content_changed(change):
            self.compute_title()
        self.observe(content_changed, names='content')
        dlink((self, 'content'), (self.children[0], 'value'))
        self.compute()

    def compute_title(self):
        s = self.content.strip()
        end_first_line = max(s.find('.'), s.find('\n'))
        if end_first_line > 0:
            self.set_title(0, s[:end_first_line])
        else:
            self.set_title(0, s[:100])

    def compute(self):
        r"""
        Value has changed.

        TESTS::
            sage: from sage_explorer.sage_explorer import ExplorerHelp
            sage: h = ExplorerHelp("Some initial value")
            sage: h._titles['0'][:15]
            "str(object='') "
            sage: h.value = 42
            sage: h._titles['0']
            'Integer(x=None, base=0)\nFile: sage/rings/integer'
        """
        self.content = self.value.__doc__ or 'Help'
        self.compute_title()


class ExplorerCodeCell(ExplorerComponent):
    r"""
    TESTS:

        sage: from sage_explorer.sage_explorer import ExplorerCodeCell
        sage: cc = ExplorerCodeCell(42)
    """
    def __init__(self, obj):
        super(ExplorerCodeCell, self).__init__(
            obj,
            children=(Textarea(
                rows = 1,
                layout=Layout(border='1px solid #eee', width='99%')
            ),)
        )


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
    components = Dict() # A list of widgets

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
        self.components = components
        if not test_mode:
            #self.compute()
            self.create_components()
            self.implement_interactivity()
            self.draw()
        self.donottrack = False

    def compute(self):
        self.donottrack = True
        for name in self.components:
            if name not in ['runbutton', 'codebox']:
                setattr(getattr(self, name), 'value', self.value)
        #self.draw()
        self.donottrack = False

    def create_components(self):
        r"""
        Create all components for the explorer.

        TESTS:
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

        TESTS:
            sage: from sage_explorer import SageExplorer
            sage: e = SageExplorer(42)
            sage: e.create_components()
            sage: e.implement_interactivity()
        """
        if self.test_mode:
            self.donottrack = True # Prevent any interactivity while installing the links
        if 'propsbox' in self.components:
            dlink((self.propsbox, 'value'), (self, 'value')) # Handle the clicks on property values
        if 'visualbox' in self.components:
            dlink((self.visualbox, 'new_val'), (self, 'value')) # Handle the visual widget changes
        if 'histbox' in self.components:
            dlink((self.histbox, 'new_val'), (self, 'value')) # Handle the history selection
            link((self, '_history'), (self.histbox, '_history'))
        if 'searchbox' in self.components and 'argsbox' in self.components:
            dlink((self.searchbox, 'no_args'), (self.argsbox, 'no_args'))
        if 'runbutton' in self.components:
            def compute_selected_method(button):
                method_name = self.searchbox.content
                args = self.argsbox.content
                try:
                    if AlarmInterrupt:
                        alarm(TIMEOUT)
                    out = _eval_in_main("__obj__.{}({})".format(method_name, args), locals={"__obj__": self.value})
                    if AlarmInterrupt:
                        cancel_alarm()
                except AlarmInterrupt:
                    self.outputbox.error.value = "Timeout!"
                    self.outputbox.output.value = ''
                    return
                except Exception as e:
                    if AlarmInterrupt:
                        cancel_alarm()
                    self.outputbox.error.value = '<span class="ansi-red-fg">Error: {}</span>' .format(e)
                    self.outputbox.output.value = ''
                    return
                self.outputbox.new_val = out
                self.outputbox.output.value = '${}$' .format(math_repr(out))
                self.outputbox.error.value = ''
            self.runbutton.on_click(compute_selected_method)
        if 'outputbox' in self.components:
            dlink((self.outputbox, 'value'), (self, 'value')) # Handle the clicks on output values
        if 'searchbox' in self.components and 'helpbox' in self.components:
            def selected_method_changed(change):
                self.helpbox.content = self.searchbox.get_doc()
            self.searchbox.observe(selected_method_changed, names='content')
        if self.test_mode:
            self.donottrack = False

    def draw(self):
        r"""
        Setup Sage explorer visual display.

        TESTS:
            sage: from sage_explorer import SageExplorer
            sage: e = SageExplorer(42)
            sage: e.create_components()
            sage: e.implement_interactivity()
            sage: e.draw()
        """
        propsvbox = VBox([self.descriptionbox, self.propsbox])
        propsvbox.add_class('explorer-flexitem')
        topflex = HBox(
            (propsvbox, Separator(' '), self.visualbox),
            layout=Layout(margin='10px 0')
        )
        topflex.add_class("explorer-flexrow")
        top = VBox(
            (self.titlebox, topflex)
        )
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
        bottom = VBox([middleflex, self.outputbox, self.helpbox, self.codebox])
        self.children = (top, bottom)

    @observe('value')
    def value_changed(self, change):
        r"""
        What to do when the value has been changed.

        INPUT:

            - ``change`` -- a change Bunch

        TESTS ::

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
        """
        if self.donottrack:
            return
        old_val = change.old
        new_val = change.new
        actually_changed = (id(new_val) != id(old_val))
        if actually_changed:
            self._history.push(new_val)
            self.compute()

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
        if not self._history:
            print("No more history!")
            return
        self._history.pop()
        self.value = self._history[-1]
        self.compute()
        self.donottrack = False
