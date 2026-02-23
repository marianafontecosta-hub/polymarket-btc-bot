"""
Paper Trader — Simula trades sem dinheiro real.
Regista tudo como se fosse real para avaliar performance.
"""
import time
import random
from datetime import datetime


class PaperTrader:

    def __init__(self, starting_balance: float = 100.0):
        self.balance = starting_balance
        self.starting_balance = starting_balance
        self.open_positions = []
        self.closed_trades = []

    def place_bet(
        self,
        direction: str,
        amount: float,
        market_price: float,
        btc_price: float,
        market_info: dict = None,
    ) -> dict:
        """
        Simula uma aposta.
        direction: "UP" ou "DOWN"
        amount: quanto apostar em USDC
        market_price: preço atual da share (ex: 0.52)
        """
        if amount > self.balance:
            return {
                "success": False,
                "reason": f"Saldo insuficiente: ${self.balance:.2f} < ${amount:.2f}",
            }

        shares = amount / market_price
        self.balance -= amount

        position = {
            "id": f"paper_{int(time.time())}_{random.randint(1000,9999)}",
            "direction": direction,
            "amount": amount,
            "shares": round(shares, 4),
            "entry_price": market_price,
            "btc_price_at_entry": btc_price,
            "timestamp": datetime.now().isoformat(),
            "market_question": market_info.get("question", "") if market_info else "",
            "status": "open",
        }

        self.open_positions.append(position)

        return {
            "success": True,
            "position": position,
            "remaining_balance": round(self.balance, 2),
        }

    def resolve_position(self, position_id: str, won: bool) -> dict:
        """
        Resolve uma posição.
        won=True → recebe $1 por share
        won=False → perde tudo
        """
        position = None
        for i, pos in enumerate(self.open_positions):
            if pos["id"] == position_id:
                position = self.open_positions.pop(i)
                break

        if not position:
            return {"success": False, "reason": "Posição não encontrada"}

        if won:
            payout = position["shares"] * 1.0  # Cada share paga $1
            pnl = payout - position["amount"]
            self.balance += payout
        else:
            payout = 0
            pnl = -position["amount"]

        position["status"] = "closed"
        position["won"] = won
        position["payout"] = round(payout, 2)
        position["pnl"] = round(pnl, 2)
        position["closed_at"] = datetime.now().isoformat()

        self.closed_trades.append(position)

        return {
            "success": True,
            "won": won,
            "pnl": round(pnl, 2),
            "payout": round(payout, 2),
            "balance": round(self.balance, 2),
        }

    def simulate_resolution(
        self, position_id: str, btc_price_at_close: float
    ) -> dict:
        """
        Resolve automaticamente baseado no preço do BTC.
        Se direction=UP e preço subiu → won
        Se direction=DOWN e preço desceu → won
        """
        position = None
        for pos in self.open_positions:
            if pos["id"] == position_id:
                position = pos
                break

        if not position:
            return {"success": False, "reason": "Posição não encontrada"}

        btc_went_up = btc_price_at_close >= position["btc_price_at_entry"]

        if position["direction"] == "UP":
            won = btc_went_up
        else:
            won = not btc_went_up

        return self.resolve_position(position_id, won)

    def get_summary(self) -> dict:
        """Retorna resumo do paper trading."""
        total_trades = len(self.closed_trades)
        wins = [t for t in self.closed_trades if t.get("won", False)]
        total_pnl = sum(t.get("pnl", 0) for t in self.closed_trades)

        return {
            "starting_balance": self.starting_balance,
            "current_balance": round(self.balance, 2),
            "total_pnl": round(total_pnl, 2),
            "total_pnl_pct": round(
                (total_pnl / self.starting_balance) * 100, 2
            ) if self.starting_balance > 0 else 0,
            "total_trades": total_trades,
            "wins": len(wins),
            "losses": total_trades - len(wins),
            "win_rate": round(
                len(wins) / total_trades * 100, 1
            ) if total_trades > 0 else 0,
            "open_positions": len(self.open_positions),
        }
