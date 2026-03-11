# Binance Futures Trading Bot

Automated trading bot for Binance Futures with ICT/PrimeSignal strategy and risk management.

## ⚠️ Disclaimer

Trading cryptocurrencies involves substantial risk. This software is for educational purposes only. Use at your own risk.

## Strategy

ICT (Inner Circle Trader) inspired strategy with:
- Multi-timeframe S/R detection (15m, 1h, 4h)
- EMA-based trend identification (21, 50, 200)
- RSI momentum filter
- Fibonacci extension targets (1.272, 1.618)
- Pattern detection (Consolidation, Bullish Rectangle)
- Breakout & Bounce entry zones

## Features

- ICT/PrimeSignal strategy implementation
- Risk management controls
- Paper trading mode
- Multi-symbol support

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
# Run in paper mode (recommended for testing)
python autopilot-v6.py --paper

# Run in live mode
python autopilot-v6.py --live
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

