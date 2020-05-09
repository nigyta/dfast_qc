import argparse
from peewee import Model, CharField, IntegerField, BooleanField, SqliteDatabase
from .common import get_ref_path
from .config import config

sqlite_db_path = get_ref_path(config.SQLITE_REFERENCE_DB)
db = SqliteDatabase(sqlite_db_path)

class Reference(Model):
    accession = CharField(primary_key=True)
    taxid = IntegerField()
    species_taxid = IntegerField()
    organism_name = CharField()
    species_name = CharField()
    infraspecific_name = CharField()
    relation_to_type_material = CharField()
    is_valid = BooleanField()

    class Meta:
        database = db

    def __str__(self):
        return f"<{self.accession} {self.organism_name} {self.infraspecific_name}, {self.relation_to_type_material}, {'validated' if self.is_valid else '-'}>"

class Taxon(Model):
    taxid = IntegerField(primary_key=True)
    rank = CharField()
    taxon = IntegerField()
    genomes = IntegerField()
    marker_genes = IntegerField()
    marker_sets = IntegerField()

    class Meta:
        database = db

    def __str__(self):
        return f"<{self.taxid}: {self.rank} {self.taxon}>"


def init_db():
    db.connect()
    db.create_tables([Reference, Taxon])


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='DFAST_QC DB search')
    parser.add_argument('accessions', nargs="+", help='Assembly accession no. (GCA_******)')

    args = parser.parse_args()
    print(f"Search accession no. {args.accessions}")
    for acc in args.accessions:
        ref = Reference.get_or_none(Reference.accession==acc)
        if ref:
            print(ref)
        else:
            print(f"'{acc}' not found.")
