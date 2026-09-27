# Task 01 Output

`selected_experiments.csv`: 100 experiments selected from `data/sra_result.csv` by `code/01-select-experiments.py`. It has the original SRA columns plus:

- `tissue_known`: tissue or life stage named in the experiment title, library name or sample code (or a single tissue named in the study title)
- `informative_title`: study title mentions a location, habitat or environmental condition (e.g. wild, populations, pH, heat, desiccation)
- `rnaseq_suggested`: study title indicates RNA-seq/transcriptome data (the export itself contains no RNA-seq libraries, so this is the only available signal)
- `score`: sum of the three criteria (0 to 3)

Selection: all 12 experiments scoring 3 and all 49 scoring 2, plus 39 of the 400 scoring 1 drawn at random (seed 42). The export has no RNA-seq libraries; all selected data are Bisulfite-Seq (75), ATAC-seq (23) or MeDIP-Seq (2). Total size is about 525 GB across 101 runs.
