#!/usr/bin/env python3
"""
Combine all Adj_Matrix_{SEX}_ICD_age_{AGE}.csv files into a single CSV.
SEX: Male, Female
AGE: 1-8
"""

import pandas as pd
from pathlib import Path

# Paths relative to this script
SCRIPT_DIR = Path(__file__).resolve().parent
MATRICES_DIR = SCRIPT_DIR / "3.AdjacencyMatrices"
OUTPUT_PATH = SCRIPT_DIR / "combined_adjacency_ICD.csv"

SEX_VALUES = ("Male", "Female")
AGE_VALUES = range(1, 9)


def main() -> None:
    frames = []

    for sex in SEX_VALUES:
        for age in AGE_VALUES:
            filename = f"Adj_Matrix_{sex}_ICD_age_{age}.csv"
            filepath = MATRICES_DIR / filename

            if not filepath.exists():
                print(f"Warning: skipping missing file {filepath}")
                continue

            df = pd.read_csv(
                filepath,
                sep=r"\s+",
                header=None,
                dtype=float,
            )
            df = pd.concat(
                [
                    pd.DataFrame({"sex": [sex] * len(df), "age": [age] * len(df)}),
                    df,
                ],
                axis=1,
            )
            frames.append(df)
            print(f"Loaded {filename}: {len(df)} rows")

    if not frames:
        print("No files found. Exiting.")
        return

    combined = pd.concat(frames, ignore_index=True)
    combined.to_csv(OUTPUT_PATH, index=False)
    print(f"\nWrote {combined.shape[0]} rows to {OUTPUT_PATH}")


if __name__ == "__main__":
    main()
