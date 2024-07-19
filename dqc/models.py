import argparse
from peewee import Model, CharField, IntegerField, BooleanField, SqliteDatabase, FloatField
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

    def to_table(self):
        return [self.accession, str(self.taxid), str(self.species_taxid), self.organism_name, self.infraspecific_name, self.relation_to_type_material, 'validated' if self.is_valid else '-']

class Taxon(Model):  # for checkm reference data
    taxid = IntegerField(index=True)
    rank = CharField()
    taxon = IntegerField()
    genomes = IntegerField()
    marker_genes = IntegerField()
    marker_sets = IntegerField()

    class Meta:
        database = db

    def __str__(self):
        return f"<{self.taxid}: {self.rank} {self.taxon}>"

class GTDB_Reference(Model):
    # Representative genome   GTDB species    GTDB taxonomy   ANI circumscription radius      Mean intra-species ANI  Min intra-species ANI   Mean intra-species AF   Min intra-species AF    No. clustered genomes     Clustered genomes
    accession = CharField(primary_key=True)
    gtdb_species = CharField()
    gtdb_taxonomy = CharField()
    ani_circumscription_radius = FloatField()
    mean_intra_species_ani = CharField()
    min_intra_species_ani = CharField()    
    mean_intra_species_af = CharField()
    min_intra_species_af = CharField()
    num_clustered_genomes = IntegerField()
    clustered_genomes = CharField()

    class Meta:
        database = db

    def __str__(self):
        return f"<GTDB: {self.accession}, {self.gtdb_species}>"


class Genome_Size(Model):
    #species_taxid  min_ungapped_length     max_ungapped_length     expected_ungapped_length        number_of_genomes       method_determined
    species_taxid = IntegerField(primary_key=True)
    min_ungapped_length = IntegerField()
    max_ungapped_length = IntegerField()
    expected_ungapped_length = IntegerField()
    number_of_genomes = IntegerField()
    method_determined = CharField()

    class Meta:
        database = db

    def __str__(self):
        return f"<GenomeSize: {self.species_taxid}, {self.min_ungapped_length}-{self.max_ungapped_length}>"    

def init_db():
    db.connect()
    db.create_tables([Reference, Taxon, GTDB_Reference])


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
