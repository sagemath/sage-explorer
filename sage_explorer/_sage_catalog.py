"""Catalogs for Index Page"""

from sage.groups.affine_gps import catalog as affine_groups_catalog
from sage.groups.groups_catalog import presentation as presentation_groups_catalog
from sage.groups.perm_gps import permutation_groups_catalog as permutation_groups_catalog
from sage.groups.matrix_gps import catalog as matrix_groups_catalog
from sage.groups.misc_gps import misc_groups_catalog
from sage.algebras import catalog as algebras_catalog
from sage.combinat.posets.poset_examples import Posets as posets_catalog
from sage.monoids import all as monoids_catalog
from sage.graphs.graph_generators import GraphGenerators
graphs_catalog = GraphGenerators()
from sage.modules import all as modules_catalog
from sage.matroids import catalog as matroids_catalog
from sage.combinat.crystals import catalog as crystals_catalog
from sage.coding import codes_catalog
from sage.game_theory.catalog import normal_form_games as games_catalog
from sage.combinat.words import word_generators as words_catalog

class fields_catalog:
    r"""A catalog of fields."""
    from sage.rings.finite_rings.finite_field_constructor import FiniteField
    from sage.rings.complex_field import ComplexField
    from sage.rings.rational_field import RationalField
    from sage.rings.real_mpfr import RealField
    from sage.rings.qqbar import AlgebraicRealField, AlgebraicField

presentation_groups_catalog.name = "Groups given by presentation"
permutation_groups_catalog.name = "Permutation groups"
matrix_groups_catalog.name = "Matrix groups"
affine_groups_catalog.name = "Affine groups"
misc_groups_catalog.name = "Misc groups"
monoids_catalog.name = "Monoids"
fields_catalog.name = "Fields"
algebras_catalog.name = "Algebras"
modules_catalog.name = "Modules"
graphs_catalog.name = "Graphs"
posets_catalog.name = "Posets"
crystals_catalog.name = "Crystals"
codes_catalog.name = "Codes"
matroids_catalog.name = "Matroids"
games_catalog.name = "Games"
words_catalog.name = "Words"

sage_catalogs = [
    presentation_groups_catalog,
    permutation_groups_catalog,
    matrix_groups_catalog,
    affine_groups_catalog,
    misc_groups_catalog,
    monoids_catalog,
    fields_catalog,
    algebras_catalog,
    modules_catalog,
    graphs_catalog,
    posets_catalog,
    crystals_catalog,
    codes_catalog,
    matroids_catalog,
    games_catalog,
    words_catalog,
]
