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
import ipyvuetify as v
#from ipyvuetify import ExpansionPanel
from ipywidgets import Box, HBox, VBox, GridBox, Label, Layout, Text, HTML, HTMLMath, Button, Combobox
from ipywidgets.widgets.widget_description import DescriptionStyle
from traitlets import Any
from ipywidgets.widgets.trait_types import InstanceDict, Color
from inspect import isclass
from sage.misc.sphinxify import sphinxify
from .explored_member import get_members, get_properties

title_layout = Layout(width='100%', padding='12px')
css_lines = []
css_lines.append(".title-level2 {font-size: 150%}")
css_lines.append(".explorer-title {background-color: teal}")
css = HTML("<style>%s</style>" % '\n'.join(css_lines))

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
        self.value = sphinxify(value)
        self.add_class("title-level%d" % level)


class ExplorerTitle(Box):
    r"""The sage explorer title bar
    """
    value = Any()

    def __init__(self, obj):
        s = "Exploring: %s" % str(obj)
        #d = [l for l in obj.__doc__.split("\n") if l][0].strip()
        super(ExplorerTitle, self).__init__((MathTitle(s, 2),))
        self.add_class("explorer-title")
        self.value = obj


class ExplorableValue(HTML):
    r"""
    A repr string with a link for a Sage object.
    FIXME will be a DOMWidget or HTML, with a specific javascript View
    """
    value = Any()

    def __init__(self, val=None):
        if not val:
            s = ''
        else:
            s = "<span>%s</span>" % str(val)
        super(ExplorableValue, self).__init__(s)
        self.value = val


class ExplorerProperties(GridBox):
    r"""
    GridBox, or v.Container ?
    """
    value = Any()

    def __init__(self, obj):
        children = []
        for p in get_properties(obj):
            val = getattr(obj, p.name).__call__()
            children.append(Label(p.prop_label))
            children.append(ExplorableHTML(str(val)))
            children.append(Label("?"))
        super(ExplorerProperties, self).__init__(children, layout=Layout(grid_template_columns='40% 40% 20%'))
        self.value = obj


class ExplorerVisual(Box):
    r"""
    The sage explorer visual representation
    """
    value = Any()

    def __init__(self, obj):
        super(ExplorerVisual, self).__init__()
        self.value = obj
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


class ExplorerNaming(Text):
    r"""
    A text input to give a name
    """
    value = Any()

    def __init__(self, obj, label="x"):
        super(ExplorerNaming, self).__init__(label)
        self.value = obj

    def update(self, label):
        r"""
        FIXME check the namespace first
        """
        self.value = label


class ExplorerMethodSearch(v.Combobox):
    r"""
    A widget to search a method
    """
    value = Any()

    def __init__(self, obj):
        super(ExplorerMethodSearch, self).__init__()
        self.value = obj


class ExplorerInput(Text):
    r"""
    A text input to input method arguments
    """
    value = Any()

    def __init__(self, obj=None):
        super(ExplorerInput, self).__init__()
        self.value = obj


class ExplorerHelp(v.ExpansionPanel):
    r"""
    Contains help, or output + help as expandable
    Contains MathJax
    """
    value = Any()

    def __init__(self, obj):
        super(ExplorerHelp, self).__init__()
        self.value = obj


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
        self.propsbox = ExplorerProperties(obj)
        self.titlebox.add_class('titlebox')
        self.titlebox.add_class('lightborder')
        self.visualbox = ExplorerVisual(obj)
        self.visualbox.add_class('visualbox')

        self.top = GridBox([self.titlebox, self.visualbox, self.propsbox], layout=Layout(grid_template_columns='60% 40%'))

        self.menusbox = ExplorerMenus(obj)
        self.namingbox = ExplorerNaming(obj)
        self.searchbox = ExplorerMethodSearch(obj)
        self.inputbox = ExplorerInput()
        self.inputbutton = Button(description='-')
        self.gobutton = Button(description='Run!', tooltip='Run the function or method, with specified arguments')
        self.actionbox = HBox([self.namingbox, Label('.'), self.searchbox, Label('('), self.inputbox, self.inputbutton, Label(')'), self.gobutton])
        self.outputbox = ExplorableValue()
        self.helpbox = ExplorerHelp(obj)
        self.bottom = HBox([self.actionbox, self.outputbox, self.helpbox])
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
