# Code Directory

- `01-select-experiments.py`: Scores each experiment in `data/sra_result.csv` on three criteria (tissue/life stage known, study title informative about location/environment, corresponding RNA-seq suggested) and selects the top 100, breaking ties with a seeded random draw.
- `02-download-sra-data.py`: Downloads the experiments in `output/01/selected_experiments.csv` with SRA Toolkit (`prefetch`, `fasterq-dump`) and converts each run to gzipped FASTQ; re-running resumes. See `--help` for options.
