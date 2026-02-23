# 🤖 Polymarket BTC 15-Minute Trading Bot

Bot autónomo que analisa indicadores técnicos do Bitcoin e gera sinais UP/DOWN para os mercados de 15 minutos do Polymarket.

## ⚠️ AVISO IMPORTANTE
- Este bot começa em **PAPER TRADING** (simulação, sem dinheiro real)
- Isto NÃO é conselho financeiro
- Podes perder TODO o dinheiro investido
- Testa extensivamente antes de usar dinheiro real
- Mercados de 15 minutos são extremamente voláteis

## 🚀 Setup no GitHub Codespaces

### 1. Criar o Codespace
- Faz fork deste repositório
- Clica **"<> Code"** → **"Codespaces"** → **"Create codespace on main"**

### 2. Instalar dependências
```bash
pip install -r requirements.txt
```

### 3. Configurar (copiar .env)
```bash
cp .env.example .env
```

### 4. Correr em PAPER TRADING (recomendado para começar)
```bash
python bot.py
```

### 5. Para trading real (DEPOIS de testar)
Edita o `.env`:
```
LIVE_TRADING=true
POLYMARKET_PRIVATE_KEY=tua_chave_privada
POLYMARKET_API_KEY=tua_api_key
POLYMARKET_SECRET=teu_secret
POLYMARKET_PASSPHRASE=tua_passphrase
MAX_BET_SIZE=2.0
```
Depois corre:
```bash
python bot.py
```

## 📊 Indicadores usados
- **RSI (14)** — Relative Strength Index
- **MACD** — Moving Average Convergence Divergence
- **EMA 9/21** — Exponential Moving Averages
- **VWAP** — Volume Weighted Average Price
- **Bollinger Bands** — Volatilidade
- **Momentum** — Taxa de variação do preço

## 🧠 Lógica de decisão
O bot atribui um score a cada indicador (+1 para bullish, -1 para bearish).
- Score agregado > threshold → **UP**
- Score agregado < -threshold → **DOWN**
- Score entre -threshold e threshold → **SKIP** (não aposta)

## 📁 Estrutura
```
polymarket-btc-bot/
├── bot.py              # Loop principal
├── analyzer.py         # Análise técnica
├── signals.py          # Geração de sinais UP/DOWN
├── polymarket_client.py # API do Polymarket
├── price_feed.py       # Preços em tempo real (Binance)
├── risk_manager.py     # Gestão de risco
├── paper_trader.py     # Simulação sem dinheiro real
├── config.py           # Configurações
├── requirements.txt    # Dependências
├── .env.example        # Template de configuração
└── README.md           # Este ficheiro
```

## 📈 Performance tracking
O bot regista todas as trades (reais e simuladas) em `trades_log.json`.
No final de cada sessão mostra:
- Win rate
- Profit/Loss total
- Melhor e pior trade
- Número de trades executadas vs skipped
