"""
Configuração central do bot.
Carrega variáveis do .env e define defaults.
"""
import os
from dotenv import load_dotenv

load_dotenv()


class Config:
    # Trading mode
    LIVE_TRADING = os.getenv("LIVE_TRADING", "false").lower() == "true"

    # Polymarket credentials
    POLYMARKET_PRIVATE_KEY = os.getenv("POLYMARKET_PRIVATE_KEY", "")
    POLYMARKET_API_KEY = os.getenv("POLYMARKET_API_KEY", "")
    POLYMARKET_SECRET = os.getenv("POLYMARKET_SECRET", "")
    POLYMARKET_PASSPHRASE = os.getenv("POLYMARKET_PASSPHRASE", "")

    # Polymarket endpoints
    POLYMARKET_API_URL = "https://clob.polymarket.com"
    POLYMARKET_GAMMA_URL = "https://gamma-api.polymarket.com"

    # Risk management
    MAX_BET_SIZE = float(os.getenv("MAX_BET_SIZE", "2.0"))
    MAX_DAILY_LOSS = float(os.getenv("MAX_DAILY_LOSS", "20.0"))
    MAX_DAILY_TRADES = int(os.getenv("MAX_DAILY_TRADES", "50"))
    MIN_SIGNAL_CONFIDENCE = float(os.getenv("MIN_SIGNAL_CONFIDENCE", "0.6"))

    # Strategy
    SIGNAL_THRESHOLD = float(os.getenv("SIGNAL_THRESHOLD", "0.3"))

    # Timing
    CYCLE_INTERVAL_SECONDS = int(os.getenv("CYCLE_INTERVAL_SECONDS", "60"))

    # Binance
    BINANCE_API_URL = "https://api.binance.com/api/v3"
    BINANCE_SYMBOL = os.getenv("BINANCE_SYMBOL", "BTCUSDT")

    # Logging
    TRADES_LOG_FILE = "trades_log.json"

    @classmethod
    def validate(cls):
        """Valida configuração antes de arrancar."""
        if cls.LIVE_TRADING:
            if not cls.POLYMARKET_PRIVATE_KEY:
                raise ValueError(
                    "❌ LIVE_TRADING=true mas POLYMARKET_PRIVATE_KEY não definida!"
                )
            if not cls.POLYMARKET_API_KEY:
                raise ValueError(
                    "❌ LIVE_TRADING=true mas POLYMARKET_API_KEY não definida!"
                )
            print("⚠️  MODO LIVE TRADING ATIVADO — Dinheiro real em jogo!")
        else:
            print("📝 Modo PAPER TRADING — Simulação sem dinheiro real")
        return True
