#!/usr/bin/env python3
"""
Task 02: download the experiments in output/01/selected_experiments.csv from
NCBI SRA and convert them to gzipped FASTQ.

Each input row is an experiment accession (SRX/ERX/DRX). prefetch expands an
experiment into its runs (SRR/ERR/DRR), so each experiment gets its own
directory and every run found there is converted with fasterq-dump:

    output/02/<experiment>/<run>_1.fastq.gz, <run>_2.fastq.gz, ...

Experiments with a .done marker are skipped, so the script can be re-run to
resume after an interruption. The .sra files are deleted after conversion
unless --keep-sra is given. A per-experiment log is written to
output/02/download_log.tsv.

Requires SRA Toolkit (prefetch, fasterq-dump): conda install -c bioconda sra-tools
"""

import argparse
import csv
import shutil
import subprocess
import sys
from pathlib import Path

import pandas as pd

REPO = Path(__file__).resolve().parent.parent
DEFAULT_INPUT = REPO / 'output' / '01' / 'selected_experiments.csv'
DEFAULT_OUTDIR = REPO / 'output' / '02'

# Free space needed per experiment, as a multiple of its SRA size: the .sra
# file, fasterq-dump's temporary files and the uncompressed FASTQ.
SPACE_FACTOR = 4


def parse_args():
    p = argparse.ArgumentParser(description=__doc__,
                                formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument('--input', type=Path, default=DEFAULT_INPUT,
                   help='CSV with an "Experiment Accession" column')
    p.add_argument('--outdir', type=Path, default=DEFAULT_OUTDIR)
    p.add_argument('--bin-dir', type=Path,
                   help='directory containing prefetch and fasterq-dump '
                        '(default: search PATH)')
    p.add_argument('--threads', type=int, default=4)
    p.add_argument('--max-size', default='50G',
                   help='prefetch --max-size (prefetch default is 20G)')
    p.add_argument('--keep-sra', action='store_true',
                   help='keep .sra files after conversion')
    return p.parse_args()


def find_tool(name, bin_dir):
    if bin_dir:
        path = bin_dir / name
        return str(path) if path.exists() else None
    return shutil.which(name)


def run(cmd):
    subprocess.run(cmd, check=True, stdout=subprocess.PIPE,
                   stderr=subprocess.PIPE, universal_newlines=True)


def gzip_files(paths, threads):
    pigz = shutil.which('pigz')
    cmd = [pigz, '-p', str(threads)] if pigz else ['gzip']
    if paths:
        run(cmd + [str(p) for p in paths])


def download_experiment(accession, outdir, tools, args):
    """Download and convert one experiment. Returns (status, runs, message)."""
    exp_dir = outdir / accession
    done = exp_dir / '.done'
    if done.exists():
        return 'skipped', done.read_text().split(), 'already done'

    exp_dir.mkdir(parents=True, exist_ok=True)
    try:
        run([tools['prefetch'], accession, '--output-directory', str(exp_dir),
             '--max-size', args.max_size])

        sra_files = sorted(exp_dir.glob('*/*.sra')) + sorted(exp_dir.glob('*/*.sralite'))
        if not sra_files:
            return 'failed', [], 'prefetch produced no .sra files'

        runs = []
        for sra in sra_files:
            run_id = sra.parent.name
            run([tools['fasterq-dump'], str(sra), '--outdir', str(exp_dir),
                 '--temp', str(exp_dir), '--threads', str(args.threads),
                 '--split-files'])
            fastqs = sorted(exp_dir.glob(f'{run_id}*.fastq'))
            if not fastqs:
                return 'failed', runs, f'fasterq-dump produced no FASTQ for {run_id}'
            gzip_files(fastqs, args.threads)
            if not args.keep_sra:
                shutil.rmtree(sra.parent)
            runs.append(run_id)

        done.write_text('\n'.join(runs) + '\n')
        return 'ok', runs, ''

    except subprocess.CalledProcessError as e:
        return 'failed', [], f'{Path(e.cmd[0]).name} exited {e.returncode}: {e.stderr.strip()}'


def main():
    args = parse_args()

    if not args.input.exists():
        sys.exit(f'Error: input file {args.input} not found.')

    tools = {name: find_tool(name, args.bin_dir) for name in ['prefetch', 'fasterq-dump']}
    missing = [name for name, path in tools.items() if not path]
    if missing:
        sys.exit(f'Error: {", ".join(missing)} not found. Install SRA Toolkit '
                 '(conda install -c bioconda sra-tools) or pass --bin-dir.')

    df = pd.read_csv(args.input)
    if 'Experiment Accession' not in df.columns:
        sys.exit('Error: "Experiment Accession" column not found in input file.')
    sizes_mb = (df.set_index('Experiment Accession')['Total Size, Mb']
                if 'Total Size, Mb' in df.columns else pd.Series(dtype=float))

    args.outdir.mkdir(parents=True, exist_ok=True)
    accessions = df['Experiment Accession'].tolist()
    total_gb = sizes_mb.sum() / 1024
    free_gb = shutil.disk_usage(args.outdir).free / 1024**3
    print(f'{len(accessions)} experiments, about {total_gb:.0f} GB of SRA data; '
          f'{free_gb:.0f} GB free in {args.outdir}')

    log_path = args.outdir / 'download_log.tsv'
    results = {'ok': 0, 'skipped': 0, 'failed': 0}
    with open(log_path, 'w', newline='') as log:
        writer = csv.writer(log, delimiter='\t')
        writer.writerow(['experiment', 'status', 'runs', 'message'])

        for i, accession in enumerate(accessions, 1):
            print(f'[{i}/{len(accessions)}] {accession} ... ', end='', flush=True)

            need_gb = sizes_mb.get(accession, 0) * SPACE_FACTOR / 1024
            free_gb = shutil.disk_usage(args.outdir).free / 1024**3
            if not (args.outdir / accession / '.done').exists() and free_gb < need_gb:
                print(f'stopping: {free_gb:.0f} GB free, need about {need_gb:.0f} GB')
                writer.writerow([accession, 'failed', '', 'not enough disk space'])
                results['failed'] += 1
                break

            status, runs, message = download_experiment(accession, args.outdir, tools, args)
            print(status + (f' ({message})' if message else ''))
            writer.writerow([accession, status, ','.join(runs), message])
            log.flush()
            results[status] += 1

    print(f'\nDone: {results["ok"]} downloaded, {results["skipped"]} already present, '
          f'{results["failed"]} failed. Log: {log_path}')
    if results['failed']:
        sys.exit(1)


if __name__ == '__main__':
    main()
