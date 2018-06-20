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
from ipywidgets import Layout, VBox, HBox, Text, Label, HTML, Select
import traitlets

cell_layout = Layout(width='3em',height='2em', margin='0',padding='0')
box_layout = Layout()
css = HTML("<style></style>")
try:
    display(css)
except:
    pass # We are not in a notebook

def hierarchy(c):
    r"""Compute parental hierarchy tree for class c
    INPUT: class
    OUTPUT: LabelledRootedTree
    """
    out = {}
    out[c] = [ hierarchy(b) for b in c.__bases__ ]
    return LabelledRootedTree(out)

class SageExplorerObject(SageObject):
    def __init__(self, *args, **kws):
        super(SageExplorerObject, self).__init__(*args, **kws)

    def

class SageExplorer(VBox):
    """Sage Explorer in Jupyter Notebook"""

    def __init__(self, obj):
        """
        TESTS::

        S = StandardTableaux(15)
        t = S.random_element()
        widget = SageExplorer(t)
        widget.compute()
        assert widget.label == 'OK'
        """
        super(SageExplorer, self).__init__()
        self.obj = obj
        self.label = Label('OK')

    def compute(self):
        pass

    def get_object(self):
        return self.obj

    def set_object(self, obj):
        self.obj = obj
        self.compute()
