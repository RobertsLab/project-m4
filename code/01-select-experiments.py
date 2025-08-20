
import pandas as pd
import numpy as np

# Load the SRA results CSV
df = pd.read_csv('data/sra_result.csv')

# Define filters
def is_informative(row):
    tissue_life_stage = str(row.get('Experiment Title', '') or '').lower()
    study_title = str(row.get('Study Title', '') or '').lower()
    library_strategy = str(row.get('Library Strategy', '') or '').lower()
    tissue_known = any(x in tissue_life_stage for x in ['gill', 'mantle', 'soft tissue', 'larva', 'embryo', 'juvenile', 'adult'])
    location_keywords = ['china', 'france', 'environment', 'infection', 'strain', 'gestinov', 'vibrio', 'growth']
    informative_title = any(x in study_title for x in location_keywords)
    rna_seq = 'rna-seq' in library_strategy or 'transcriptome' in library_strategy
    score = int(tissue_known) + int(informative_title) + int(rna_seq)
    return score

# Score all experiments
df['score'] = df.apply(is_informative, axis=1)

# Sort by score (highest first)
df_sorted = df.sort_values(by='score', ascending=False)

# Select up to 100 experiments, prioritizing those with highest score
selected_100 = df_sorted.head(100)

# If fewer than 100 with score > 0, fill with random others
if selected_100['score'].min() == 0:
    # If some are score 0, replace them with random from rest
    n_needed = 100 - (df_sorted['score'] > 0).sum()
    if n_needed > 0:
        random_fill = df_sorted[df_sorted['score'] == 0].sample(n=n_needed, random_state=42)
        selected_100 = pd.concat([df_sorted[df_sorted['score'] > 0], random_fill]).head(100)

# Save selected experiments
selected_100.drop(columns=['score']).to_csv('output/01/selected_experiments.csv', index=False)
