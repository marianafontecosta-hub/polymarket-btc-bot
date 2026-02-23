"""
🔔 SIGNAL ONLY — Sinal UP/DOWN a cada 60 segundos
===================================================
Versão simplificada: apenas mostra o sinal para apostares manualmente.
Não faz trades automáticos. Não precisa de credenciais Polymarket.

Uso:
    python signal_only.py              # sinal a cada 60 segundos
    python signal_only.py --interval 30  # sinal a cada 30 segundos
    python signal_only.py --interval 10  # sinal a cada 10 segundos
"""
import os
import sys
import time
import argparse
from datetime import datetime

try:
    from colorama import init, Fore, Style, Back
    init(autoreset=True)
except ImportError:
    # Fallback se colorama não estiver instalada
    class Fore:
        GREEN = RED = YELLOW = CYAN = WHITE = MAGENTA = ""
    class Back:
        GREEN = RED = YELLOW = ""
    class Style:
        RESET_ALL = BRIGHT = ""


from price_feed import PriceFeed
from analyzer import TechnicalAnalyzer
from signals import SignalGenerator


def clear():
    os.system("cls" if os.name == "nt" else "clear")


def beep():
    """Tenta fazer um som para chamar atenção."""
    try:
        print("\a", end="", flush=True)
    except Exception:
        pass


def main():
    parser = argparse.ArgumentParser(description="Polymarket BTC Signal Bot")
    parser.add_argument(
        "--interval", type=int, default=60,
        help="Segundos entre cada sinal (default: 60)"
    )
    args = parser.parse_args()
    interval = args.interval

    # Inicializar
    feed = PriceFeed()
    analyzer = TechnicalAnalyzer()
    signal_gen = SignalGenerator()

    # Histórico de sinais
    signal_history = []
    correct = 0
    total_resolved = 0

    print(f"\n⏳ A carregar dados...")
    candles = feed.get_klines(interval="1m", limit=100)
    if not candles:
        print("❌ Sem dados. Verifica a tua conexão à internet.")
        sys.exit(1)

    print(f"✅ Pronto! Sinais a cada {interval} segundos.\n")
    time.sleep(1)

    cycle = 0
    last_signal = None
    last_price = None

    try:
        while True:
            cycle += 1

            # Atualizar dados
            new_candles = feed.get_klines(interval="1m", limit=100)
            if new_candles:
                candles = new_candles

            orderbook = feed.get_orderbook()
            analysis = analyzer.full_analysis(candles, orderbook)
            signal = signal_gen.generate_signal(analysis)

            price = analysis["price"]
            now = datetime.now().strftime("%H:%M:%S")

            # Verificar sinal anterior
            if last_signal and last_price:
                went_up = price >= last_price
                was_correct = (
                    (last_signal == "UP" and went_up)
                    or (last_signal == "DOWN" and not went_up)
                )
                if last_signal != "SKIP":
                    total_resolved += 1
                    if was_correct:
                        correct += 1

            # ===== DISPLAY =====
            clear()

            # Header
            print(Fore.CYAN + "╔══════════════════════════════════════════════════╗")
            print("║     🔔 POLYMARKET BTC — SIGNAL ONLY              ║")
            print("╚══════════════════════════════════════════════════╝" + Style.RESET_ALL)

            # Preço
            price_change = ""
            if last_price:
                diff = price - last_price
                pct = (diff / last_price) * 100
                if diff >= 0:
                    price_change = f"  {Fore.GREEN}▲ +${diff:,.2f} (+{pct:.3f}%){Style.RESET_ALL}"
                else:
                    price_change = f"  {Fore.RED}▼ ${diff:,.2f} ({pct:.3f}%){Style.RESET_ALL}"

            print(f"\n  💰 BTC:  {Fore.WHITE}${price:,.2f}{Style.RESET_ALL}{price_change}")
            print(f"  ⏰ Hora: {now}  |  Ciclo: #{cycle}")

            # Indicadores resumidos
            print(f"\n  ┌─────────────────────────────────────────┐")

            rsi = analysis["rsi"]
            rsi_color = Fore.GREEN if rsi < 40 else (Fore.RED if rsi > 60 else Fore.YELLOW)
            print(f"  │ RSI:      {rsi_color}{rsi:>6.1f}{Style.RESET_ALL}  ", end="")
            if rsi < 30: print("  ← Oversold (bullish)")
            elif rsi > 70: print("  ← Overbought (bearish)")
            else: print("  ← Neutral")

            macd = analysis["macd"]
            macd_color = Fore.GREEN if macd["bullish"] else Fore.RED
            print(f"  │ MACD:     {macd_color}{macd['histogram']:>+.4f}{Style.RESET_ALL}  ", end="")
            print("  ← Bullish" if macd["bullish"] else "  ← Bearish")

            ema_cross = analysis["ema_crossover"]
            ema_color = Fore.GREEN if ema_cross else Fore.RED
            print(f"  │ EMA 9/21: {ema_color}{'Cross ↑' if ema_cross else 'Cross ↓':>8}{Style.RESET_ALL}  ", end="")
            print(f"  ← {analysis['ema_9']:.0f} / {analysis['ema_21']:.0f}")

            mom = analysis["momentum"]
            mom_color = Fore.GREEN if mom["bullish"] else Fore.RED
            print(f"  │ Momentum: {mom_color}{mom['percent']:>+.3f}%{Style.RESET_ALL}")

            vwap = analysis["vwap"]
            vwap_pos = analysis["price_vs_vwap"]
            vwap_color = Fore.GREEN if vwap_pos == "above" else Fore.RED
            print(f"  │ VWAP:     {vwap_color}{vwap_pos:>8}{Style.RESET_ALL}  ", end="")
            print(f"  ← ${vwap:,.2f}")

            bb = analysis["bollinger"]
            if bb["upper"] != bb["lower"]:
                bb_pos = (price - bb["lower"]) / (bb["upper"] - bb["lower"])
                bb_color = Fore.GREEN if bb_pos < 0.3 else (Fore.RED if bb_pos > 0.7 else Fore.YELLOW)
                print(f"  │ Bollinger:{bb_color}{bb_pos:>7.0%}{Style.RESET_ALL}  ", end="")
                print(f"  ← L:{bb['lower']:.0f} U:{bb['upper']:.0f}")

            if analysis.get("orderbook"):
                ob = analysis["orderbook"]
                ob_color = Fore.GREEN if ob["bullish"] else Fore.RED
                print(f"  │ Orderbook:{ob_color}{ob['ratio']:>7.2f}{Style.RESET_ALL}  ", end="")
                print("  ← Buyers" if ob["bullish"] else "  ← Sellers")

            print(f"  └─────────────────────────────────────────┘")

            # ===== SINAL PRINCIPAL =====
            direction = signal["direction"]
            confidence = signal["confidence"]

            print()
            if direction == "UP":
                beep()
                print(f"  ╔══════════════════════════════════════════╗")
                print(f"  ║  {Back.GREEN}{Fore.WHITE}  🟢  SINAL:  UP  ▲  — COMPRA UP  {Style.RESET_ALL}       ║")
                print(f"  ╚══════════════════════════════════════════╝")
            elif direction == "DOWN":
                beep()
                print(f"  ╔══════════════════════════════════════════╗")
                print(f"  ║  {Back.RED}{Fore.WHITE}  🔴  SINAL:  DOWN ▼ — COMPRA DOWN {Style.RESET_ALL}       ║")
                print(f"  ╚══════════════════════════════════════════╝")
            else:
                print(f"  ╔══════════════════════════════════════════╗")
                print(f"  ║  {Back.YELLOW}  ⏸️  SINAL:  SKIP — NÃO APOSTAR   {Style.RESET_ALL}       ║")
                print(f"  ╚══════════════════════════════════════════╝")

            print(f"\n  Confiança: {confidence:.0%}  |  "
                  f"Score: {signal['score']:+.3f}  |  "
                  f"Votos: 🟢{signal['bullish_votes']} "
                  f"🔴{signal['bearish_votes']} "
                  f"⚪{signal['neutral_votes']}")

            # Explicação
            print(f"\n  {signal['recommendation']}")

            # Accuracy tracking
            if total_resolved > 0:
                acc = (correct / total_resolved) * 100
                acc_color = Fore.GREEN if acc > 55 else (Fore.RED if acc < 45 else Fore.YELLOW)
                print(f"\n  📊 Accuracy: {acc_color}{acc:.1f}%{Style.RESET_ALL}"
                      f" ({correct}/{total_resolved} corretos)")

            # Histórico últimos 5 sinais
            signal_history.append({
                "time": now,
                "direction": direction,
                "price": price,
                "confidence": confidence,
            })
            if len(signal_history) > 10:
                signal_history = signal_history[-10:]

            if len(signal_history) > 1:
                print(f"\n  📜 Últimos sinais:")
                for s in signal_history[-5:]:
                    emoji = "🟢" if s["direction"] == "UP" else (
                        "🔴" if s["direction"] == "DOWN" else "⏸️"
                    )
                    print(f"     {s['time']} {emoji} {s['direction']:>4}"
                          f" @ ${s['price']:,.2f}"
                          f" ({s['confidence']:.0%})")

            # Footer
            print(f"\n  ⏳ Próximo sinal em {interval}s  |  Ctrl+C para sair")

            # Guardar para comparar no próximo ciclo
            if signal["direction"] != "SKIP":
                last_signal = signal["direction"]
                last_price = price

            time.sleep(interval)

    except KeyboardInterrupt:
        print(f"\n\n  👋 Parado.")
        if total_resolved > 0:
            acc = (correct / total_resolved) * 100
            print(f"  📊 Accuracy final: {acc:.1f}% ({correct}/{total_resolved})")
        print()


if __name__ == "__main__":
    main()
