from __future__ import annotations
import torch
from torch import nn


class TwoTower(nn.Module):
    def __init__(self, n_users: int, n_courses: int, dim: int = 64):
        super().__init__()
        self.user_tower = nn.Sequential(nn.Embedding(n_users, dim), nn.Flatten(), nn.Linear(dim, dim), nn.ReLU(), nn.LayerNorm(dim))
        self.course_tower = nn.Sequential(nn.Embedding(n_courses, dim), nn.Flatten(), nn.Linear(dim, dim), nn.ReLU(), nn.LayerNorm(dim))

    def forward(self, user_ids: torch.Tensor, course_ids: torch.Tensor) -> torch.Tensor:
        u = nn.functional.normalize(self.user_tower(user_ids), dim=-1)
        c = nn.functional.normalize(self.course_tower(course_ids), dim=-1)
        return (u * c).sum(dim=-1)
