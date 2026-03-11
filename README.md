# Binance Futures Trading Bot

Automated trading bot for Binance Futures with PrimeSignal strategy and risk management.

## ⚠️ Disclaimer

Trading cryptocurrencies involves substantial risk. This software is for educational purposes only. Use at your own risk.

## Strategy

PrimeSignal is a custom price action strategy featuring:
- Multi-timeframe S/R detection (15m, 1h, 4h)
- EMA-based trend identification (21, 50, 200)
- RSI momentum filter
- Fibonacci extension targets (1.272, 1.618)
- Pattern detection (Consolidation, Bullish Rectangle)
- Breakout & Bounce entry zones

## Features

- PrimeSignal strategy implementation
- Risk management controls
- Multi-symbol support
- Telegram signal notifications

## Installation

```bash
# Clone repo
git clone https://github.com/lukmanc405/binance-futures.git
cd binance-futures

# Install dependencies
pip install requests

# Configure
cp .env.example .env
# Edit .env with your API keys
```

## Usage

```bash
# Run the bot
python autopilot-v6.py
```

## Configuration

Set these environment variables in `.env`:

| Variable | Description |
|----------|-------------|
| `BINANCE_API_KEY` | Your Binance API key |
| `BINANCE_SECRET` | Your Binance secret |
| `SYMBOLS` | Trading pairs (e.g., BTCUSDT) |
| `TELEGRAM_CHANNEL` | Telegram channel for signals |

## Risk Parameters

- Max margin per position: 30%
- Entry size: 5% of margin
- Max positions: 8
- Min entry: 15 USDT
- Stop Loss: Below/above EMA-21
- Take Profit: Fibonacci 1.272 / 1.618 extension

## License

MIT License - See [LICENSE](LICENSE)

## Author

lukmanc405

