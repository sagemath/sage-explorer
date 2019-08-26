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
from ipywidgets import Accordion, Box, Button, Combobox, Dropdown, GridBox, HBox, HTML, HTMLMath, Label, Layout, Text, Textarea, VBox
from ipywidgets.widgets.widget_description import DescriptionStyle
from traitlets import Any, Bool, Integer, Unicode, dlink, observe
from ipywidgets.widgets.trait_types import InstanceDict, Color
with warnings.catch_warnings():
    warnings.filterwarnings("ignore", category=DeprecationWarning)
    from ipyevents import Event
from .explored_member import _eval_in_main, get_members, get_properties

title_layout = Layout(width='100%', padding='12px')
css_lines = []
css_lines.append(".title-level2 {font-size: 150%}")
css_lines.append('.explorer-title {background-color: teal; background-image: url("data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAB4AAAAeCAQAAACROWYpAAAABGdBTUEAALGPC/xhBQAAACBjSFJNAAB6JgAAgIQAAPoAAACA6AAAdTAAAOpgAAA6mAAAF3CculE8AAAAAmJLR0QA/4ePzL8AAAAHdElNRQfjCBQVGx7629/nAAAB60lEQVQ4y5WUQU8aQRSAv0UPGDcaJYKaCISj6VFJ6skfoEc5EUhIvWniTzFpjyb2ZJB/UBtMf0BvwA0WIfFAemqRSGJ2xwPDMLuz227nXd68ed/uvDfvPYhaZTwEAo9ylEsiEs5iAWCRjQOvs6ntCiEabLIeBqe4pkFR7mwfbEvtgDqf2QreIMVXXARP1MhQosEYIWVMgxJpKjgIPO5I6+gat7jKtcOrAufySos/UveoswGwDMASuyoAm/2Q3CT5oHSLjOTkOsQx/hYlQ46C365oUf5NJpybF9uh5XN6o0uTJl3efPYOuyZcYqq59LkkS5IkWS7oaydTSn7QYpWGDz32nR/78HvsWfVZlNmjQIGiKgWXK74E7nXBNUtSf+EnDg4D1PsupEveCCpPz/BzEyGtMWBk2EYMDFsiuqtirASeYcuRMWwZcobNW6ZqJCzPiZGwUw3WEjZ/qvv/f6rFMoskxwor5P5VJAA7tAPl2aNJk16gPFtsm3CNSazGeKEaRIs8xW5Jh0Md3eAhNioQfJtNklmRuDyr9x7TZmoENaXDROqCEa5+OB+AfSqkOQsZgNt8YigHYMj8vOW7isbmUcGPqnw+8oN6SP0RHPo3Cr7RrFukFht9Cv72fcoJ0eCX7hLdVUOETM8wyuUdTAVXcgNG490AAAAldEVYdGRhdGU6Y3JlYXRlADIwMTktMDgtMjBUMTk6Mjc6MzArMDI6MDCNIxYDAAAAJXRFWHRkYXRlOm1vZGlmeQAyMDE5LTA4LTIwVDE5OjI3OjMwKzAyOjAw/H6uvwAAAABJRU5ErkJggg=="); background-repeat: no-repeat; background-position: right;background-origin: content-box;}')
css_lines.append(".explorable-value {background-color: #ccc}")
css_lines.append(".explorer-visual {position: absolute;}")
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

    def __init__(self, obj):
        s = "Exploring: {}" . format(math_repr(obj))
        super(ExplorerTitle, self).__init__(
            (MathTitle(s, 2),),
            layout=Layout(padding='5px 10px')
        )
        self.add_class("explorer-title")
        self.value = obj


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


class ExplorableValue(Box):
    r"""
    A repr string with a link for a Sage object.
    """
    value = Any()

    def __init__(self, obj, parent=None):
        self.value = obj # we should compute it -- or use it -- as a 'member'
        self.parent = parent
        h = HTMLMath(math_repr(obj))
        h.add_class('explorable-value')
        self.clc = Event(source=h, watched_events=['click'])
        super(ExplorableValue, self).__init__(
            (h,),
            layout = Layout(border='1px solid green', padding='2px 50px 2px 2px')
        )
        def propagate_click(event):
            self.parent.value = self.value
        self.clc.on_dom_event(propagate_click)


class ExplorerProperties(Box):
    r"""
    Display object properties as a table.
    """
    value = Any()

    def __init__(self, obj):
        self.value = obj
        children = []
        for p in get_properties(obj):
            val = getattr(obj, p.name).__call__()
            children.append(Label(p.prop_label))
            children.append(ExplorableValue(val, parent=self))
        super(ExplorerProperties, self).__init__(
            (GridBox(children, layout=Layout(grid_template_columns='25% 75%')),),
            layout=Layout(border='1px solid red')
            )


class ExplorerVisual(Box):
    r"""
    The sage explorer visual representation
    """
    value = Any()

    def __init__(self, obj):
        self.value = obj
        super(ExplorerVisual, self).__init__(
            layout = Layout(border='1px solid red', right='0')
        )
        self.add_class('explorer-visual') # needed for absolute positioning
        w = _get_visual_widget(obj)
        if w:
            self.children = [w]
        else:
            try:
                l = repr(obj._ascii_art_())
            except:
                l = repr(obj)
            self.children = [Textarea(l, rows=8)]

    def get_widget(self):
        if isclass(self.obj):
            return
        if hasattr(obj, "_widget_"):
            return obj._widget_()
        else:
            return
        

class ExplorerMenus(Box):
    r"""
    Contains a Treeview
    """
    value = Any()

    def __init__(self, obj):
        super(ExplorerMenus, self).__init__()
        self.value = obj


class ExplorerNaming(Box):
    r"""
    A text input to give a name to a math object
    """
    value = Any()
    initial_name = Unicode('')
    history_index = Integer(-1)
    content = Unicode('')

    def __init__(self, obj):
        self.value = obj
        d = Dropdown(
            options=[('Hist[0]', 0)],
            value=0,
            layout=Layout(width='5em', padding='0', margin='0')
        )
        super(ExplorerNaming, self).__init__(
            (d,),
            layout=Layout(padding='0')
        )
        # User input
        def changed(change):
            self.content = self.children[0].options[change.new][0]
        d.observe(changed, names='value')
        # History change
        def history_changed(change):
            self.children[0].options = [(self.initial_name, 0)] + [("Hist[{}]" . format(i+1), i+1) for i in range(change.new)]
            self.children[0].value = change.new
            if change.new == 0:
                self.content = self.initial_name
                self.children[0].disabled = True
            else:
                self.content = "Hist[{}]" . format(change.new)
        self.observe(history_changed, names='history_index')


class ExplorerMethodSearch(Box):
    r"""
    A widget to search a method
    """
    value = Any()
    selected_method = Unicode('')
    no_args = Bool(False)
    args_placeholder = Unicode("Enter arguments")

    def __init__(self, obj):
        self.value = obj
        self.get_members()
        c = Combobox(
            options=[m.name for m in self.members],
            placeholder="Enter method name"
        )
        super(ExplorerMethodSearch, self).__init__((c,))
        def changed(change):
            new_val = change.new
            if new_val in self.members_dict:
                self.selected_method = new_val
                args, defaults = self.get_argspec()
                if (not args or args == ['self']) and not self.no_args:
                    self.no_args = True
                if (args and args != ['self']) and self.no_args:
                    self.no_args = False
                if defaults:
                    self.args_placeholder = str(defaults)
                else:
                    self.args_placeholder = "Enter arguments"
        c.observe(changed, names='value')

    def get_members(self):
        if isclass(self.value):
            cls = self.value
        else:
            cls = self.value.__class__
        self.members = get_members(cls)
        self.members_dict = {m.name: m for m in self.members}

    def get_member(self):
        if self.selected_method in self.members_dict:
            return self.members_dict[self.selected_method].member

    def get_doc(self):
        if self.selected_method in self.members_dict:
            return self.members_dict[self.selected_method].member.__doc__

    def get_argspec(self):
        if self.selected_method in self.members_dict:
            m = self.members_dict[self.selected_method]
            if not hasattr(m, 'args'):
                m.compute_argspec()
            return m.args, m.defaults

class ExplorerArgs(Box):
    r"""
    A text input to input method arguments
    """
    value = Any()
    content = Any()
    no_args = Bool(False)

    def __init__(self, obj=None):
        self.value = obj
        t = Text(placeholder="Enter arguments")
        super(ExplorerArgs, self).__init__(
            (t,),
            layout = Layout(border='1px solid green', padding='2px 50px 2px 2px')
        )
        def disabled(change):
            if change.new == True:
                change.owner.placeholder = ""
            elif change.new == False:
                change.owner.placeholder = "Enter arguments"
        t.observe(disabled, names='disabled')
        dlink((self, 'no_args'), (self.children[0], 'disabled'))
        dlink((self.children[0], 'value'), (self, 'content'))


class ExplorerOutput(Box):
    r"""
    A text box to output method results
    """
    value = Any()
    content = Any()
    in_error = Bool(False)

    def __init__(self, obj=None):
        self.value = obj
        self.output = HTMLMath("")
        self.output.add_class('explorable-value')
        self.clc = Event(source=self.output, watched_events=['click'])
        super(ExplorerOutput, self).__init__(
            (self.output,),
            layout = Layout(border='1px solid green', padding='2px 50px 2px 2px')
        )
        def propagate_click(event):
            pass
            #self.value = self.output.value
        self.clc.on_dom_event(propagate_click)

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
            layout=Layout(width='95%', border='1px solid yellow', padding='0')
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


class SageExplorer(VBox):
    """Sage Explorer in Jupyter Notebook"""

    value = Any()
    initial_name = Unicode()
    history_index = Integer(0)

    def __init__(self, obj=None):
        """
        TESTS::

            sage: from sage_explorer.sage_explorer import SageExplorer
            sage: t = StandardTableaux(15).random_element()
            sage: widget = SageExplorer(t)
        """
        self.donottrack = True # Prevent any interactivity while drawing the widget
        super(SageExplorer, self).__init__()
        self.value = obj
        self.get_initial_name()
        self._history = [obj]
        self.compute()
        self.donottrack = False

    def get_initial_name(self, test_sh_hist=[]):
        r"""Attempt to deduce the widget value variable name
        from notebook input history.
        In case it is not found, or not a string, set to `Hist[0]`.

        TESTS::
            sage: from sage_explorer.sage_explorer import _eval_in_main, SageExplorer
            sage: w = SageExplorer(42)
            sage: w.get_initial_name()
            sage: w.initial_name
            'Hist[0]'
            sage: import __main__
            sage: __main__.__dict__.update({'x': 42})
            sage: w.get_initial_name(test_sh_hist=["w = explore(42)", "w"])
            sage: w.initial_name
            'Hist[0]'
            sage: w.get_initial_name(test_sh_hist=["x=42", "w = explore(x)", "w"])
            sage: w.initial_name
            'x'
            sage: w.get_initial_name(test_sh_hist=["x=42", "w = explore(x)", "explore(43)", "w"])
            sage: w.initial_name
            'x'
        """
        self.initial_name = "Hist[0]"
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
                        pass
                    try:
                        if _eval_in_main(initial_name_candidate) == self.value:
                            self.initial_name = initial_name_candidate
                            break
                    except:
                        pass

    def compute(self):
        obj = self.value
        self.titlebox = ExplorerTitle(obj)
        self.titlebox.add_class('titlebox')
        self.titlebox.add_class('lightborder')
        self.description = ExplorerDescription(obj)
        self.props = ExplorerProperties(obj)
        dlink((self.props, 'value'), (self, 'value')) # Handle the clicks on property values
        self.propsbox = VBox([self.description, self.props])
        self.visualbox = ExplorerVisual(obj)
        self.visualbox.add_class('visualbox')
        self.top = VBox(
            [self.titlebox,
             HBox(
                 [self.propsbox, Separator(' '), self.visualbox],
                         layout=Layout(margin='10px 0')
             )
            ],
            layout=Layout(border='1px solid yellow')
        )

        self.menusbox = ExplorerMenus(obj)
        self.namingbox = ExplorerNaming(obj)
        self.namingbox.initial_name = self.initial_name
        dlink((self, 'history_index'), (self.namingbox, 'history_index'))
        self.searchbox = ExplorerMethodSearch(obj)
        self.argsbox = ExplorerArgs(obj)
        dlink((self.searchbox, 'no_args'), (self.argsbox, 'no_args'))
        self.runbutton = Button(
            description='Run!',
            tooltip='Run the method with specified arguments',
            layout = Layout(width='4em'))
        def compute_selected_method(button):
            method_name = self.searchbox.selected_method
            args = self.argsbox.content
            try:
                if AlarmInterrupt:
                    alarm(TIMEOUT)
                out = _eval_in_main("__obj__.{}({})".format(method_name, args), locals={"__obj__": obj})
                if AlarmInterrupt:
                    cancel_alarm()
            except AlarmInterrupt:
                self.output.output.value = "Timeout!"
            except Exception as e:
                self.outputbox.in_error = True
                self.outputbox.output.value = 'Error: %s; method_name=%s; input=%s;' % (e, method_name, self.argsbox.value)
                return
            self.outputbox.in_error = False
            self.outputbox.value = out
            self.outputbox.output.value = '$%s$' % out
        self.runbutton.on_click(compute_selected_method)
        self.actionbox = HBox([
            self.namingbox,
            Separator('.'),
            self.searchbox,
            Separator('('),
            self.argsbox,
            Separator(')'),
            self.runbutton
        ])
        self.outputbox = ExplorerOutput(obj)
        dlink((self.outputbox, 'value'), (self, 'value')) # Handle the clicks on output values
        self.helpbox = ExplorerHelp(obj)

        def selected_method_changed(change):
            self.helpbox.content = self.searchbox.get_doc()
        self.searchbox.observe(selected_method_changed, names='selected_method')
        self.bottom = VBox([self.actionbox, self.outputbox, self.helpbox])

        self.children = (self.top, self.bottom)

    def push_history(self, obj):
        r"""
        Push an object to explorer history.
        Ensure that history does not become too long.

        INPUT:

            - ``obj`` -- an object (the old one)

        TESTS::

            sage: from sage_explorer import SageExplorer
            sage: t = Tableau([[1, 2, 5, 6], [3], [4]])
            sage: n = 42
            sage: e = SageExplorer(t)
            sage: e._history
            [[[1, 2, 5, 6], [3], [4]]]
            sage: e.push_history(n)
            sage: e._history
            [[[1, 2, 5, 6], [3], [4]], 42]
        """
        self._history.append(obj)
        self.history_index = self.history_index + 1
        if len(self._history) > MAX_LEN_HISTORY:
            self._history = self._history[1:]

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
            [[[1, 2, 5, 6], [3], [4]]]
            sage: from traitlets import Bunch
            sage: e.value_changed(Bunch({'name': 'value', 'old': t, 'new': new_t, 'owner': e, 'type': 'change'}))
            sage: e._history
            [[[1, 2, 5, 6], [3], [4]], [[1, 2, 7, 6], [3], [4]]]
        """
        if self.donottrack:
            return
        old_val = change.old
        new_val = change.new
        actually_changed = (id(new_val) != id(old_val))
        if actually_changed:
            self.push_history(new_val)
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
        self.history_index = self.history_index - 1
        self.donottrack = True
        self.value = self._history[-1]
        self.compute()
        self.donottrack = False
