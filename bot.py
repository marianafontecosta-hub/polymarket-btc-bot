"""
🤖 Polymarket BTC 15-Minute Trading Bot
========================================
Analisa indicadores técnicos do Bitcoin e gera sinais UP/DOWN
para os mercados de 15 minutos do Polymarket.

Modo padrão: PAPER TRADING (simulação sem dinheiro real)
"""
import os
import sys
import time
from datetime import datetime

from colorama import init, Fore, Style
from tabulate import tabulate

from config import Config
from price_feed import PriceFeed
from analyzer import TechnicalAnalyzer
from signals import SignalGenerator
from polymarket_client import PolymarketClient
from risk_manager import RiskManager
from paper_trader import PaperTrader

init(autoreset=True)  # Colorama


def clear_screen():
    os.system("cls" if os.name == "nt" else "clear")


def print_banner():
    print(Fore.CYAN + """
╔══════════════════════════════════════════════════╗
║  🤖 POLYMARKET BTC 15-MIN TRADING BOT           ║
║  Análise técnica + Sinais automáticos            ║
╚══════════════════════════════════════════════════╝
""" + Style.RESET_ALL)


def print_analysis(analysis: dict, signal: dict, market: dict = None):
    """Imprime a análise de forma legível."""

    # Preço atual
    print(f"\n{'='*50}")
    print(
        f"  💰 BTC: {Fore.WHITE}${analysis['price']:,.2f}{Style.RESET_ALL}"
        f"  |  ⏰ {datetime.now().strftime('%H:%M:%S')}"
    )
    print(f"{'='*50}")

    # Mercado Polymarket
    if market:
        print(f"\n  📊 Mercado: {market['question'][:60]}")
        print(
            f"  UP: {Fore.GREEN}${market['up_price']:.2f}{Style.RESET_ALL}"
            f"  ({market['up_probability']}%)"
            f"  |  DOWN: {Fore.RED}${market['down_price']:.2f}{Style.RESET_ALL}"
            f"  ({market['down_probability']}%)"
        )

    # Tabela de indicadores
    indicators = [
        [
            "RSI (14)",
            f"{analysis['rsi']:.1f}",
            _rsi_label(analysis["rsi"]),
            _score_color(signal["breakdown"]["rsi"]),
        ],
        [
            "MACD",
            f"{analysis['macd']['histogram']:.4f}",
            "Bullish ↑" if analysis["macd"]["bullish"] else "Bearish ↓",
            _score_color(signal["breakdown"]["macd"]),
        ],
        [
            "EMA 9/21",
            f"{analysis['ema_9']:.0f} / {analysis['ema_21']:.0f}",
            "Cross ↑" if analysis["ema_crossover"] else "Cross ↓",
            _score_color(signal["breakdown"]["ema_crossover"]),
        ],
        [
            "Bollinger",
            f"L:{analysis['bollinger']['lower']:.0f} "
            f"U:{analysis['bollinger']['upper']:.0f}",
            _bb_position(analysis["price"], analysis["bollinger"]),
            _score_color(signal["breakdown"]["bollinger"]),
        ],
        [
            "VWAP",
            f"${analysis['vwap']:,.2f}",
            f"Price {analysis['price_vs_vwap']}",
            _score_color(signal["breakdown"]["vwap"]),
        ],
        [
            "Momentum",
            f"{analysis['momentum']['percent']:.3f}%",
            "Bullish ↑" if analysis["momentum"]["bullish"] else "Bearish ↓",
            _score_color(signal["breakdown"]["momentum"]),
        ],
    ]

    if analysis.get("orderbook"):
        ob = analysis["orderbook"]
        indicators.append([
            "Orderbook",
            f"Bid/Ask: {ob['ratio']:.2f}",
            "Buyers ↑" if ob["bullish"] else "Sellers ↓",
            _score_color(signal["breakdown"]["orderbook"]),
        ])

    print(f"\n{tabulate(indicators, headers=['Indicador', 'Valor', 'Leitura', 'Score'], tablefmt='rounded_grid')}")

    # Sinal final
    print(f"\n  {'='*46}")
    direction = signal["direction"]
    if direction == "UP":
        color = Fore.GREEN
        emoji = "🟢"
    elif direction == "DOWN":
        color = Fore.RED
        emoji = "🔴"
    else:
        color = Fore.YELLOW
        emoji = "⏸️"

    print(
        f"  {emoji} SINAL: {color}{direction}{Style.RESET_ALL}"
        f"  |  Confiança: {signal['confidence']:.0%}"
        f"  |  Score: {signal['score']:.3f}"
    )
    print(
        f"  Votos: 🟢{signal['bullish_votes']} "
        f"🔴{signal['bearish_votes']} "
        f"⚪{signal['neutral_votes']}"
    )
    print(f"\n  {signal['recommendation']}")
    print(f"  {'='*46}")


def _rsi_label(rsi: float) -> str:
    if rsi < 30:
        return f"{Fore.GREEN}Oversold ↑{Style.RESET_ALL}"
    elif rsi > 70:
        return f"{Fore.RED}Overbought ↓{Style.RESET_ALL}"
    return "Neutral"


def _bb_position(price: float, bb: dict) -> str:
    if bb["upper"] == bb["lower"]:
        return "N/A"
    pos = (price - bb["lower"]) / (bb["upper"] - bb["lower"])
    if pos < 0.2:
        return f"{Fore.GREEN}Near Lower ↑{Style.RESET_ALL}"
    elif pos > 0.8:
        return f"{Fore.RED}Near Upper ↓{Style.RESET_ALL}"
    return "Middle"


def _score_color(score: float) -> str:
    if score > 0:
        return f"{Fore.GREEN}+{score:.1f}{Style.RESET_ALL}"
    elif score < 0:
        return f"{Fore.RED}{score:.1f}{Style.RESET_ALL}"
    return f"{Fore.YELLOW} 0.0{Style.RESET_ALL}"


def print_paper_summary(paper: PaperTrader):
    """Imprime resumo do paper trading."""
    summary = paper.get_summary()
    pnl_color = Fore.GREEN if summary["total_pnl"] >= 0 else Fore.RED

    print(f"\n{Fore.CYAN}📋 PAPER TRADING SUMMARY{Style.RESET_ALL}")
    print(f"  Saldo: ${summary['current_balance']:.2f} "
          f"({pnl_color}{summary['total_pnl']:+.2f}{Style.RESET_ALL})")
    print(f"  Trades: {summary['total_trades']} "
          f"(W:{summary['wins']} L:{summary['losses']})")
    if summary["total_trades"] > 0:
        print(f"  Win Rate: {summary['win_rate']:.1f}%")
    if summary["open_positions"] > 0:
        print(f"  Posições abertas: {summary['open_positions']}")


def main():
    """Loop principal do bot."""
    clear_screen()
    print_banner()

    # Validar configuração
    try:
        Config.validate()
    except ValueError as e:
        print(f"{Fore.RED}{e}{Style.RESET_ALL}")
        sys.exit(1)

    # Inicializar componentes
    price_feed = PriceFeed()
    analyzer = TechnicalAnalyzer()
    signal_gen = SignalGenerator()
    polymarket = PolymarketClient()
    risk_mgr = RiskManager()
    paper = PaperTrader(starting_balance=100.0)

    print(f"\n⏳ A carregar dados iniciais...")

    # Carregar candles iniciais
    candles = price_feed.get_klines(interval="1m", limit=100)
    if not candles:
        print(f"{Fore.RED}❌ Não foi possível obter dados de preço. Verifica a conexão.{Style.RESET_ALL}")
        sys.exit(1)

    print(f"✅ {len(candles)} candles carregadas")
    print(f"💰 Preço atual: ${candles[-1]['close']:,.2f}")
    print(f"\n🔄 Bot ativo — Ctrl+C para parar\n")

    cycle = 0
    pending_positions = []

    try:
        while True:
            cycle += 1

            # 1. Atualizar dados
            new_candles = price_feed.get_klines(interval="1m", limit=100)
            if new_candles:
                candles = new_candles

            orderbook = price_feed.get_orderbook()

            # 2. Análise técnica
            analysis = analyzer.full_analysis(candles, orderbook)

            # 3. Gerar sinal
            signal = signal_gen.generate_signal(analysis)

            # 4. Buscar mercado Polymarket
            market = polymarket.get_active_btc_15m_market()

            # 5. Mostrar análise
            clear_screen()
            print_banner()

            mode = (
                f"{Fore.RED}🔴 LIVE TRADING{Style.RESET_ALL}"
                if Config.LIVE_TRADING
                else f"{Fore.GREEN}📝 PAPER TRADING{Style.RESET_ALL}"
            )
            print(f"  Modo: {mode}  |  Ciclo: #{cycle}")

            print_analysis(analysis, signal, market)

            # 6. Resolver posições pendentes (paper trading)
            current_price = analysis["price"]
            resolved = []
            for pos in pending_positions:
                result = paper.simulate_resolution(pos["id"], current_price)
                if result["success"]:
                    won_str = (
                        f"{Fore.GREEN}WON +${result['pnl']:.2f}{Style.RESET_ALL}"
                        if result["won"]
                        else f"{Fore.RED}LOST ${result['pnl']:.2f}{Style.RESET_ALL}"
                    )
                    print(f"\n  📌 Posição resolvida: {pos['direction']} → {won_str}")
                    risk_mgr.record_trade({
                        "direction": pos["direction"],
                        "amount": pos["amount"],
                        "pnl": result["pnl"],
                        "won": result["won"],
                        "mode": "paper",
                    })
                    resolved.append(pos["id"])

            pending_positions = [
                p for p in pending_positions if p["id"] not in resolved
            ]

            # 7. Decidir se aposta
            if signal["direction"] != "SKIP":
                risk_check = risk_mgr.can_trade(signal["confidence"])

                if risk_check["allowed"]:
                    bet_size = risk_mgr.calculate_bet_size(signal["confidence"])

                    if market:
                        market_price = (
                            market["up_price"]
                            if signal["direction"] == "UP"
                            else market["down_price"]
                        )
                    else:
                        market_price = 0.50  # default para paper trading

                    if Config.LIVE_TRADING and market:
                        # TRADE REAL
                        token_id = (
                            market["up_token_id"]
                            if signal["direction"] == "UP"
                            else market["down_token_id"]
                        )
                        result = polymarket.place_order(
                            token_id=token_id,
                            side="BUY",
                            amount=bet_size,
                            price=market_price,
                        )
                        if result["success"]:
                            print(
                                f"\n  ✅ ORDEM REAL: {signal['direction']}"
                                f" ${bet_size:.2f} @ {market_price:.2f}"
                            )
                        else:
                            print(f"\n  ❌ Ordem falhou: {result['reason']}")
                    else:
                        # PAPER TRADE
                        result = paper.place_bet(
                            direction=signal["direction"],
                            amount=bet_size,
                            market_price=market_price,
                            btc_price=current_price,
                            market_info=market,
                        )
                        if result["success"]:
                            pending_positions.append(result["position"])
                            print(
                                f"\n  📝 PAPER TRADE: {signal['direction']}"
                                f" ${bet_size:.2f} @ {market_price:.2f}"
                                f"  (saldo: ${result['remaining_balance']:.2f})"
                            )
                else:
                    print(f"\n  ⛔ Trade bloqueada: {risk_check['reason']}")

            # 8. Mostrar estatísticas
            print_paper_summary(paper)

            stats = risk_mgr.get_stats()
            if stats["total_trades"] > 0:
                print(f"\n{Fore.CYAN}📊 ESTATÍSTICAS GERAIS{Style.RESET_ALL}")
                print(f"  Win rate: {stats['win_rate']:.1f}%")
                print(f"  P&L total: ${stats['total_pnl']:.2f}")
                print(f"  Hoje: {stats['today_trades']} trades, "
                      f"${stats['today_pnl']:.2f}")

            # 9. Próximo ciclo
            next_in = Config.CYCLE_INTERVAL_SECONDS
            print(f"\n  ⏳ Próxima análise em {next_in}s...")
            print(f"  Pressiona Ctrl+C para parar")

            time.sleep(next_in)

    except KeyboardInterrupt:
        print(f"\n\n{Fore.YELLOW}👋 Bot parado pelo utilizador{Style.RESET_ALL}")
        print_paper_summary(paper)
        stats = risk_mgr.get_stats()
        if stats["total_trades"] > 0:
            print(f"\n📊 Resultado final:")
            print(f"  Trades: {stats['total_trades']}")
            print(f"  Win rate: {stats['win_rate']:.1f}%")
            print(f"  P&L: ${stats['total_pnl']:.2f}")
        print(f"\n✅ Log guardado em: {Config.TRADES_LOG_FILE}")


if __name__ == "__main__":
    main()
