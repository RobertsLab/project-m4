#!/usr/bin/env python3
"""
Task 01: select 100 experiments from data/sra_result.csv.

Each experiment gets one point for each criterion it meets:
  - tissue_known:      tissue or life stage is named in the experiment metadata
  - informative_title: study title says something about location or environment
  - rnaseq_suggested:  the study indicates corresponding RNA-seq data exists

Experiments are ranked by total score. Ties are broken by a seeded random
shuffle, so any experiments filled in from a partially used score tier are a
reproducible random draw.
"""

import re
from pathlib import Path

import pandas as pd

SEED = 42
N_SELECT = 100

REPO = Path(__file__).resolve().parent.parent
INPUT = REPO / 'data' / 'sra_result.csv'
OUTPUT = REPO / 'output' / '01' / 'selected_experiments.csv'

# Tissue and life stage terms (matched as substrings, so 'gonad' covers
# 'gonads' and 'gonadal', 'embryo' covers 'embryos').
TISSUE_TERMS = [
    'gill', 'ctenidia', 'mantle', 'gonad', 'muscle', 'hepatopancreas',
    'digestive gland', 'hemocyte', 'haemocyte', 'soft tissue', 'somatic tissue',
    'sperm', 'oocyte', 'egg',
]
LIFE_STAGE_TERMS = [
    'larva', 'embryo', 'morula', 'blastula', 'gastrula', 'trochophore',
    'veliger', 'spat', 'juvenile', 'adult',
]
# Sample codes such as GT1_09_T0_G_R, where G = gill and M = mantle.
TISSUE_CODE = re.compile(r'_t\d+_[gm]_', re.IGNORECASE)

# Location and environment terms for the study title. Pathogen, strain and
# growth terms are left out: they describe the experimental design, not where
# the animals came from or the conditions they lived in.
LOCATION_TERMS = [
    'china', 'chinese', 'france', 'french', 'japan', 'korea', 'washington',
    'intertidal', 'subtidal', 'estuar', 'wild', 'field', 'populations',
    'environment',
]
ENVIRONMENT_TERMS = [
    'heat', 'temperature', 'thermal', 'desiccation', 'dessication', 'salinity',
    'hypoxia', 'acidification',
]
PH_PATTERN = re.compile(r'\bph\b', re.IGNORECASE)

RNASEQ_PATTERN = re.compile(r'rna-seq|rnaseq|transcriptom|gene expression',
                            re.IGNORECASE)


def text(value):
    return '' if pd.isna(value) else str(value).lower()


def tissues_in(s):
    return {t for t in TISSUE_TERMS + LIFE_STAGE_TERMS if t in s}


def tissue_known(row):
    sample_text = ' '.join(text(row[c]) for c in
                           ['Experiment Title', 'Sample Title', 'Library Name'])
    if tissues_in(sample_text) or TISSUE_CODE.search(sample_text):
        return True
    # Fall back to the study title only when it names a single tissue or
    # stage; a title listing several ('gills and mantle') does not say which
    # one this experiment is.
    return len(tissues_in(text(row['Study Title']))) == 1


def informative_title(row):
    title = text(row['Study Title'])
    return (any(t in title for t in LOCATION_TERMS + ENVIRONMENT_TERMS)
            or bool(PH_PATTERN.search(title)))


def rnaseq_suggested(row):
    return (bool(RNASEQ_PATTERN.search(text(row['Study Title'])))
            or text(row['Library Strategy']) == 'rna-seq'
            or text(row['Library Source']) == 'transcriptomic')


def main():
    df = pd.read_csv(INPUT)

    df['tissue_known'] = df.apply(tissue_known, axis=1)
    df['informative_title'] = df.apply(informative_title, axis=1)
    df['rnaseq_suggested'] = df.apply(rnaseq_suggested, axis=1)
    df['score'] = df[['tissue_known', 'informative_title',
                      'rnaseq_suggested']].sum(axis=1)

    # Shuffle first, then stable-sort by score: rows keep their random order
    # within each score tier, so the cut at N_SELECT is a seeded random draw.
    selected = (df.sample(frac=1, random_state=SEED)
                  .sort_values('score', ascending=False, kind='stable')
                  .head(N_SELECT))

    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    selected.to_csv(OUTPUT, index=False)

    print('Score distribution (all experiments):')
    print(df['score'].value_counts().sort_index(ascending=False).to_string())
    print('\nScore distribution (selected):')
    print(selected['score'].value_counts().sort_index(ascending=False).to_string())
    print(f'\nWrote {len(selected)} experiments to {OUTPUT.relative_to(REPO)}')


if __name__ == '__main__':
    main()
