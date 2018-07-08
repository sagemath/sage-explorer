# -*- coding: utf-8 -*-
r"""
Tests in Jupyter Notebook
"""
from ipywidgets import Layout, Box, VBox, HBox, Text, Label, HTML, Select, Textarea, Accordion, Tab, Button
import traitlets

EXPL_ROOT = '/home/odile/odk/sage/git/nthiery/odile/explorer'
jscode = open(EXPL_ROOT + "/TestPage.js").read()
js = HTML("<script>%s</script>" % jscode)
try:
    display(js)
    IP = get_ipython()
except:
    pass # We are not in a notebook

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


# Persisting link identifiers
# On pourrait vouloir le mettre dans ip = get_ipython()
mylinkids = []
def increment(l):
    """Append next positive integer at the end of list l"""
    if not mylinkids:
        newid = 1
    else:
        newid = mylinkids[-1] + 1
    mylinkids.append(newid)
    return newid


class LinkObj:
    """Un lien HTML riche d'informations
    En particulier : un identifiant numérique
    et la ligne de commande qui va permettre de créer un nouvel objet Sage"""
    def __init__(self, label, cmd, title=None):
        self.ident = increment(mylinkids)
        self.label = label
        self.cmd = cmd
        self.title = title or label

    def display(self):
        """Use Sphinx syntax"""
        pass

    def direct_html(self):
        #return '<a id="%d" title="%s" href="%s">%s</a>' % (self.ident, self.title, self.command, self.label)
        return '<a id="%d" title="%s" href="javascript:alert(\'%s\'); NavHTMLModel.selected_link">%s</a>' % (self.ident, self.title, self.cmd, self.label)

class NavBox(VBox):
    """Boîte de test pour navigation explorer.
    Contient du HTML avec des liens, et un Label pour voir le résultat"""
    def __init__(self, linkobjs):
        super(NavBox, self).__init__()
        self.html = NavHTML(linkobjs)
        self.res = Label()
        traitlets.dlink((self.html, 'selected_link'), (self.res, 'value'))
        self.children = [self.html, self.res]

class NavHTML(HTML):
    """Test création widget dédié pour navigation explorer"""
    #selected_link = traitlets.Int(None, help="Selected link", allow_none=True).tag(sync=True)
    selected_link = traitlets.Unicode('No link selected yet', help="Selected link", allow_none=True).tag(sync=True)

    def __init__(self, linkobjs):
        """linkobjs est un dictionnaire ident -> linkobj"""
        super(NavHTML, self).__init__()
        _view_name = traitlets.Unicode('MyHTMLView').tag(sync=True)
        _model_name = traitlets.Unicode('MyHTMLModel').tag(sync=True)
        self.links = linkobjs
        self.value = ''
        for link, linkobj in self.links.items():
            self.value += "<p>%s : %s</p>" % (link, linkobj.direct_html())

    #def update(self, ident):
    #    self.selected_link = self.links[ident].cmd
