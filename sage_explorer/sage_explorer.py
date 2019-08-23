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
from cysignals.alarm import alarm, cancel_alarm
from cysignals.signals import AlarmInterrupt
from inspect import isclass
from ipywidgets import Accordion, Box, Button, Combobox, GridBox, HBox, HTML, HTMLMath, Label, Layout, Text, Textarea, VBox
from ipywidgets.widgets.widget_description import DescriptionStyle
from traitlets import Any, Unicode, dlink, observe
from ipywidgets.widgets.trait_types import InstanceDict, Color
from ipyevents import Event
from .explored_member import get_members, get_properties

title_layout = Layout(width='100%', padding='12px')
css_lines = []
css_lines.append(".title-level2 {font-size: 150%}")
css_lines.append('.explorer-title {background-color: teal; background-image: url("data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAB4AAAAeCAQAAACROWYpAAAABGdBTUEAALGPC/xhBQAAACBjSFJNAAB6JgAAgIQAAPoAAACA6AAAdTAAAOpgAAA6mAAAF3CculE8AAAAAmJLR0QA/4ePzL8AAAAHdElNRQfjCBQVGx7629/nAAAB60lEQVQ4y5WUQU8aQRSAv0UPGDcaJYKaCISj6VFJ6skfoEc5EUhIvWniTzFpjyb2ZJB/UBtMf0BvwA0WIfFAemqRSGJ2xwPDMLuz227nXd68ed/uvDfvPYhaZTwEAo9ylEsiEs5iAWCRjQOvs6ntCiEabLIeBqe4pkFR7mwfbEvtgDqf2QreIMVXXARP1MhQosEYIWVMgxJpKjgIPO5I6+gat7jKtcOrAufySos/UveoswGwDMASuyoAm/2Q3CT5oHSLjOTkOsQx/hYlQ46C365oUf5NJpybF9uh5XN6o0uTJl3efPYOuyZcYqq59LkkS5IkWS7oaydTSn7QYpWGDz32nR/78HvsWfVZlNmjQIGiKgWXK74E7nXBNUtSf+EnDg4D1PsupEveCCpPz/BzEyGtMWBk2EYMDFsiuqtirASeYcuRMWwZcobNW6ZqJCzPiZGwUw3WEjZ/qvv/f6rFMoskxwor5P5VJAA7tAPl2aNJk16gPFtsm3CNSazGeKEaRIs8xW5Jh0Md3eAhNioQfJtNklmRuDyr9x7TZmoENaXDROqCEa5+OB+AfSqkOQsZgNt8YigHYMj8vOW7isbmUcGPqnw+8oN6SP0RHPo3Cr7RrFukFht9Cv72fcoJ0eCX7hLdVUOETM8wyuUdTAVXcgNG490AAAAldEVYdGRhdGU6Y3JlYXRlADIwMTktMDgtMjBUMTk6Mjc6MzArMDI6MDCNIxYDAAAAJXRFWHRkYXRlOm1vZGlmeQAyMDE5LTA4LTIwVDE5OjI3OjMwKzAyOjAw/H6uvwAAAABJRU5ErkJggg=="); background-repeat: no-repeat; background-position: right;background-origin: content-box;}')
css_lines.append(".explorable-value {background-color: #ccc}")
css = HTML("<style>%s</style>" % '\n'.join(css_lines))

try:
    ip = get_ipython()
    ip.display_formatter.format(css)
except:
    pass # We are in the test environment

import __main__
def _eval_in_main(s, locals={}):
    """
    Evaluate the expression `s` in the global scope

    TESTS::
        sage: from sage_explorer.sage_explorer import _eval_in_main
        sage: from sage.combinat.tableau import Tableaux
        sage: _eval_in_main("Tableaux")
        <class 'sage.combinat.tableau.Tableaux'>
    """
    try:
        globs = sage.all.__dict__
    except:
        globs = __main__.__dict__
    globs.update(locals)
    return eval(s, globs)

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
        self.value = '$$%s$$' % value
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
        s = "Exploring: %s" % str(obj)
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
        if hasattr(obj, '_latex_list'):
            s = obj._latex_list()
        elif hasattr(obj, '_latex_'):
            s = obj._latex_()
        else:
            s = obj.__str__()
        h = HTMLMath('$%s$' % s)
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
        super(ExplorerVisual, self).__init__(layout = Layout(border='1px solid red'))
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
    content = Unicode('')

    def __init__(self, obj):
        self.value = obj
        t = Text(layout=Layout(width='55px', padding='0', margin='0'))
        super(ExplorerNaming, self).__init__(
            (t,),
            layout=Layout(padding='0')
        )
        def changed(change):
            self.content = change.new
        t.observe(changed, names='value')
        self.get_input_name()

    def get_input_name(self):
        self.children[0].value = "Hist[0]"


class ExplorerMethodSearch(Box):
    r"""
    A widget to search a method
    """
    value = Any()
    selected_method = Unicode('')

    def __init__(self, obj):
        self.value = obj
        self.get_members()
        c = Combobox(options=[m.name for m in self.members])
        super(ExplorerMethodSearch, self).__init__((c,))
        def changed(change):
            new_val = change.new
            if new_val in self.members_dict:
                self.selected_method = new_val
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


class ExplorerOutput(Box):
    r"""
    A text input to input method arguments
    """
    value = Any()
    content = Any()

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
        self.children[0].value = "$$%s$$" % self.content
        self.set_title(0, [l for l in self.content.split(".") if l][0].strip())


class SageExplorer(VBox):
    """Sage Explorer in Jupyter Notebook"""

    value = Any()

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
        self._history = []
        self.compute()
        self.donottrack = False

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
        self.searchbox = ExplorerMethodSearch(obj)
        self.inputbox = Text()
        self.inputbutton = Button(description='-', layout=Layout(width='30px'))
        self.gobutton = Button(description='Run!', tooltip='Run the method with specified arguments')
        def compute_selected_method(button):
            method_name = self.searchbox.selected_method
            args = self.inputbox.value
            try:
                if AlarmInterrupt:
                    alarm(TIMEOUT)
                out = _eval_in_main("__obj__.{}({})".format(method_name, args), locals={"__obj__": obj})
                if AlarmInterrupt:
                    cancel_alarm()
            except AlarmInterrupt:
                self.output.output.value = "Timeout!"
            except Exception as e:
                self.outputbox.output.value = 'Error: %s; method_name=%s; input=%s;' % (e, method_name, self.inputbox.value)
                return
            self.outputbox.value = out
            self.outputbox.output.value = '$%s$' % out
        self.gobutton.on_click(compute_selected_method)
        self.actionbox = HBox([
            self.namingbox,
            Separator('.'),
            self.searchbox,
            Separator('('),
            self.inputbox,
            self.inputbutton,
            Separator(')'),
            self.gobutton
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
            sage: e = SageExplorer(t)
            sage: e._history
            []
            sage: e.push_history(t)
            sage: e._history
            [[[1, 2, 5, 6], [3], [4]]]
        """
        self._history.append(obj)
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
            []
            sage: from traitlets import Bunch
            sage: e.value_changed(Bunch({'name': 'value', 'old': t, 'new': new_t, 'owner': e, 'type': 'change'}))
            sage: e._history
            [[[1, 2, 5, 6], [3], [4]]]
        """
        if self.donottrack:
            return
        old_val = change.old
        new_val = change.new
        actually_changed = (id(new_val) != id(old_val))
        if actually_changed:
            self.push_history(old_val)
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
        prev = self._history.pop()
        self.donottrack = True
        self.value = prev
        self.compute()
        self.donottrack = False
