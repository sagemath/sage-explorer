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

    def append_child(self, new_child):
        self.children = [ x for x in self.children ] + [ new_child ]

class TestSelect(Select):
    def __init__(self):
        super(TestSelect, self).__init__()
        self.options = [1,2]

    def switch(self, options):
        self.options = options


class TestLink(HTML):
    """Test d'un lien HTML"""
    def __init__(self, s):
        super(TestLink, self).__init__()
        self.value = '<a href="%s">%s</a>' % (s,s)
