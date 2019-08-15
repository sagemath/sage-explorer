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
- Odile Bénassy, Nicolas Thiéry, Nathan Carter

"""
from ipywidgets import Box, HBox, VBox, GridBox, Label, Layout, Text, HTML, HTMLMath, Accordion, Button, Combobox
from ipywidgets.widgets.widget_description import DescriptionStyle
from traitlets import Any
from ipywidgets.widgets.trait_types import InstanceDict, Color
from inspect import isclass
from ipyevents import Event
from .explored_member import get_members, get_properties

title_layout = Layout(width='100%', padding='12px')
css_lines = []
css_lines.append(".title-level2 {font-size: 150%}")
css_lines.append(".explorer-title {background-color: teal}")
css_lines.append(".explorable-value {background-color: #ccc}")
css = HTML("<style>%s</style>" % '\n'.join(css_lines))

try:
    ip = get_ipython()
    ip.display_formatter.format(css)
except:
    pass # We are in the test environment


def get_visual_widget(obj):
    r"""
    Which is the specialized widget class name for viewing this object (if any)

    TESTS::
        sage: from sage.all import *
        sage: from new_sage_explorer._widgets import *
        sage: from new_sage_explorer.new_sage_explorer import get_visual_widget
        sage: p = Partition([3,3,2,1])
        sage: get_visual_widget(p).__class__
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
        #d = [l for l in obj.__doc__.split("\n") if l][0].strip()
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

    def __init__(self, obj):
        self.value = obj
        s = [l for l in obj.__doc__.split("\n") if l][0].strip()
        super(ExplorerDescription, self).__init__((HTMLMath(s),))
        self.add_class("explorer-description")


class ExplorableValue(HBox):
    r"""
    A repr string with a link for a Sage object.
    FIXME will be a DOMWidget or HTML, with a specific javascript View
    """
    value = Any()

    def __init__(self, obj):
        self.value = obj # we should compute it -- or use it -- as a 'member'
        if hasattr(obj, '_latex_list'):
            s = obj._latex_list()
        elif hasattr(obj, '_latex_'):
            s = obj._latex_()
        else:
            s = obj.__str__()
        h = HTMLMath('$$%s$$' % s)
        h.add_class('explorable-value')
        l0 = Label(" ")
        l = Label("clc")
        def handle_clic(e):
            l.value = str(obj)
        clic = Event(source=h, watched_events=['click'])
        clic.on_dom_event(handle_clic)
        super(ExplorableValue, self).__init__(
            (h, l0, l),
            layout = Layout(border='1px solid green', padding='2px 50px 2px 2px')
        )


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
            children.append(ExplorableValue(val))
            #children.append(Label("?"))
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
        w = get_visual_widget(obj)
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
    A text input to give a name
    """
    value = Any()

    def __init__(self, obj, label="x"):
        self.value = obj
        super(ExplorerNaming, self).__init__(
            (Text(label),),
            layout=Layout(width='25px')
        )

    def update(self, label):
        r"""
        FIXME check the namespace first
        """
        self.value = label


class ExplorerMethodSearch(Box):
    r"""
    A widget to search a method
    """
    value = Any()

    def __init__(self, obj):
        self.value = obj
        self.get_members()
        c = Combobox(options=[m.name for m in self.members])
        super(ExplorerMethodSearch, self).__init__((c,))

    def get_members(self):
        if isclass(self.value):
            cls = self.value
        else:
            cls = self.value.__class__
        self.members = get_members(cls)


class ExplorerInput(Text):
    r"""
    A text input to input method arguments
    """
    value = Any()

    def __init__(self, obj=None):
        super(ExplorerInput, self).__init__()
        self.value = obj


class ExplorerOutput(Box):
    r"""
    A text input to input method arguments
    """
    value = Any()

    def __init__(self, obj=None):
        self.value = obj
        super(ExplorerOutput, self).__init__((HTMLMath("&nbsp;"),))


class ExplorerHelp(Accordion):
    r"""
    Contains help, or output + help as expandable
    Contains MathJax
    """
    value = Any()

    def __init__(self, obj):
        self.value = obj
        t = HTMLMath("$$%s$$" % obj.__doc__)
        super(ExplorerHelp, self).__init__(
            (t,),
            selected_index=None,
            layout=Layout(width='95%', border='1px solid yellow', padding='0')
        )
        self.set_title(0, "Help")


class NewSageExplorer(VBox):
    """Sage Explorer in Jupyter Notebook"""

    value = Any()

    def __init__(self, obj=None):
        """
        TESTS::

            sage: from new_sage_explorer.new_sage_explorer import NewSageExplorer
            sage: t = StandardTableaux(15).random_element()
            sage: widget = NewSageExplorer(t)
        """
        super(NewSageExplorer, self).__init__()
        self.titlebox = ExplorerTitle(obj)
        self.propsbox = VBox([ExplorerDescription(obj), ExplorerProperties(obj)])
        self.titlebox.add_class('titlebox')
        self.titlebox.add_class('lightborder')
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
        self.inputbox = ExplorerInput()
        self.inputbutton = Button(description='-', layout=Layout(width='30px'))
        self.gobutton = Button(description='Run!', tooltip='Run the function or method, with specified arguments')
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
        self.helpbox = ExplorerHelp(obj)

        self.bottom = VBox([self.actionbox, self.outputbox, self.helpbox])

        self.children = (self.top, self.bottom)
        self.history = []
        self.set_value(obj)

    def set_value(self, obj):
        r"""
        Set new math object `obj` to the explorer.

        TESTS::
            sage: from new_sage_explorer.new_sage_explorer import NewSageExplorer
            sage: from sage.combinat.partition import Partition
            sage: p = Partition([3,3,2,1])
            sage: e = NewSageExplorer(p)
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
        #self.compute()

    def get_value(self):
        r"""
        Return math object currently explored.

        TESTS::
            sage: from new_sage_explorer.new_sage_explorer import NewSageExplorer
            sage: from sage.combinat.partition import Partition
            sage: p = Partition([3,3,2,1])
            sage: e = NewSageExplorer(p)
            sage: e.get_value()
            [3, 3, 2, 1]
        """
        return self.value

    def pop_value(self):
        r"""
        Set again previous math object to the explorer.

        TESTS::
            sage: from new_sage_explorer.new_sage_explorer import NewSageExplorer
            sage: from sage.combinat.partition import Partition
            sage: p = Partition([3,3,2,1])
            sage: e = NewSageExplorer(p)
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
        #self.compute()
