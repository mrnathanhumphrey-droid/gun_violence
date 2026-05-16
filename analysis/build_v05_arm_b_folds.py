"""v0.5 Arm B: cell-stratified 5-fold random split of v0.4 county-units.

Per pre-reg: seed = 20260602, stratified by cell_id to preserve cell representation
across folds. Saves fold_assignments.csv (immutable per pre-reg constraint #1).
"""
import pathlib
import numpy as np
import pandas as pd

ROOT = pathlib.Path(r"D:/Gun Violence")
units = pd.read_parquet(ROOT / "analysis/production_v0_1/design_units.parquet")
print(f"Loaded v0.1 design_units: {len(units)} county-units across {units['cell_id'].nunique()} cells")
print(f"  cell distribution:\n{units.groupby('cell_id').size().to_string()}")

SEED = 20260602
K = 5
rng = np.random.default_rng(SEED)

assignments = []
for cell, sub in units.groupby("cell_id"):
    n = len(sub)
    # Random permutation, then assign to folds in round-robin
    perm = rng.permutation(n)
    fold = np.empty(n, dtype=int)
    for i, p in enumerate(perm):
        fold[p] = (i % K) + 1
    sub_out = sub.copy()
    sub_out["fold"] = fold
    assignments.append(sub_out[["state","county","cell_id","fold"]])

fold_df = pd.concat(assignments, ignore_index=True)
out = ROOT / "analysis/production_v0_5/fold_assignments.csv"
out.parent.mkdir(parents=True, exist_ok=True)
fold_df.to_csv(out, index=False)
print(f"\nWrote {out}")
print(f"\nFold sizes overall: {fold_df.groupby('fold').size().to_dict()}")
print(f"\nPer-cell fold counts:")
print(fold_df.groupby(['cell_id','fold']).size().unstack(fill_value=0).to_string())
