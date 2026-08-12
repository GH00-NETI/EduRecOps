from __future__ import annotations

import os
import sys
from pathlib import Path

import mlflow
import torch
from torch import nn

# Allow `python ml/train.py` and `python -m ml.train` style invocation.
ML_ROOT = Path(__file__).resolve().parent
if str(ML_ROOT) not in sys.path:
    sys.path.insert(0, str(ML_ROOT))

from models.two_tower import TwoTower  # noqa: E402


def synthetic_batch(size: int = 2048):
    users = torch.randint(0, 1000, (size, 1))
    positives = (users.squeeze(-1) % 100 + torch.randint(0, 8, (size,))) % 100
    negatives = torch.randint(0, 100, (size,))
    return users, positives[:, None], negatives[:, None]


def train(epochs: int = 5, embedding_dim: int = 64) -> Path:
    mlflow.set_tracking_uri(os.getenv("MLFLOW_TRACKING_URI", "http://localhost:5000"))
    mlflow.set_experiment("edurec-two-tower")
    model = TwoTower(1000, 100, dim=embedding_dim)
    opt = torch.optim.AdamW(model.parameters(), lr=1e-3)
    loss_fn = nn.BCEWithLogitsLoss()

    artifact_dir = Path("artifacts")
    artifact_dir.mkdir(exist_ok=True)
    artifact_path = artifact_dir / "two_tower.pt"

    with mlflow.start_run():
        mlflow.log_param("embedding_dim", embedding_dim)
        mlflow.log_param("epochs", epochs)
        for epoch in range(epochs):
            users, pos, neg = synthetic_batch()
            scores = torch.cat([model(users, pos), model(users, neg)])
            labels = torch.cat([torch.ones(len(users)), torch.zeros(len(users))])
            loss = loss_fn(scores, labels)
            opt.zero_grad()
            loss.backward()
            opt.step()
            mlflow.log_metric("train_loss", float(loss), step=epoch)
        torch.save(model.state_dict(), artifact_path)
        mlflow.log_artifact(str(artifact_path))
    return artifact_path


def main() -> None:
    path = train(epochs=int(os.getenv("TRAIN_EPOCHS", "5")))
    print(f"wrote {path}", flush=True)


if __name__ == "__main__":
    main()
