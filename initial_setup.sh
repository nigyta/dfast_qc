#!/bin/bash

usage_exit() {
        echo "Usage: $0 [-n int]" 1>&2
        exit 1
}

NUM_THREADS=1
while getopts n:h OPT
do
    case $OPT in
        n)  NUM_THREADS=$OPTARG
            ;;
        h)  usage_exit
            ;;
    esac
done
echo "===================== DFAST_QC initial setup ====================="

./dqc_admin_tools.py download_master_files --targets asm ani tsr hmm igp --num_threads $NUM_THREADS
./dqc_admin_tools.py update_taxdump
./dqc_admin_tools.py download_genomes --num_threads $NUM_THREADS
./dqc_admin_tools.py prepare_reference_hmm
./dqc_admin_tools.py prepare_reference_fasta --num_threads $NUM_THREADS
./dqc_admin_tools.py prepare_sqlite_db
./dqc_admin_tools.py prepare_checkm
./dqc_admin_tools.py update_checkm_db
