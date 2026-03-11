# Binance Futures Trading Bot

Automated trading bot for Binance Futures with grid strategy and risk management.

## ⚠️ Disclaimer

Trading cryptocurrencies involves substantial risk. This software is for educational purposes only. Use at your own risk.

## Features

- Grid-based futures trading
- Risk management controls
- Paper trading mode
- Multi-symbol support

## Installation

```bash
# Clone repo
git clone https://github.com/lukmanc405/binance-futures.git
cd binance-futures

# Install dependencies
pip install -r requirements.txt

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
| `GRID_LEVELS` | Number of grid levels |
| `POSITION_SIZE` | Position size per grid |

## License

MIT License - See [LICENSE](LICENSE)

## Author

lukmanc405

