import os
import sys
from .models import Taxon


def show_taxon():
    sys.stdout.write("Available markers for CheckM\n")
    sys.stdout.write("\t".join(["taxid", "rank", "taxon_name", "#genomes", "#marker_genes", "#marker_sets"]) + "\n")

    for t in Taxon.select().order_by(Taxon.rank):
        L = [t.taxid, t.rank, t.taxon, t.genomes, t.marker_genes, t.marker_sets]
        sys.stdout.write("\t".join(map(str, L)) + "\n")
