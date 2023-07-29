from __future__ import annotations

from dataclasses import dataclass


@dataclass
class User:
    user_principal_name: str
    display_name: str
    distinguished_name: str
