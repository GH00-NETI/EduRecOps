from __future__ import annotations

import argparse
import json
from pathlib import Path

import pandas as pd
from evidently import Report
from evidently.presets import DataDriftPreset


def run_drift_report(reference_path: str, current_path: str, output_path: str) -> str:
    reference = pd.read_parquet(reference_path)
    current = pd.read_parquet(current_path)
    report = Report([DataDriftPreset()])
    result = report.run(current, reference)

    output = Path(output_path)
    output.parent.mkdir(parents=True, exist_ok=True)

    # Evidently APIs differ across majors; prefer json/dict helpers when present.
    if hasattr(result, "json"):
        payload = result.json()
        if isinstance(payload, str):
            output.write_text(payload, encoding="utf-8")
        else:
            output.write_text(json.dumps(payload, default=str, indent=2), encoding="utf-8")
    elif hasattr(result, "dict"):
        output.write_text(json.dumps(result.dict(), default=str, indent=2), encoding="utf-8")
    else:
        output.write_text(json.dumps({"result": str(result)}, indent=2), encoding="utf-8")
    return str(output)


def main() -> None:
    parser = argparse.ArgumentParser(description="Run an Evidently data-drift report")
    parser.add_argument("--reference", required=True)
    parser.add_argument("--current", required=True)
    parser.add_argument("--output", default="artifacts/drift-report.json")
    args = parser.parse_args()
    path = run_drift_report(args.reference, args.current, args.output)
    print(path)


if __name__ == "__main__":
    main()
