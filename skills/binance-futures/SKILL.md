# binance-futures

**Binance Futures trading automation with PrimeSignal Algorithm.**

## Description

- 🎯 PrimeSignal Algorithm - AI-powered precision trading
- 📈 Fibonacci Extension TP/SL for optimal profit targets
- 🛡️ Max 8 positions, 40% margin cap
- ⚡ Fully automated entry & exit

## Configuration

Create a `.env` file in workspace root:
```bash
cp .env.example .env
nano .env  # Edit your API keys
```

Required variables:
```
BINANCE_API_KEY=your_api_key
BINANCE_SECRET=your_secret
```

## Files
- `.env.example` - Template for API keys
- `autopilot-v5-secure.py` - Main autopilot script

## Autopilot Rules (Fibonacci Extension)
| Position | Entry | TP | SL |
|----------|-------|-----|-----|
| LONG | Buy at support/EMA-21 | price + (range × 1.272) | Below support/EMA-21 |
| SHORT | Sell at resistance/EMA-21 | price - (range × 1.272) | Above resistance/EMA-21 |

- Entry: 5% balance × leverage
- Max Margin: 40%
- Max Positions: 8

## Security
⚠️ NEVER commit `.env` to GitHub!
- Add `.env` to `.gitignore`
- Only `.env.example` should be committed

## Running
```bash
# Load env vars and run
source .env && python3 autopilot-v5-secure.py

# Or use the startup script
bash run-autopilot.sh
```
