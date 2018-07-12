"""Catalogs for Index Page"""

from sage.groups.groups_catalog import presentation as groups_catalog
from sage.groups.perm_gps import permutation_groups_catalog
from sage.groups.misc_gps import misc_groups_catalog
from sage.algebras import catalog as algebras_catalog
from sage.combinat.posets import poset_examples
from sage.monoids import all as monoids_all
from sage.graphs.generators import smallgraphs
from sage.modules import all as modules_all
from sage.matroids import catalog as matroids_catalog
import sage.combinat.crystals.catalog as crystals_catalog
from sage.coding import codes_catalog
from sage.game_theory.catalog import normal_form_games as games_catalog
from sage.combinat.words import word_generators

index_labels = ["Groups", "Permutations", "Misc Groups", "Fields", "Algebras", "Posets", "Monoids", "Graphs", "Modules", "Crystals", "Codes", "Matroids", "Games", "Words"]
index_catalogs = [
    groups_catalog,
    permutation_groups_catalog,
    misc_groups_catalog,
    None,
    algebras_catalog,
    poset_examples,
    monoids_all,
    smallgraphs,
    modules_all,
    crystals_catalog,
    codes_catalog,
    matroids_catalog,
    games_catalog,
    word_generators
]
