# -*- coding: utf-8 -*-

#from sage.combinat.tableau import *
from sage.combinat.rooted_tree import LabelledRootedTree
from inspect import getdoc, getsource, getmembers, ismethod, isbuiltin, getargspec


def class_hierarchy(c):
    r"""Compute parental hierarchy tree for class c
    INPUT: class
    OUTPUT: LabelledRootedTree of its parents
    EXAMPLES::
    sage: var('X')
    sage: P = 2*X^2 + 3*X + 4
    sage: hierarchy(P.__class__)
    <type 'sage.symbolic.expression.Expression'>[<type 'sage.structure.element.CommutativeRingElement'>[<type 'sage.structure.element.RingElement'>[<type 'sage.structure.element.ModuleElement'>[<type 'sage.structure.element.Element'>[<type 'sage.structure.sage_object.SageObject'>[<type 'object'>[]]]]]]]
    sage: P = Partitions(7)[3]
    sage: hierarchy(P.__class__)
    <class 'sage.combinat.partition.Partitions_n_with_category.element_class'>[<class 'sage.combinat.partition.Partition'>[<class 'sage.combinat.combinat.CombinatorialElement'>[<class 'sage.combinat.combinat.CombinatorialObject'>[<type 'sage.structure.sage_object.SageObject'>[<type 'object'>[]]], <type 'sage.structure.element.Element'>[<type 'sage.structure.sage_object.SageObject'>[<type 'object'>[]]]]], <class 'sage.categories.finite_enumerated_sets.FiniteEnumeratedSets.element_class'>[<class 'sage.categories.enumerated_sets.EnumeratedSets.element_class'>[<class 'sage.categories.sets_cat.Sets.element_class'>[<class 'sage.categories.sets_with_partial_maps.SetsWithPartialMaps.element_class'>[<class 'sage.categories.objects.Objects.element_class'>[<type 'object'>[]]]]], <class 'sage.categories.finite_sets.FiniteSets.element_class'>[<class 'sage.categories.sets_cat.Sets.element_class'>[<class 'sage.categories.sets_with_partial_maps.SetsWithPartialMaps.element_class'>[<class 'sage.categories.objects.Objects.element_class'>[<type 'object'>[]]]]]]]
    """
    return LabelledRootedTree([class_hierarchy(b) for b in c.__bases__], label=c)

def method_origin(obj, name):
    """Return class where method 'name' is actually defined"""
    c0 = obj.__class__
    ct = class_hierarchy(c0)
    traversal = ct.pre_order_traversal_iter()
    ret = c0
    while 1:
        next = traversal.next()
        if not next:
            break
        c = next.label()
        if c == c0:
            continue
        if not name in [x[0] for x in getmembers(c)]:
            continue
        #print
        #print c
        for x in getmembers(c):
            if x[0] == name:
                #print "ok"
                #print x[1]
                #print getattr(c0, name)
                if x[1] == getattr(c0, name):
                    ret = c
    return ret

def method_origins(obj, names):
    """Return class where methods in list 'names' are actually defined"""
    c0 = obj.__class__
    ct = class_hierarchy(c0)
    traversal = ct.pre_order_traversal_iter()
    ret = {}
    for name in names:
        ret[name] = c0
    while 1:
        next = traversal.next()
        if not next:
            break
        c = next.label()
        if c == c0:
            continue
        for name in names:
            if not name in [x[0] for x in getmembers(c)]:
                continue
            for x in getmembers(c):
                if x[0] == name:
                    if x[1] == getattr(c0, name):
                        ret[name] = c
    return ret




S = StandardTableaux(15)
t = S.random_element()

ct = class_hierarchy(t.__class__)
print method_origin(t, 'add_entry')
print method_origins(t, ['add_entry', 'pp', 'append'])
print method_origins(t, [m[0] for m in getmembers(t)])
