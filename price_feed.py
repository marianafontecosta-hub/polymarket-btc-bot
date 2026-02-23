"""
Price Feed — Obtém preços BTC em tempo real da Binance.
Não precisa de API key para dados públicos.
"""
import time
import requests
import numpy as np
from config import Config


class PriceFeed:
    def __init__(self):
        self.symbol = Config.BINANCE_SYMBOL
        self.base_url = Config.BINANCE_API_URL
        self.price_history = []
        self.volume_history = []

    def get_current_price(self) -> float:
        """Obtém o preço atual do BTC."""
        try:
            url = f"{self.base_url}/ticker/price"
            resp = requests.get(url, params={"symbol": self.symbol}, timeout=5)
            resp.raise_for_status()
            price = float(resp.json()["price"])
            return price
        except Exception as e:
            print(f"⚠️  Erro ao obter preço: {e}")
            return self.price_history[-1] if self.price_history else 0.0

    def get_klines(self, interval: str = "1m", limit: int = 100) -> list:
        """
        Obtém candles históricas da Binance.
        interval: 1m, 3m, 5m, 15m, 1h, etc.
        """
        try:
            url = f"{self.base_url}/klines"
            params = {
                "symbol": self.symbol,
                "interval": interval,
                "limit": limit,
            }
            resp = requests.get(url, params=params, timeout=10)
            resp.raise_for_status()
            raw = resp.json()

            candles = []
            for k in raw:
                candles.append({
                    "timestamp": k[0],
                    "open": float(k[1]),
                    "high": float(k[2]),
                    "low": float(k[3]),
                    "close": float(k[4]),
                    "volume": float(k[5]),
                    "close_time": k[6],
                })
            return candles

        except Exception as e:
            print(f"⚠️  Erro ao obter klines: {e}")
            return []

    def get_orderbook(self, limit: int = 10) -> dict:
        """Obtém o order book para análise de liquidez."""
        try:
            url = f"{self.base_url}/depth"
            params = {"symbol": self.symbol, "limit": limit}
            resp = requests.get(url, params=params, timeout=5)
            resp.raise_for_status()
            data = resp.json()
            return {
                "bids": [(float(p), float(q)) for p, q in data["bids"]],
                "asks": [(float(p), float(q)) for p, q in data["asks"]],
                "bid_volume": sum(float(q) for _, q in data["bids"]),
                "ask_volume": sum(float(q) for _, q in data["asks"]),
            }
        except Exception as e:
            print(f"⚠️  Erro ao obter orderbook: {e}")
            return {"bids": [], "asks": [], "bid_volume": 0, "ask_volume": 0}

    def get_recent_trades(self, limit: int = 50) -> list:
        """Obtém trades recentes para análise de momentum."""
        try:
            url = f"{self.base_url}/trades"
            params = {"symbol": self.symbol, "limit": limit}
            resp = requests.get(url, params=params, timeout=5)
            resp.raise_for_status()
            return resp.json()
        except Exception as e:
            print(f"⚠️  Erro ao obter trades: {e}")
            return []

    def update_history(self):
        """Atualiza o histórico de preços interno."""
        price = self.get_current_price()
        if price > 0:
            self.price_history.append(price)
            # Manter últimos 500 pontos
            if len(self.price_history) > 500:
                self.price_history = self.price_history[-500:]
        return price
