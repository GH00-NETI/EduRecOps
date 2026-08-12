from pathlib import Path
import json
import sys

root = Path(__file__).resolve().parents[1]
required = [
    "README.md", "LICENSE", "docker-compose.yml", "pyproject.toml",
    "packages/edurec_core/ranking.py", "apps/recommendation_api/main.py",
    "apps/feature_worker/worker.py", "apps/event_generator/generate.py",
    "docs/architecture.md", "docs/research-plan.md", "docs/evaluation.md",
    "infra/postgres/init.sql", ".github/workflows/ci.yml",
    "monitoring/requirements.txt", "ml/models/__init__.py",
]
missing = [path for path in required if not (root / path).exists()]
for path in root.rglob("*.json"):
    json.loads(path.read_text("utf-8"))
if missing:
    print("Missing required files:", *missing, sep="\n- ")
    sys.exit(1)
print(f"repository validation passed: {len(list(root.rglob('*')))} paths")
