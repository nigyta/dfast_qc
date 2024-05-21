#!/bin/bash

SCRIPT_DIR=$(cd $(dirname $(realpath $0)); pwd)


usage_exit() {
        echo "Usage: $0 [-n int] [-r dir/to/reference/data]" 1>&2
        exit 1
}

NUM_THREADS=1
while getopts n:r:h OPT
do
    case $OPT in
        n)  NUM_THREADS=$OPTARG
            ;;
        r)  REF_DIR="--ref_dir "$OPTARG
            ;;
        h)  usage_exit
            ;;
    esac
done
echo "===================== DFAST_QC initial setup ====================="


$SCRIPT_DIR/dqc_admin_tools.py download_master_files --targets asm ani tsr igp --num_threads $NUM_THREADS ${REF_DIR}
$SCRIPT_DIR/dqc_admin_tools.py update_taxdump ${REF_DIR}
$SCRIPT_DIR/dqc_admin_tools.py download_genomes --num_threads $NUM_THREADS ${REF_DIR}
$SCRIPT_DIR/dqc_admin_tools.py mash_ref_sketch --num_threads $NUM_THREADS ${REF_DIR}
$SCRIPT_DIR/dqc_admin_tools.py prepare_sqlite_db ${REF_DIR}
$SCRIPT_DIR/dqc_admin_tools.py prepare_checkm ${REF_DIR}
$SCRIPT_DIR/dqc_admin_tools.py update_checkm_db ${REF_DIR}
