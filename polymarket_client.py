"""
Polymarket Client — Interação com a API do Polymarket.
Busca mercados de 15 minutos BTC e coloca ordens.
"""
import time
import requests
from config import Config


class PolymarketClient:

    def __init__(self):
        self.gamma_url = Config.POLYMARKET_GAMMA_URL
        self.clob_url = Config.POLYMARKET_API_URL
        self.live = Config.LIVE_TRADING
        self._clob_client = None

        if self.live:
            self._init_clob_client()

    def _init_clob_client(self):
        """Inicializa o cliente CLOB para trading real."""
        try:
            from py_clob_client.client import ClobClient
            from py_clob_client.clob_types import ApiCreds

            creds = ApiCreds(
                api_key=Config.POLYMARKET_API_KEY,
                api_secret=Config.POLYMARKET_SECRET,
                api_passphrase=Config.POLYMARKET_PASSPHRASE,
            )
            self._clob_client = ClobClient(
                self.clob_url,
                key=Config.POLYMARKET_PRIVATE_KEY,
                chain_id=137,  # Polygon
                creds=creds,
            )
            print("✅ Cliente CLOB inicializado para trading real")
        except ImportError:
            print("⚠️  py-clob-client não instalado. Só paper trading disponível.")
            self.live = False
        except Exception as e:
            print(f"❌ Erro ao inicializar CLOB client: {e}")
            self.live = False

    def get_active_btc_15m_market(self) -> dict | None:
        """
        Encontra o mercado ativo de BTC Up/Down 15 minutos.
        Retorna info do mercado ou None.
        """
        try:
            url = f"{self.gamma_url}/markets"
            params = {
                "tag": "crypto",
                "active": "true",
                "closed": "false",
                "limit": 50,
            }
            resp = requests.get(url, params=params, timeout=10)
            resp.raise_for_status()
            markets = resp.json()

            # Filtrar para BTC Up/Down 15 minutos
            for market in markets:
                question = market.get("question", "").lower()
                if (
                    "bitcoin" in question
                    and ("up or down" in question or "up/down" in question)
                    and "15" in question
                ):
                    # Verificar que ainda não resolveu
                    if not market.get("closed", False):
                        return self._parse_market(market)

            # Fallback: procurar pelo slug
            for market in markets:
                slug = market.get("slug", "")
                if "btc-updown-15m" in slug and not market.get("closed", False):
                    return self._parse_market(market)

            print("⚠️  Nenhum mercado BTC 15m ativo encontrado")
            return None

        except Exception as e:
            print(f"❌ Erro ao buscar mercados: {e}")
            return None

    def _parse_market(self, market: dict) -> dict:
        """Extrai informação relevante do mercado."""
        tokens = market.get("tokens", [])
        up_token = None
        down_token = None

        for token in tokens:
            outcome = token.get("outcome", "").lower()
            if outcome in ("up", "yes"):
                up_token = token
            elif outcome in ("down", "no"):
                down_token = token

        up_price = float(up_token["price"]) if up_token else 0.5
        down_price = float(down_token["price"]) if down_token else 0.5

        return {
            "id": market.get("condition_id", ""),
            "question": market.get("question", ""),
            "slug": market.get("slug", ""),
            "end_date": market.get("end_date_iso", ""),
            "up_token_id": up_token.get("token_id", "") if up_token else "",
            "down_token_id": down_token.get("token_id", "") if down_token else "",
            "up_price": up_price,
            "down_price": down_price,
            "up_probability": round(up_price * 100, 1),
            "down_probability": round(down_price * 100, 1),
            "volume": market.get("volume", 0),
            "liquidity": market.get("liquidity", 0),
        }

    def place_order(self, token_id: str, side: str, amount: float, price: float) -> dict:
        """
        Coloca uma ordem no Polymarket.
        side: "BUY" ou "SELL"
        amount: em USDC
        price: preço por share (0.01 a 0.99)
        """
        if not self.live:
            return {
                "success": False,
                "reason": "Paper trading mode — ordem simulada",
                "simulated": True,
            }

        if not self._clob_client:
            return {"success": False, "reason": "CLOB client não inicializado"}

        try:
            from py_clob_client.clob_types import OrderArgs
            from py_clob_client.order_builder.constants import BUY, SELL

            order_side = BUY if side.upper() == "BUY" else SELL

            order_args = OrderArgs(
                price=price,
                size=amount / price,  # Converter USDC em shares
                side=order_side,
                token_id=token_id,
            )

            signed_order = self._clob_client.create_order(order_args)
            result = self._clob_client.post_order(signed_order)

            return {
                "success": True,
                "order_id": result.get("orderID", ""),
                "details": result,
            }

        except Exception as e:
            return {"success": False, "reason": str(e)}

    def get_balance(self) -> float:
        """Obtém o saldo USDC disponível."""
        if not self.live or not self._clob_client:
            return 0.0
        try:
            # Isto depende da implementação específica
            return 0.0  # placeholder
        except Exception:
            return 0.0
