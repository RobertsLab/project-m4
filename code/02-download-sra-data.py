#!/usr/bin/env python3
"""
Script to download SRA experiments from NCBI based on selected experiments CSV file.
This script reads the experiment accessions from the Task 01 output and downloads 
the corresponding SRA data using the SRA Toolkit.
"""

import pandas as pd
import subprocess
import os
import sys
from pathlib import Path

def check_sra_toolkit():
    """Check if SRA Toolkit is installed and available."""
    # Try common paths for SRA tools
    prefetch_paths = [
        '/mmfs1/home/sr320/miniforge3/bin/prefetch',
        'prefetch',  # if it's in PATH
        '/usr/local/bin/prefetch',
        '/usr/bin/prefetch'
    ]
    
    for prefetch_path in prefetch_paths:
        try:
            result = subprocess.run([prefetch_path, '--version'], 
                                  stdout=subprocess.PIPE, stderr=subprocess.PIPE, 
                                  universal_newlines=True, check=True)
            print(f"SRA Toolkit found at {prefetch_path}: {result.stdout.strip()}")
            return prefetch_path
        except (subprocess.CalledProcessError, FileNotFoundError):
            continue
    
    print("Error: SRA Toolkit not found. Please install SRA Toolkit first.")
    print("You can install it using: conda install -c bioconda sra-tools")
    return None

def download_sra_experiment(accession, output_dir, prefetch_path):
    """Download a single SRA experiment using prefetch and fasterq-dump."""
    try:
        print(f"Downloading {accession}...")
        
        # Determine fasterq-dump path based on prefetch path
        if prefetch_path == '/mmfs1/home/sr320/miniforge3/bin/prefetch':
            fasterq_path = '/mmfs1/home/sr320/miniforge3/bin/fasterq-dump'
        else:
            fasterq_path = 'fasterq-dump'
        
        # First, prefetch the SRA file
        prefetch_cmd = [prefetch_path, accession, '--output-directory', output_dir]
        result = subprocess.run(prefetch_cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, 
                              universal_newlines=True, check=True)
        
        # Then convert to FASTQ using fasterq-dump
        sra_path = os.path.join(output_dir, accession, f"{accession}.sra")
        if os.path.exists(sra_path):
            fastq_cmd = [fasterq_path, sra_path, '--outdir', output_dir, '--split-files']
            result = subprocess.run(fastq_cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, 
                                  universal_newlines=True, check=True)
            print(f"Successfully downloaded and converted {accession}")
            return True
        else:
            print(f"Warning: SRA file not found for {accession}")
            return False
            
    except subprocess.CalledProcessError as e:
        print(f"Error downloading {accession}: {e}")
        print(f"Command output: {e.stdout}")
        print(f"Command error: {e.stderr}")
        return False

def main():
    """Main function to download all selected SRA experiments."""
    
    # Define file paths
    input_file = "../output/01/selected_experiments.csv"
    output_dir = "../output/02"
    
    # Convert to absolute paths
    script_dir = Path(__file__).parent
    input_file = script_dir / input_file
    output_dir = script_dir / output_dir
    
    # Check if input file exists
    if not input_file.exists():
        print(f"Error: Input file {input_file} not found.")
        sys.exit(1)
    
    # Check SRA Toolkit
    prefetch_path = check_sra_toolkit()
    if not prefetch_path:
        sys.exit(1)
    
    # Create output directory if it doesn't exist
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Read the selected experiments CSV
    try:
        df = pd.read_csv(input_file)
        print(f"Found {len(df)} experiments to download")
    except Exception as e:
        print(f"Error reading input file: {e}")
        sys.exit(1)
    
    # Extract experiment accessions
    if 'Experiment Accession' not in df.columns:
        print("Error: 'Experiment Accession' column not found in CSV file")
        sys.exit(1)
    
    accessions = df['Experiment Accession'].tolist()
    
    # Download each experiment
    successful_downloads = 0
    failed_downloads = 0
    
    for i, accession in enumerate(accessions, 1):
        print(f"\nProcessing {i}/{len(accessions)}: {accession}")
        
        if download_sra_experiment(accession, str(output_dir), prefetch_path):
            successful_downloads += 1
        else:
            failed_downloads += 1
    
    # Print summary
    print(f"\n" + "="*50)
    print(f"Download Summary:")
    print(f"Total experiments: {len(accessions)}")
    print(f"Successful downloads: {successful_downloads}")
    print(f"Failed downloads: {failed_downloads}")
    print(f"Output directory: {output_dir}")
    
    if failed_downloads > 0:
        print(f"\nNote: {failed_downloads} downloads failed. Check the error messages above.")

if __name__ == "__main__":
    main()
