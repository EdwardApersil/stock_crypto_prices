from __future__ import annotations
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum, auto

from matplotlib.axis import Ticker


class AssetType(Enum):
    STOCK = auto()
    CRYPTO = auto()

@dataclass(frozen=True)
class Tracker:

    symbol: str
    asset_type: AssetType
    display_name: str

    def __post_init__(self) -> None:
        if not self.display_name:
            object.__setattr__(self, "display_name", self.symbol)

    @property
    def key(self) -> str:
        return self.symbol.lower()

@dataclass(frozen=True)
class PriceSnapshot:
    timestamp: datetime = field(default_factory=datetime.now)
    price: float
    ticker: Ticker
    changes: float
    change_pct: float

    @property
    def is_positive(self) -> bool:
        return self.change_pct >= 0

    @property
    def direction_symbol(self) -> str:
        return "▲" if self.is_positive else "▼"

