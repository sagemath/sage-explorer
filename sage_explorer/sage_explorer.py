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
    # When Sage LaTeX implementation
    # applies well to MathJax, use it.
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


class ExplorerTitle(Box):
    r"""The sage explorer title bar
    """
    value = Any()
    content = Unicode('')

    def __init__(self, obj):
        self.value = obj
        self.content = "Exploring: {}" . format(math_repr(obj))
        m = MathTitle(self.content, 2)
        super(ExplorerTitle, self).__init__(
            (m,),
            layout=Layout(padding='5px 10px')
        )
        self.add_class("explorer-title")


class ExplorerDescription(Box):
    r"""The sage explorer object description
    """
    value = Any()
    content = Unicode('')

    def __init__(self, obj):
        self.value = obj
        if obj.__doc__:
            s = [l for l in obj.__doc__.split("\n") if l][0].strip()
        else:
            s = ''
        super(ExplorerDescription, self).__init__((HTMLMath(s),))
        self.content = s
        self.add_class("explorer-description")


class ExplorableHistory(deque):
    def __init__(self, obj, initial_name=None):
        super(ExplorableHistory, self).__init__()
        self.append(obj)
        self.initial_name = self.get_initial_name(value=obj)
        self.current_index = 0

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

    def get_index(self, i):
        return self.current_index

    def set_index(self, i):
        self.current_index = i

    def push(self, obj):
        r"""
        Push the history, ie append
        an object and increment index.
        """
        self.current_index = self.__len__()
        self.append(obj)
        self.truncate(MAX_LEN_HISTORY)

    def pop(self):
        r"""
        Pop the history, ie pop the list
        and decrement index.
        """
        val = super(ExplorableHistory, self).pop()
        self.current_index = self.__len__() - 1
        return val

    def get_item(self, i=None):
        return self.__getitem__(i or self.current_index)

    def get_current_item(self):
        return self.get_item()

    def make_menu_options(self):
        first_label = self.initial_name or "Hist[0]"
        return [(first_label, 0)] + [("Hist[{}]" . format(i+1), i+1) for i in range(self.__len__()-1)]

    def truncate(self, max=MAX_LEN_HISTORY):
        shift = self.__len__() - max
        if shift < 1:
            return
        for i in range(shift):
            self.popleft()
        self.current_index = self.current_index + shift


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


class ExplorerProperties(GridBox):
    r"""
    Display object properties as a table.
    """
    value = Any()

    def __init__(self, obj):
        self.value = obj
        children = []
        for p in get_properties(obj):
            explorable = getattr(obj, p.name).__call__()
            children.append(Box((Label(p.prop_label),), layout=Layout(border='1px solid #eee')))
            ev = ExplorableValue(obj, explorable)
            dlink((ev, 'new_val'), (self, 'value')) # Propagate explorable if clicked
            children.append(Box((ev,), layout=Layout(border='1px solid #eee')))
        super(ExplorerProperties, self).__init__(
            children,
            layout=Layout(border='1px solid #eee', width='100%', grid_template_columns='auto auto')
            )
        self.add_class("explorer-table")


class ExplorerVisual(Box):
    r"""
    The sage explorer visual representation
    """
    value = Any()
    new_val = Any() # holds visual widget value

    def __init__(self, obj):
        self.value = obj
        super(ExplorerVisual, self).__init__(
            layout = Layout(right='0')
        )
        w = _get_visual_widget(obj)
        if w:
            self.children = [w]
        else:
            if hasattr(obj, '__ascii_art__'):
                l = repr(obj._ascii_art_())
            else:
                l = repr(obj)
                self.children = [Textarea(l, rows=8)]
        dlink((self.children[0], 'value'), (self, 'new_val'))

    def get_widget(self):
        if isclass(self.obj):
            return
        if hasattr(obj, "_widget_"):
            return obj._widget_()
        else:
            return


class ExplorerHistory(Box):
    r"""
    A text input to give a name to a math object
    """
    value = Any()
    new_val = Any() # Use selection ?
    _history = Instance(ExplorableHistory)

    def __init__(self, obj, history=None):
        self.value = obj
        self._history = history or ExplorableHistory(obj)
        d = Dropdown(
            options=self._history.make_menu_options(),
            value = self._history.current_index,
            layout=Layout(width='5em', padding='0', margin='0')
        )
        super(ExplorerHistory, self).__init__(
            (d,),
            layout=Layout(padding='0')
        )
        # User input
        def changed(change):
            if self.donottrack:
                return
            self.donottrack = True
            self.new_val = self._history.get_item(change.new)
            self._history.set_index(change.new)
            self.donottrack = False
        #d.observe(changed, names='value')
        # History change
        def history_changed(change):
            if self.donottrack:
                return
            self.donottrack = True
            self._history = change.new
            self.children[0].options = self._history.make_menu_options()
            self.children[0].value = change.new.current_index
            if change.new == 0:
                self.new_val = self.initial_name
                self.children[0].disabled = True
            else:
                self.new_val = "Hist[{}]" . format(change.new.current_index)
            self.donottrack = False
        #self.observe(history_changed, names='_history')
        self.donottrack = False


class ExplorerMethodSearch(Box):
    r"""
    A widget to search a method
    """
    value = Any()
    content = Unicode('')
    no_args = Bool(False)
    args_placeholder = Unicode("Enter arguments")

    def __init__(self, obj):
        self.value = obj
        self.get_members()
        c = Combobox(
            options=[m.name for m in self.members],
            placeholder="Enter method name",
            continuous_update = False
        )
        super(ExplorerMethodSearch, self).__init__((c,))
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
        #dlink((self.children[0], 'value'), (self, 'content'))
        self.observe(method_changed, names='content') # ici on calcule un éventuel no_args
        #self.observe(method_changed, names='value') # ici on calcule un éventuel no_args

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

class ExplorerArgs(Box):
    r"""
    A text input to input method arguments
    """
    value = Any()
    content = Unicode()
    no_args = Bool(False)

    def __init__(self, obj=None):
        self.value = obj
        self.content = ''
        t = Text(
            self.content,
            placeholder="Enter arguments",
            layout=Layout(width="100%")
        )
        super(ExplorerArgs, self).__init__(
            (t,)
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
        dlink((self.children[0], 'value'), (self, 'content'))


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


class ExplorerOutput(Box):
    r"""
    A text box to output method results
    """
    value = Any() # the explorer value
    new_val = Any() # output value

    def __init__(self, obj=None):
        self.value = obj
        self.output = ExplorableValue(obj, '')
        self.output.add_class('invisible')
        def output_changed(change):
            if change.new:
                change.owner.remove_class('invisible')
                change.owner.add_class('visible')
                change.owner.value = '${}$' .format(math_repr(change.new))
            else:
                change.owner.remove_class('visible')
                change.owner.add_class('invisible')
        self.output.observe(output_changed, names='value')
        self.clc = Event(source=self.output, watched_events=['click'])
        def propagate_click(event):
            self.value = self.new_val
        self.clc.on_dom_event(propagate_click)
        self.error = HTML("")
        self.error.add_class("ansi-red-fg")
        super(ExplorerOutput, self).__init__(
            (self.output, self.error),
            layout = Layout(padding='2px 50px 2px 2px')
        )


class ExplorerHelp(Accordion):
    r"""
    Contains help, or output + help as expandable
    Contains MathJax
    """
    value = Any()
    content = Unicode('')

    def __init__(self, obj):
        self.value = obj
        t = HTMLMath()
        super(ExplorerHelp, self).__init__(
            (t,),
            selected_index=None,
            layout=Layout(width='99%', padding='0')
        )
        def content_changed(change):
            self.compute()
        self.observe(content_changed, names='content')
        self.content = obj.__doc__ or 'Help'

    def compute(self):
        self.children[0].value = self.content
        s = self.content.strip()
        end_first_line = max(s.find('.'), s.find('\n'))
        if end_first_line > 0:
            self.set_title(0, s[:end_first_line])
        else:
            self.set_title(0, s[:100])


class ExplorerCodeCell(Textarea):
    r"""
    TESTS:

        sage: from sage_explorer.sage_explorer import ExplorerCodeCell
        sage: cc = ExplorerCodeCell()
    """
    def __init__(self):
        super(ExplorerCodeCell, self).__init__(
            rows = 1,
            layout=Layout(border='1px solid #eee', width='99%')
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
        #self.compute()
        if not test_mode:
            self.create_components()
            self.implement_interactivity()
            self.draw()
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
            if name in ['runbutton', 'codebox']:
                setattr(self, name, self.components[name].__call__())
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

    def compute(self):
        obj = self.value
        self.titlebox = ExplorerTitle(obj)
        #dlink((self, 'value'), (self.titlebox, 'value'))
        self.description = ExplorerDescription(obj)
        self.propsbox = ExplorerProperties(obj)
        #dlink((self.propsbox, 'value'), (self, 'value')) # Handle the clicks on property values
        propsvbox = VBox([self.description, self.propsbox])
        propsvbox.add_class('explorer-flexitem')
        self.visualbox = ExplorerVisual(obj)
        #dlink((self.visualbox, 'content'), (self, 'value')) # Handle the visual widget changes
        topflex = HBox(
            (propsvbox, Separator(' '), self.visualbox),
            layout=Layout(margin='10px 0')
        )
        topflex.add_class("explorer-flexrow")
        self.top = VBox(
            (self.titlebox, topflex)
        )

        self.histbox = ExplorerHistory(obj)
        #link((self, '_history'), (self.histbox, '_history'))
        self.searchbox = ExplorerMethodSearch(obj)
        self.argsbox = ExplorerArgs(obj)
        #dlink((self.searchbox, 'no_args'), (self.argsbox, 'no_args'))
        self.runbutton = Button(
            description='Run!',
            tooltip='Run the method with specified arguments',
            layout = Layout(width='4em', right='0')
        )
        def compute_selection(button):
            method_name = self.searchbox.selection
            args = self.argsbox.content
            try:
                if AlarmInterrupt:
                    alarm(TIMEOUT)
                out = _eval_in_main("__obj__.{}({})".format(method_name, args), locals={"__obj__": obj})
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
            self.outputbox.content = out
            self.outputbox.output.value = '${}$' .format(math_repr(out))
            self.outputbox.error.value = ''
        #self.runbutton.on_click(compute_selection)
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
        self.outputbox = ExplorerOutput(obj)
        #dlink((self.outputbox, 'value'), (self, 'value')) # Handle the clicks on output values
        #dlink((self.histbox, '_history'), (self, '_history')) # Handle the history selection
        self.helpbox = ExplorerHelp(obj)

        def selection_changed(change):
            self.helpbox.content = self.searchbox.get_doc()
        #self.searchbox.observe(selection_changed, names='selection')
        self.bottom = VBox([middleflex, self.outputbox, self.helpbox])

        self.children = (self.top, self.bottom)

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
