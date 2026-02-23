"""
Signals — Combina todos os indicadores num sinal UP / DOWN / SKIP.
Cada indicador vota +1 (bullish), -1 (bearish), ou 0 (neutro).
O score agregado determina a decisão.
"""
from config import Config


class SignalGenerator:

    def __init__(self):
        self.threshold = Config.SIGNAL_THRESHOLD
        self.weights = {
            "rsi": 1.5,
            "macd": 1.5,
            "ema_crossover": 1.0,
            "bollinger": 1.0,
            "vwap": 1.0,
            "momentum": 1.2,
            "orderbook": 0.8,
        }

    def _score_rsi(self, rsi: float) -> float:
        """RSI: oversold = bullish, overbought = bearish."""
        if rsi < 30:
            return 1.0   # Strongly oversold → bullish
        elif rsi < 40:
            return 0.5   # Mildly oversold → slightly bullish
        elif rsi > 70:
            return -1.0  # Strongly overbought → bearish
        elif rsi > 60:
            return -0.5  # Mildly overbought → slightly bearish
        return 0.0        # Neutral

    def _score_macd(self, macd: dict) -> float:
        """MACD: histogram positivo e crescente = bullish."""
        if macd["bullish"]:
            return 1.0 if macd["histogram"] > 0 else 0.5
        else:
            return -1.0 if macd["histogram"] < 0 else -0.5

    def _score_ema(self, ema_crossover: bool) -> float:
        """EMA 9/21: crossover bullish ou bearish."""
        return 1.0 if ema_crossover else -1.0

    def _score_bollinger(self, price: float, bb: dict) -> float:
        """Bollinger: perto da lower = bullish, perto da upper = bearish."""
        if bb["upper"] == bb["lower"]:
            return 0.0
        position = (price - bb["lower"]) / (bb["upper"] - bb["lower"])
        if position < 0.2:
            return 1.0   # Perto da lower band
        elif position < 0.35:
            return 0.5
        elif position > 0.8:
            return -1.0  # Perto da upper band
        elif position > 0.65:
            return -0.5
        return 0.0

    def _score_vwap(self, price: float, vwap: float) -> float:
        """VWAP: preço acima = bullish, abaixo = bearish."""
        if vwap == 0:
            return 0.0
        diff_pct = ((price - vwap) / vwap) * 100
        if diff_pct > 0.1:
            return 1.0
        elif diff_pct > 0.02:
            return 0.5
        elif diff_pct < -0.1:
            return -1.0
        elif diff_pct < -0.02:
            return -0.5
        return 0.0

    def _score_momentum(self, momentum: dict) -> float:
        """Momentum: positivo = bullish, negativo = bearish."""
        pct = momentum["percent"]
        if pct > 0.15:
            return 1.0
        elif pct > 0.05:
            return 0.5
        elif pct < -0.15:
            return -1.0
        elif pct < -0.05:
            return -0.5
        return 0.0

    def _score_orderbook(self, ob: dict) -> float:
        """Orderbook: mais bids = bullish."""
        if ob is None:
            return 0.0
        ratio = ob["ratio"]
        if ratio > 0.6:
            return 1.0
        elif ratio > 0.55:
            return 0.5
        elif ratio < 0.4:
            return -1.0
        elif ratio < 0.45:
            return -0.5
        return 0.0

    def generate_signal(self, analysis: dict) -> dict:
        """
        Gera sinal final a partir da análise completa.
        Retorna: direction (UP/DOWN/SKIP), confidence, breakdown.
        """
        scores = {}

        # Calcular score de cada indicador
        scores["rsi"] = self._score_rsi(analysis["rsi"])
        scores["macd"] = self._score_macd(analysis["macd"])
        scores["ema_crossover"] = self._score_ema(analysis["ema_crossover"])
        scores["bollinger"] = self._score_bollinger(
            analysis["price"], analysis["bollinger"]
        )
        scores["vwap"] = self._score_vwap(analysis["price"], analysis["vwap"])
        scores["momentum"] = self._score_momentum(analysis["momentum"])
        scores["orderbook"] = self._score_orderbook(analysis.get("orderbook"))

        # Score ponderado
        weighted_sum = 0
        total_weight = 0
        for key, score in scores.items():
            weight = self.weights.get(key, 1.0)
            weighted_sum += score * weight
            total_weight += weight

        # Normalizar entre -1 e 1
        normalized_score = weighted_sum / total_weight if total_weight > 0 else 0

        # Contar votos
        bullish_votes = sum(1 for s in scores.values() if s > 0)
        bearish_votes = sum(1 for s in scores.values() if s < 0)
        neutral_votes = sum(1 for s in scores.values() if s == 0)

        # Determinar direção
        if normalized_score > self.threshold:
            direction = "UP"
        elif normalized_score < -self.threshold:
            direction = "DOWN"
        else:
            direction = "SKIP"

        confidence = abs(normalized_score)

        return {
            "direction": direction,
            "confidence": round(confidence, 4),
            "score": round(normalized_score, 4),
            "bullish_votes": bullish_votes,
            "bearish_votes": bearish_votes,
            "neutral_votes": neutral_votes,
            "breakdown": scores,
            "recommendation": self._build_recommendation(
                direction, confidence, scores
            ),
        }

    def _build_recommendation(
        self, direction: str, confidence: float, scores: dict
    ) -> str:
        """Gera explicação legível do sinal."""
        if direction == "SKIP":
            return (
                "⏸️  SKIP — Sinais mistos, sem edge claro. "
                "Esperar por melhor oportunidade."
            )

        emoji = "🟢" if direction == "UP" else "🔴"
        strength = "FORTE" if confidence > 0.6 else "MODERADO"

        reasons = []
        for indicator, score in scores.items():
            if direction == "UP" and score > 0:
                reasons.append(f"{indicator}(+)")
            elif direction == "DOWN" and score < 0:
                reasons.append(f"{indicator}(-)")

        reason_str = ", ".join(reasons) if reasons else "consensus"

        return (
            f"{emoji} {direction} — Sinal {strength} "
            f"(confiança: {confidence:.0%}). "
            f"Suportado por: {reason_str}"
        )
