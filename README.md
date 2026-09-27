# project-m4

Selects 100 oyster (*Magallana* / *Crassostrea*) sequencing experiments from an NCBI SRA search export and downloads them.

| Task | Code | Output |
|------|------|--------|
| 01 Select 100 experiments from `data/sra_result.csv` | `code/01-select-experiments.py` | `output/01/` |
| 02 Download the selected experiments from NCBI SRA | `code/02-download-sra-data.py` | `output/02/` (data not tracked in git) |

Task descriptions are in `Tasks.txt`; repository conventions are in `Instructions.txt`.

## Setup

```
pip install -r requirements.txt            # pandas
conda install -c bioconda sra-tools pigz   # needed for Task 02 only
```

## Running

Scripts can be run from any directory.

```
python3 code/01-select-experiments.py
python3 code/02-download-sra-data.py --threads 8
```

Task 02 downloads about 525 GB of SRA data and needs substantially more free space while converting to FASTQ. It can be re-run to resume.
