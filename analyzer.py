"""
Analyzer — Motor de análise técnica.
Calcula RSI, MACD, EMA, Bollinger Bands, VWAP, e Momentum.
"""
import numpy as np
import pandas as pd


class TechnicalAnalyzer:

    @staticmethod
    def calculate_rsi(closes: list, period: int = 14) -> float:
        """
        Relative Strength Index.
        < 30 = oversold (bullish signal)
        > 70 = overbought (bearish signal)
        """
        if len(closes) < period + 1:
            return 50.0  # neutral default

        prices = np.array(closes)
        deltas = np.diff(prices)
        gains = np.where(deltas > 0, deltas, 0)
        losses = np.where(deltas < 0, -deltas, 0)

        avg_gain = np.mean(gains[-period:])
        avg_loss = np.mean(losses[-period:])

        if avg_loss == 0:
            return 100.0

        rs = avg_gain / avg_loss
        rsi = 100 - (100 / (1 + rs))
        return round(rsi, 2)

    @staticmethod
    def calculate_macd(
        closes: list,
        fast: int = 12,
        slow: int = 26,
        signal_period: int = 9,
    ) -> dict:
        """
        MACD — Moving Average Convergence Divergence.
        Retorna macd_line, signal_line, e histogram.
        """
        if len(closes) < slow + signal_period:
            return {"macd": 0, "signal": 0, "histogram": 0, "bullish": False}

        prices = pd.Series(closes)
        ema_fast = prices.ewm(span=fast, adjust=False).mean()
        ema_slow = prices.ewm(span=slow, adjust=False).mean()
        macd_line = ema_fast - ema_slow
        signal_line = macd_line.ewm(span=signal_period, adjust=False).mean()
        histogram = macd_line - signal_line

        return {
            "macd": round(macd_line.iloc[-1], 4),
            "signal": round(signal_line.iloc[-1], 4),
            "histogram": round(histogram.iloc[-1], 4),
            "bullish": histogram.iloc[-1] > 0
            and histogram.iloc[-1] > histogram.iloc[-2],
        }

    @staticmethod
    def calculate_ema(closes: list, period: int) -> float:
        """Exponential Moving Average."""
        if len(closes) < period:
            return closes[-1] if closes else 0
        prices = pd.Series(closes)
        ema = prices.ewm(span=period, adjust=False).mean()
        return round(ema.iloc[-1], 2)

    @staticmethod
    def calculate_bollinger_bands(
        closes: list, period: int = 20, std_dev: float = 2.0
    ) -> dict:
        """
        Bollinger Bands.
        Preço perto da lower band = bullish
        Preço perto da upper band = bearish
        """
        if len(closes) < period:
            price = closes[-1] if closes else 0
            return {"upper": price, "middle": price, "lower": price, "width": 0}

        prices = pd.Series(closes)
        middle = prices.rolling(window=period).mean().iloc[-1]
        std = prices.rolling(window=period).std().iloc[-1]
        upper = middle + (std_dev * std)
        lower = middle - (std_dev * std)
        width = (upper - lower) / middle if middle > 0 else 0

        return {
            "upper": round(upper, 2),
            "middle": round(middle, 2),
            "lower": round(lower, 2),
            "width": round(width, 6),
        }

    @staticmethod
    def calculate_vwap(candles: list) -> float:
        """
        Volume Weighted Average Price.
        Preço acima do VWAP = bullish
        Preço abaixo do VWAP = bearish
        """
        if not candles:
            return 0.0

        total_volume = 0
        total_pv = 0

        for c in candles:
            typical_price = (c["high"] + c["low"] + c["close"]) / 3
            volume = c["volume"]
            total_pv += typical_price * volume
            total_volume += volume

        if total_volume == 0:
            return 0.0

        return round(total_pv / total_volume, 2)

    @staticmethod
    def calculate_momentum(closes: list, period: int = 10) -> dict:
        """
        Momentum — taxa de variação do preço.
        Positivo = bullish, Negativo = bearish.
        """
        if len(closes) < period + 1:
            return {"value": 0, "percent": 0, "bullish": False}

        current = closes[-1]
        past = closes[-period - 1]
        momentum = current - past
        pct = ((current - past) / past) * 100 if past != 0 else 0

        return {
            "value": round(momentum, 2),
            "percent": round(pct, 4),
            "bullish": momentum > 0,
        }

    @staticmethod
    def calculate_orderbook_imbalance(orderbook: dict) -> dict:
        """
        Analisa o desequilíbrio do order book.
        Mais bids que asks = pressão compradora (bullish).
        """
        bid_vol = orderbook.get("bid_volume", 0)
        ask_vol = orderbook.get("ask_volume", 0)
        total = bid_vol + ask_vol

        if total == 0:
            return {"ratio": 0.5, "bullish": False}

        ratio = bid_vol / total
        return {
            "ratio": round(ratio, 4),
            "bullish": ratio > 0.55,
            "bid_volume": round(bid_vol, 4),
            "ask_volume": round(ask_vol, 4),
        }

    def full_analysis(self, candles: list, orderbook: dict = None) -> dict:
        """
        Corre TODOS os indicadores e retorna análise completa.
        """
        closes = [c["close"] for c in candles]
        current_price = closes[-1] if closes else 0

        rsi = self.calculate_rsi(closes)
        macd = self.calculate_macd(closes)
        ema_9 = self.calculate_ema(closes, 9)
        ema_21 = self.calculate_ema(closes, 21)
        bb = self.calculate_bollinger_bands(closes)
        vwap = self.calculate_vwap(candles)
        momentum = self.calculate_momentum(closes)

        ob_analysis = None
        if orderbook:
            ob_analysis = self.calculate_orderbook_imbalance(orderbook)

        return {
            "price": current_price,
            "rsi": rsi,
            "macd": macd,
            "ema_9": ema_9,
            "ema_21": ema_21,
            "ema_crossover": ema_9 > ema_21,
            "bollinger": bb,
            "vwap": vwap,
            "price_vs_vwap": "above" if current_price > vwap else "below",
            "momentum": momentum,
            "orderbook": ob_analysis,
        }
