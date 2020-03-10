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
import os, re, six, types, operator as OP
from inspect import getargspec, getmro, isclass, isabstract
#from functools import lru_cache
try: # Are we in a Sage environment?
    import sage.all
    from sage.misc.sageinspect import sage_getargspec as getargspec
    from sage.misc.sage_eval import sage_eval as eval
except:
    pass

EXCLUDED_MEMBERS = ['__init__', '__repr__', '__str__']
OPERATORS = {'==' : OP.eq, '<' : OP.lt, '<=' : OP.le, '>' : OP.gt, '>=' : OP.ge}

import __main__
def _eval_in_main(s, locals={}):
    """
    Evaluate the expression `s` in the global scope

    TESTS::

        sage: from sage_explorer.explored_member import _eval_in_main
        sage: from sage.combinat.tableau import Tableaux
        sage: _eval_in_main("Tableaux")
        <class 'sage.combinat.tableau.Tableaux'>
    """
    try:
        globs = sage.all.__dict__
    except:
        globs = {}
    globs.update(__main__.__dict__)
    globs.update(locals)
    return eval(s, globs)

def getmembers(object):
    """Return all members of an object as (name, value) pairs sorted by name.
    This function patches inspect.getmembers
    because of Python3's new `__weakref__` attribute.

    TESTS::

        sage: from sage_explorer.sage_explorer import Settings
        sage: from sage_explorer.explored_member import getmembers
        sage: len(getmembers(1))
        272
        sage: len(getmembers(ZZ))
        316
    """
    if isclass(object):
        mro = (object,) + getmro(object)
    else:
        mro = ()
    results = []
    processed = set()
    names = dir(object)
    # :dd any DynamicClassAttributes to the list of names if object is a class;
    # this may result in duplicate entries if, for example, a virtual
    # attribute with the same name as a DynamicClassAttribute exists
    try:
        for base in object.__bases__:
            for k, v in base.__dict__.items():
                if isinstance(v, types.DynamicClassAttribute):
                    names.append(k)
    except AttributeError:
        pass
    for key in names:
        # First try to get the value via getattr.  Some descriptors don't
        # like calling their __get__ (see bug #1785), so fall back to
        # looking in the __dict__.
        if key == '__weakref__':
            continue
        try:
            value = getattr(object, key)
            # handle the duplicate key
            if key in processed:
                raise AttributeError
        except AttributeError:
            for base in mro:
                if key in base.__dict__:
                    value = base.__dict__[key]
                    break
            else:
                # could be a (currently) missing slot member, or a buggy
                # __dir__; discard and move on
                continue
        results.append((key, value))
        processed.add(key)
    results.sort(key=lambda pair: pair[0])
    return results


class ExploredMember(object):
    r"""
    A member of an explored object: method, attribute ..
    """
    vocabulary = ['name', 'member', 'container', 'member_type', 'doc', 'origin', 'overrides', 'privacy', 'prop_label', 'args', 'defaults']

    def __init__(self, name, **kws):
        r"""
        A method or attribute.
        Must have a name.

        TESTS::

            sage: from sage_explorer.explored_member import ExploredMember
            sage: from sage.combinat.partition import Partition
            sage: p = Partition([3,3,2,1])
            sage: m = ExploredMember('conjugate', container=p)
            sage: m.name
            'conjugate'
        """
        self.name = name
        for arg in kws:
            try:
                assert arg in self.vocabulary
            except:
                raise ValueError("Argument '%s' not in vocabulary." % arg)
            setattr(self, arg, kws[arg])

    def compute_member(self, container=None):
        r"""
        Get method or attribute value, given the name.

        TESTS::

            sage: from sage_explorer.explored_member import ExploredMember
            sage: from sage.combinat.partition import Partition
            sage: p = Partition([3,3,2,1])
            sage: m = ExploredMember('conjugate', container=p)
            sage: m.compute_member()
            sage: m.member
            <bound method Partitions_all_with_category.element_class.conjugate of [3, 3, 2, 1]>
            sage: x = 42
            sage: m = ExploredMember('denominator', container=x)
            sage: m.compute_member()
            sage: str(m.member)[:20]
            '<built-in method den'
        """
        if hasattr(self, 'member') and not container:
            return
        if not container and hasattr(self, 'container'):
            container = self.container
        if not container:
            return
        self.container = container
        self.member = getattr(container, self.name)
        self.doc = self.member.__doc__

    def compute_doc(self, container=None):
        r"""
        Get method or attribute documentation, given the name.

        TESTS::

            sage: from sage_explorer.explored_member import ExploredMember
            sage: from sage.combinat.partition import Partition
            sage: p = Partition([3,3,2,1])
            sage: m = ExploredMember('conjugate', container=p)
            sage: m.compute_doc()
            sage: m.doc[:100]
            '\n        Return the conjugate partition of the partition ``self``. This\n        is also called the a'
        """
        if hasattr(self, 'member'):
            self.doc = self.member.__doc__
        else:
            self.compute_member(container)

    def compute_member_type(self, container=None):
        r"""
        Get method or attribute value, given the name.

        TESTS::

            sage: from sage_explorer.explored_member import ExploredMember
            sage: from sage.combinat.partition import Partition
            sage: p = Partition([3,3,2,1])
            sage: m = ExploredMember('conjugate', container=p)
            sage: m.compute_member_type()
            sage: assert 'method' in m.member_type
            sage: x = 42
            sage: m = ExploredMember('denominator', container=x)
            sage: m.compute_member_type()
            sage: assert 'method' in m.member_type
        """
        if not hasattr(self, 'member'):
            self.compute_member(container)
        if not hasattr(self, 'member'):
            raise ValueError("Cannot determine the type of a non existent member.")
        m = re.match("<(type|class) '([.\\w]+)'>", str(type(self.member)))
        if m and ('method' in m.group(2)):
            self.member_type = m.group(2)
        elif callable(self.member):
            self.member_type = "callable (%s)" % str(type(self.member))
        else:
            self.member_type = "attribute (%s)" % str(type(self.member))

    def compute_privacy(self):
        r"""
        Compute member privacy, if any.

        TESTS::

            sage: from sage_explorer.explored_member import ExploredMember
            sage: from sage.combinat.partition import Partition
            sage: p = Partition([3,3,2,1])
            sage: m = ExploredMember('__class__', container=p)
            sage: m.compute_privacy()
            sage: m.privacy
            'python_special'
            sage: m = ExploredMember('_doccls', container=p)
            sage: m.compute_privacy()
            sage: m.privacy
            'private'
        """
        if not self.name.startswith('_'):
            self.privacy = None
            return
        if self.name.startswith('__') and self.name.endswith('__'):
            self.privacy = 'python_special'
        elif self.name.startswith('_') and self.name.endswith('_'):
            self.privacy = 'sage_special'
        else:
            self.privacy = 'private'

    def compute_origin(self, container=None):
        r"""
        Determine in which base class 'origin' of class 'container'
        this member is actually defined, and also return the list
        of overrides if any.

        TESTS::

            sage: from sage_explorer.explored_member import ExploredMember
            sage: from sage.combinat.partition import Partition
            sage: p = Partition([3,3,2,1])
            sage: m = ExploredMember('_reduction', container=p)
            sage: m.compute_origin()
            sage: m.origin, m.overrides
            (<class 'sage.combinat.partition.Partitions_all_with_category.element_class'>,
             [<class 'sage.categories.infinite_enumerated_sets.InfiniteEnumeratedSets.element_class'>,
              <class 'sage.categories.enumerated_sets.EnumeratedSets.element_class'>,
              <class 'sage.categories.sets_cat.Sets.Infinite.element_class'>,
              <class 'sage.categories.sets_cat.Sets.element_class'>,
              <class 'sage.categories.sets_with_partial_maps.SetsWithPartialMaps.element_class'>,
              <class 'sage.categories.objects.Objects.element_class'>])
        """
        if not container:
            if not hasattr(self, 'container'):
                raise ValueError("Cannot compute origin without a container.")
            container = self.container
        self.container = container
        if isclass(container):
            containerclass = container
        else:
            containerclass = container.__class__
        self.origin = None
        self.overrides = []
        for c in containerclass.__mro__:
            if self.name in c.__dict__:
                self.overrides.append(c)
                if self.origin is None: # and getattr(containerclass, self.name) == getattr(c, self.name):
                    self.origin = c
        if self.overrides:
            self.overrides = self.overrides[1:]

    def compute_argspec(self, container=None):
        r"""
        If this member is a method: compute its args and defaults.

        TESTS::

            sage: from sage_explorer.explored_member import ExploredMember
            sage: from sage.combinat.partition import Partition
            sage: p = Partition([3,3,2,1])
            sage: m = ExploredMember('add_cell', container=p)
            sage: m.compute_member()
            sage: m.compute_argspec()
            sage: m.args, m.defaults
            (['self', 'i', 'j'], (None,))
            sage: x = 42
            sage: m = ExploredMember('denominator', container=x)
            sage: m.compute_argspec()
            sage: m.args
            []
        """
        try:
            argspec = getargspec(self.member)
            if hasattr(argspec, 'args'):
                self.args = argspec.args
            if hasattr(argspec, 'defaults'):
                self.defaults = argspec.defaults
        except: # e.g. pure attribute
            self.args, self.defaults = [], []

    def compute_property_label(self, properties_settings={}):
        r"""
        Retrieve the property label, if any, from configuration 'properties_settings'.

        TESTS::

            sage: from sage_explorer.explored_member import ExploredMember
            sage: F = GF(7)
            sage: m = ExploredMember('polynomial', container=F)
            sage: m.compute_property_label({'polynomial': [{'in': 'Fields.Finite'}]})
            sage: m.prop_label
            'Polynomial'
            sage: G = PermutationGroup([[(1,2,3),(4,5)],[(3,4)]])
            sage: m = ExploredMember('cardinality', container=G)
            sage: m.compute_property_label({'cardinality': [{'in': 'EnumeratedSets.Finite'}]})
            sage: m.prop_label
            'Cardinality'
            sage: m = ExploredMember('category', container=G)
            sage: m.compute_property_label({'category': [{'in': 'Sets', 'label': 'A Better Category Label'}]})
            sage: m.prop_label
            'A Better Category Label'
            sage: m = ExploredMember('__abs__', container=1)
            sage: m.compute_property_label({'__abs__': [{'label': 'Absolute value'}]})
            sage: m.prop_label
            'Absolute value'
            sage: m.compute_property_label({'__abs__': [{'label': 'Absolute value', 'predicate': lambda x:False}]})
            sage: m.prop_label
            sage: from sage.rings.integer_ring import ZZ
            sage: m = ExploredMember('cardinality', container=ZZ)
            sage: m.compute_property_label({'cardinality': [{'predicate': Groups().Finite().__contains__}]})
            sage: m.prop_label
        """
        self.prop_label = None
        if self.name not in properties_settings:
            return
        if not hasattr(self, 'container'):
            raise ValueError("Cannot compute property label without a container.")
        contexts = properties_settings[self.name]
        def test_predicate(obj, predicate):
            return predicate(obj)
        def test_when(funcname, expected, operator=None, complement=None):
            if funcname == 'isclass': # FIXME Prendre les premières valeurs de obj.getmembers pour le test -> calculer cette liste avant ?
                res = _eval_in_main(funcname)(self.container)
            else:
                res = getattr(self.container, funcname).__call__()
            if operator and complement:
                res = operator(res, _eval_in_main(complement))
            return (res == expected)
        def split_when(s, context):
            when_parts = context['when'].split()
            funcname = when_parts[0]
            if len(when_parts) > 2:
                operatorsign, complement = when_parts[1], when_parts[2]
            elif len(when_parts) > 1:
                operatorsign, complement = when_parts[1][0], when_parts[1][1:]
            if operatorsign in OPERATORS.keys():
                operator = OPERATORS[operatorsign]
            else:
                operator = "not found"
            return funcname, operator, complement
        for context in contexts:
            fullfilled = True
            if 'predicate' in context.keys():
                if not context['predicate'](self.container):
                    fulfilled = False
                    continue
            if 'isinstance' in context.keys():
                """Test isinstance"""
                if not isinstance(self.container, _eval_in_main(context['isinstance'])):
                    fullfilled = False
                    continue
            if 'not isinstance' in context.keys():
                """Test not isinstance"""
                if isinstance(self.container, _eval_in_main(context['not isinstance'])):
                    fullfilled = False
                    continue
            if 'in' in context.keys():
                """Test in"""
                try:
                    if not self.container in _eval_in_main(context['in']):
                        fullfilled = False
                        continue
                except:
                    fullfilled = False
                    continue # The error is : descriptor 'category' of 'sage.structure.parent.Parent' object needs an argument
            if 'not in' in context.keys():
                """Test not in"""
                if self.container in _eval_in_main(context['not in']):
                    fullfilled = False
                    continue
            if 'when' in context.keys():
                """Test when predicate(s)"""
                if isinstance(context['when'], six.string_types):
                    when = [context['when']]
                elif isinstance(context['when'], (list,)):
                    when = context['when']
                else:
                    fullfilled = False
                    continue
                for predicate in when:
                    if not ' ' in predicate:
                        if not hasattr(self.container, predicate):
                            fullfilled = False
                            continue
                        if not test_when(predicate, True):
                            fullfilled = False
                            continue
                    else:
                        funcname, operator, complement = split_when(predicate, context)
                        if not hasattr(self.container, funcname):
                            fullfilled = False
                            continue
                        if operator == "not found":
                            fullfilled = False
                            continue
                        if not test_when(funcname, True, operator, complement):
                            fullfilled = False
                            continue
            if 'not when' in context.keys():
                """Test not when predicate(s)"""
                if isinstance(context['not when'], six.string_types):
                    nwhen = [context['not when']]
                if not test_when(context['not when'],False):
                    fullfilled = False
                    continue
                elif isinstance(context['not when'], (list,)):
                    nwhen = context['not when']
                else:
                    fullfilled = False
                    continue
                for predicate in nwhen:
                    if not ' ' in predicate:
                        if not test_when(predicate, False):
                            fullfilled = False
                            continue
                    else:
                        funcname, operator, complement = split_when(predicate)
                        if not test_when(funcname, False, operator, complement):
                            fullfilled = False
                            continue
                if fullfilled:
                    break # contexts should not overlap
            if not fullfilled:
                return
            if 'label' in context.keys():
                self.prop_label = context['label']
            else:
                self.prop_label = ' '.join([x.capitalize() for x in self.name.split('_')])


#@lru_cache(maxsize=100)
def get_members(cls, properties_settings, include_private=False):
    r"""
    Get all members for a class.

    INPUT: ``cls`` a Sage class.
    OUTPUT: List of `Member` named tuples.

    TESTS::

        sage: from sage_explorer.explored_member import get_members
        sage: from sage_explorer.sage_explorer import Settings
        sage: from sage.combinat.partition import Partition
        sage: mm = get_members(42, Settings.properties)
        sage: mm = get_members(int(42), Settings.properties)
        sage: mm = get_members(NN, Settings.properties)
        sage: mm[0].name, mm[0].origin
        ('CartesianProduct', None)
        sage: mm = get_members(Partition, Settings.properties, include_private=True)
        sage: mm[2].name, mm[2].privacy
        ('__class__', 'python_special')
        sage: [(mm[i].name, mm[i].origin, mm[i].overrides, mm[i].privacy) for i in range(len(mm)) if mm[i].name == '_unicode_art_']
        [('_unicode_art_',
          <class 'sage.combinat.partition.Partition'>,
          [<class 'sage.structure.sage_object.SageObject'>],
          'sage_special')]
        sage: from sage.combinat.tableau import Tableau
        sage: mm = get_members(Tableau([[1], [2], [3]]), Settings.properties)
        sage: [(mm[i].name, mm[i].container, mm[i].origin, mm[i].prop_label) for i in range(len(mm)) if mm[i].name == 'cocharge']
        [('cocharge', [[1], [2], [3]], <class 'sage.combinat.tableau.Tableau'>, 'Cocharge')]
        sage: mm = get_members(Groups(), Settings.properties)
        sage: (mm[0].name, mm[0].container, mm[0].origin, mm[0].overrides)
        ('Algebras',
         Category of groups,
         <class 'sage.categories.groups.Groups'>,
         [<class 'sage.categories.sets_cat.Sets.subcategory_class'>])
    """
    members = []
    for name, member in getmembers(cls):
        if isabstract(member) or 'deprecated' in str(type(member)).lower():
            continue
        m = ExploredMember(name, member=member, container=cls)
        m.compute_member_type()
        m.compute_origin()
        m.compute_privacy()
        if not include_private and m.privacy:
            continue
        m.compute_property_label(properties_settings)
        members.append(m)
    return members

#@lru_cache(maxsize=500)
def get_properties(obj, properties_settings={}):
    r"""
    Get all properties for an object.

    INPUT: ``obj`` a Sage object.
    OUTPUT: List of `Member` named tuples.

    TESTS::

        sage: from sage_explorer.explored_member import get_properties
        sage: from sage.combinat.tableau import *
        sage: st = StandardTableaux(3).an_element()
        sage: sst = SemistandardTableaux(3).an_element()
        sage: G = PermutationGroup([[(1,2,3),(4,5)],[(3,4)]])
        sage: from sage_explorer.sage_explorer import Settings
        sage: pp = get_properties(st, Settings.properties)
        sage: [p.name for p in pp]
        ['charge', 'cocharge', 'conjugate', 'parent']
        sage: pp[3].name, pp[3].prop_label
        ('parent', 'Element of')
        sage: pp = get_properties(sst, Settings.properties)
        sage: pp[3].name, pp[3].prop_label
        ('is_standard', 'Is Standard')
        sage: pp = get_properties(G, Settings.properties)
        sage: [p.name for p in pp]
        ['an_element', 'cardinality', 'category']
        sage: len(pp)
        3
        sage: [p.name for p in get_properties(1, Settings.properties)]
        ['parent']
        sage: Settings.add_property('__abs__')
        sage: [p.name for p in get_properties(1, Settings.properties)]
        ['__abs__', 'parent']
        sage: Settings.remove_property('__abs__')
        sage: Settings.add_property('__abs__', predicate=lambda x:False)
        sage: [p.name for p in get_properties(1, Settings.properties)]
        ['parent']
    """
    try:
        members = getmembers(obj)
    except:
        return [] # Can be a numeric value ..
    properties = []
    for name, member in members:
        if isabstract(member) or 'deprecated' in str(type(member)).lower():
            continue
        m = ExploredMember(name, member=member, container=obj)
        m.compute_property_label(properties_settings)
        if m.prop_label:
            properties.append(m)
    return properties
