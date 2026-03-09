# binance-futures

Binance Futures trading automation with ICT strategy signals.

## Tools
- exec: Run Python scripts for trading
- message: Send signals to Telegram channel

## Files
- `/root/.openclaw/workspace/autopilot-v6.py` - Latest version with Multi-TF analysis (RECOMMENDED)
- `/root/.openclaw/workspace/autopilot-v5-secure.py` - Secure version with error handling
- `/root/.openclaw/workspace/autopilot-v5.py` - ICT strategy
- `/root/.openclaw/workspace/autopilot-v4.py` - Legacy version
- `/root/.openclaw/workspace/futures_symbols.json` - Valid futures symbols cache
- `/root/.openclaw/workspace/trading-strategy.md` - ICT trading guide

## Configuration
Set environment variables (RECOMMENDED):
```bash
export BINANCE_API_KEY="your_api_key"
export BINANCE_SECRET="your_secret"
export TELEGRAM_CHANNEL="-1003847994290"
```

## Autopilot Rules
| Position | TP | SL |
|----------|-----|-----|
| LONG | +10% | -5% |
| SHORT | -10% | +5% |

- Entry: 5% balance per position (notional with 5x leverage)
- Min Entry: $15 margin
- Max Margin: 30%
- Max Positions: 8
- No re-entry for recently closed coins (auto-clears after 1 hour)

## ICT Strategy (v6 - Multi-Timeframe)

### Indicators
- **EMA-21**: Fast MA for entries
- **EMA-50**: Medium MA
- **EMA-200**: Trend confirmation
- **RSI (14)**: Momentum

### Structure Analysis
- **Support**: Nearest support zone
- **Resistance**: Nearest resistance zone
- **Range Height**: Support to Resistance distance

### Entry Strategies (like BNX chart)
1. **Breakout Entry**: When price breaks above resistance
   - SL: Below EMA-21
2. **Bounce Entry**: When price touches support and bounces
   - SL: Below support

### Target Calculation
- **TP1**: Current + (Range × 1.272)
- **TP2**: Current + (Range × 1.618)

### Trend Confirmation
- **Above EMA-200**: Uptrend (LONG)
- **Below EMA-200**: Downtrend (SHORT)

## Signal Template (Wajib Post)
```
📈 [PAIR] TECHNICAL ANALYSIS 📊

📊 Chart: https://www.tradingview.com/chart/?symbol=BINANCE:[PAIR]

📐 ICT INDICATORS:
• RSI (14): [value]
• EMA 21: [value]
• EMA 50: [value]
• EMA 200: [value]
• Trend: [BEARISH/BULLISH]

📊 STRUCTURE (Multi-TF):
• Support: [value]
• Resistance: [value]
• Range: [value]

💡 ENTRY STRATEGIES:
1. Breakout: > [resistance] (SL: below EMA-21)
2. Bounce: [support] (SL: below support)

💡 INSIGHT: [Analytical based on RSI + EMA + S/R]

🎯 Entry: $[entry]
📈 TP1: $[Fib 1.272]
📈 TP2: $[Fib 1.618]
🛡️ SL: $[Below support/EMA-21]

⏰ Timeframe: 1H
```

## Usage

### Check Positions
```bash
python3 << 'EOF'
import hmac, hashlib, time, requests

API_KEY = "YOUR_API_KEY"
SECRET = "YOUR_SECRET"

ts = int(time.time() * 1000)
params = f"timestamp={ts}"
sig = hmac.new(SECRET.encode(), params.encode(), hashlib.sha256).hexdigest()
r = requests.get(f"https://fapi.binance.com/fapi/v2/positionRisk?{params}&signature={sig}", headers={"X-MBX-APIKEY": API_KEY})
positions = r.json()
for p in positions:
    amt = float(p.get('positionAmt',0))
    if amt != 0:
        pct = ((float(p.get('markPrice',0))-float(p.get('entryPrice',0)))/float(p.get('entryPrice',0)))*100
        print(f"{p.get('symbol')}: {pct:+.2f}%")
EOF
```

### Run Autopilot
```bash
export BINANCE_API_KEY="your_key"
export BINANCE_SECRET="your_secret"
cd /root/.openclaw/workspace && python3 autopilot-v6.py
```

### Stop Autopilot
```bash
pkill -f autopilot-v6
```

## Security Features (v5+)
| Issue | Fix |
|-------|-----|
| Hardcoded API Keys | Environment variables |
| No request timeout | 10s timeout |
| Bare except clauses | Specific exceptions |
| Unbounded memory | Auto-clear after 1 hour |
| No API validation | Error checking |

## Rules Reminder
- **Setiap entry WAJIB post signal template ke channel -1003847994290**
- Include: Entry price, Current price, TP, SL, RSI, EMA-21/50/200, Support/Resistance, Entry strategies, Insight analytical

## Current Status
- Balance: ~$334 USDT
- Positions: BANANA, ROBO
- Running: autopilot-v5-secure.py
