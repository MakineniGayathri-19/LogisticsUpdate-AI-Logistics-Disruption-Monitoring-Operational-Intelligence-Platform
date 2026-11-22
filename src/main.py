"""Entry point for LogisticsUpdate AI.
Orchestrates data collection, processing, historical storage, and brief generation.
"""
import os
import pandas as pd

from .config import LOG_DIR
from .data_collection import run as collect
from .processing import clean as process
from .historical import save_event
from .brief_generator import generate_brief

def ensure_log_dir():
    os.makedirs(LOG_DIR, exist_ok=True)

def main():
    ensure_log_dir()
    # Step 1: collect raw data
    print("=== Collecting raw logistics updates ===")
    collect()

    # Step 2: process raw HTML into structured CSV
    print("=== Processing raw data ===")
    csv_path = process()

    # Step 3: load processed records and handle each event
    df = pd.read_csv(csv_path)
    if df.empty:
        print("No disruption records found after processing.")
        return

    print(f"=== Generating briefs for {len(df)} events ===")
    for _, row in df.iterrows():
        event = row.to_dict()
        # Save to historical store first
        save_event(event)
        # Generate operational brief using LLM
        brief = generate_brief(event)
        print("\n--- Operational Brief ---")
        print(brief)
        print("--- End Brief ---\n")

if __name__ == "__main__":
    main()
