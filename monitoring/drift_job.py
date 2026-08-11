from __future__ import annotations
import argparse
import json
import pandas as pd
from evidently import Report
from evidently.presets import DataDriftPreset

parser = argparse.ArgumentParser()
parser.add_argument("--reference", required=True)
parser.add_argument("--current", required=True)
parser.add_argument("--output", default="artifacts/drift-report.json")
args = parser.parse_args()
reference = pd.read_parquet(args.reference)
current = pd.read_parquet(args.current)
report = Report([DataDriftPreset()])
result = report.run(current, reference)
with open(args.output, "w") as f:
    json.dump(result.dict(), f, default=str, indent=2)
print(args.output)
