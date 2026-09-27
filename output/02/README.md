# Task 02 Output

Data downloaded from NCBI SRA by `code/02-download-sra-data.py` for the experiments in `output/01/selected_experiments.csv`. The sequence files are too large for git and are listed in `.gitignore`.

- `<experiment accession>/<run accession>_1.fastq.gz`, `_2.fastq.gz`: reads for each run in the experiment (single-end runs have one file)
- `<experiment accession>/.done`: marker listing the runs converted; the experiment is skipped on re-runs
- `download_log.tsv`: status of each experiment from the most recent run (`ok`, `skipped` or `failed`, with runs and any error message)
