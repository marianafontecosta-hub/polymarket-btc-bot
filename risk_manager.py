"""
Risk Manager — Gestão de risco e limites de trading.
Protege contra perdas excessivas.
"""
import json
import os
from datetime import datetime, date
from config import Config


class RiskManager:

    def __init__(self):
        self.max_bet = Config.MAX_BET_SIZE
        self.max_daily_loss = Config.MAX_DAILY_LOSS
        self.max_daily_trades = Config.MAX_DAILY_TRADES
        self.min_confidence = Config.MIN_SIGNAL_CONFIDENCE
        self.log_file = Config.TRADES_LOG_FILE

        # Estado diário
        self.daily_trades = 0
        self.daily_pnl = 0.0
        self.today = date.today()
        self.trades_history = []

        self._load_history()

    def _load_history(self):
        """Carrega histórico de trades."""
        if os.path.exists(self.log_file):
            try:
                with open(self.log_file, "r") as f:
                    self.trades_history = json.load(f)
                # Contar trades de hoje
                today_str = self.today.isoformat()
                today_trades = [
                    t for t in self.trades_history
                    if t.get("date", "").startswith(today_str)
                ]
                self.daily_trades = len(today_trades)
                self.daily_pnl = sum(t.get("pnl", 0) for t in today_trades)
            except (json.JSONDecodeError, Exception):
                self.trades_history = []

    def _save_history(self):
        """Guarda histórico de trades."""
        try:
            with open(self.log_file, "w") as f:
                json.dump(self.trades_history, f, indent=2, default=str)
        except Exception as e:
            print(f"⚠️  Erro ao guardar histórico: {e}")

    def _reset_daily(self):
        """Reset contadores diários à meia-noite."""
        if date.today() != self.today:
            self.today = date.today()
            self.daily_trades = 0
            self.daily_pnl = 0.0

    def can_trade(self, confidence: float) -> dict:
        """
        Verifica se é seguro abrir nova trade.
        Retorna dict com allowed (bool) e reason.
        """
        self._reset_daily()

        # Check 1: Confiança mínima
        if confidence < self.min_confidence:
            return {
                "allowed": False,
                "reason": f"Confiança {confidence:.0%} abaixo do mínimo "
                          f"({self.min_confidence:.0%})",
            }

        # Check 2: Limite diário de trades
        if self.daily_trades >= self.max_daily_trades:
            return {
                "allowed": False,
                "reason": f"Limite diário atingido ({self.max_daily_trades} trades)",
            }

        # Check 3: Perda máxima diária
        if self.daily_pnl <= -self.max_daily_loss:
            return {
                "allowed": False,
                "reason": f"Perda diária máxima atingida "
                          f"(${abs(self.daily_pnl):.2f} / ${self.max_daily_loss:.2f})",
            }

        return {"allowed": True, "reason": "OK"}

    def calculate_bet_size(self, confidence: float) -> float:
        """
        Calcula tamanho da aposta baseado na confiança.
        Kelly Criterion simplificado.
        """
        # Base: max_bet * confidence
        # Mas nunca mais que max_bet
        size = self.max_bet * min(confidence, 1.0)

        # Reduzir se já perdemos hoje
        if self.daily_pnl < 0:
            loss_ratio = abs(self.daily_pnl) / self.max_daily_loss
            reduction = max(0.3, 1.0 - loss_ratio)
            size *= reduction

        return round(max(0.5, min(size, self.max_bet)), 2)

    def record_trade(self, trade: dict):
        """Regista uma trade no histórico."""
        trade["date"] = datetime.now().isoformat()
        trade["trade_number"] = self.daily_trades + 1

        self.trades_history.append(trade)
        self.daily_trades += 1
        self.daily_pnl += trade.get("pnl", 0)

        self._save_history()

    def get_stats(self) -> dict:
        """Retorna estatísticas de performance."""
        if not self.trades_history:
            return {
                "total_trades": 0,
                "win_rate": 0,
                "total_pnl": 0,
                "avg_pnl": 0,
                "best_trade": 0,
                "worst_trade": 0,
                "today_trades": 0,
                "today_pnl": 0,
            }

        pnls = [t.get("pnl", 0) for t in self.trades_history]
        wins = [p for p in pnls if p > 0]

        return {
            "total_trades": len(self.trades_history),
            "win_rate": round(len(wins) / len(pnls) * 100, 1) if pnls else 0,
            "total_pnl": round(sum(pnls), 2),
            "avg_pnl": round(sum(pnls) / len(pnls), 2) if pnls else 0,
            "best_trade": round(max(pnls), 2) if pnls else 0,
            "worst_trade": round(min(pnls), 2) if pnls else 0,
            "today_trades": self.daily_trades,
            "today_pnl": round(self.daily_pnl, 2),
        }
