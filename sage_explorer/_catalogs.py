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
    from sage.rings.finite_rings.finite_field_constructor import FiniteField
    from sage.rings.complex_field import ComplexField
    from sage.rings.rational_field import RationalField
    from sage.rings.real_mpfr import RealField
    from sage.rings.qqbar import AlgebraicRealField, AlgebraicField

catalogs = [
    ("Groups given by presentation", presentation_groups_catalog),
    ("Permutation groups", permutation_groups_catalog),
    ("Matrix groups", matrix_groups_catalog),
    ("Affine groups", affine_groups_catalog),
    ("Misc groups", misc_groups_catalog),
    ("Monoids", monoids_catalog),
    ("Fields", fields_catalog),
    ("Algebras", algebras_catalog),
    ("Modules", modules_catalog),
    ("Graphs", graphs_catalog),
    ("Posets", posets_catalog),
    ("Crystals", crystals_catalog),
    ("Codes", codes_catalog),
    ("Matroids", matroids_catalog),
    ("Games", games_catalog),
    ("Words", words_catalog),
]
