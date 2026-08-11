from __future__ import annotations
import os
import random
import mlflow
import torch
from torch import nn
from models.two_tower import TwoTower


def synthetic_batch(size: int = 2048):
    users = torch.randint(0, 1000, (size, 1))
    positives = (users.squeeze(-1) % 100 + torch.randint(0, 8, (size,))) % 100
    negatives = torch.randint(0, 100, (size,))
    return users, positives[:, None], negatives[:, None]


mlflow.set_tracking_uri(os.getenv("MLFLOW_TRACKING_URI", "http://localhost:5000"))
mlflow.set_experiment("edurec-two-tower")
model = TwoTower(1000, 100)
opt = torch.optim.AdamW(model.parameters(), lr=1e-3)
loss_fn = nn.BCEWithLogitsLoss()

with mlflow.start_run():
    for epoch in range(5):
        users, pos, neg = synthetic_batch()
        scores = torch.cat([model(users, pos), model(users, neg)])
        labels = torch.cat([torch.ones(len(users)), torch.zeros(len(users))])
        loss = loss_fn(scores, labels)
        opt.zero_grad(); loss.backward(); opt.step()
        mlflow.log_metric("train_loss", float(loss), step=epoch)
    os.makedirs("artifacts", exist_ok=True)
    torch.save(model.state_dict(), "artifacts/two_tower.pt")
    mlflow.log_artifact("artifacts/two_tower.pt")
    mlflow.log_param("embedding_dim", 64)
