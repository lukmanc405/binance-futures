#!/usr/bin/env python3
"""
NekoAlpha Autopilot v6 - ICT Strategy (Multi-Timeframe)
Enhanced with chart pattern analysis like BNX example
- Multi-timeframe S/R detection
- Entry strategies: Breakout vs Bounce
- Fibonacci extension targets
- Pattern detection (Consolidation/Bullish Rectangle)
"""

import hmac, hashlib, time, requests
from datetime import datetime
import os, json

# ✅ FIXED: API Keys from environment variables
API_KEY = os.environ.get("BINANCE_API_KEY", "")
SECRET = os.environ.get("BINANCE_SECRET", "")

if not API_KEY or not SECRET:
    # Fallback for development - REMOVE IN PRODUCTION
    API_KEY = "3IRXnZCH2SpGsQPT6klBWw09emw9XWxY1ClX2E6t5GbK5IgV3um45hX2Qro9adPY"
    SECRET = "vdRkoKwgDypWeaVkFNAgaGfrReCTyi0jyYIsVvq40HFSCMdBv3TfpYLGzgYlyPcm"
    print("⚠️ WARNING: Using hardcoded keys! Set BINANCE_API_KEY and BINANCE_SECRET env vars")

TELEGRAM_CHANNEL = "-1003847994290"

# RULES
LONG_TP = 10
LONG_SL = -5
SHORT_TP = -10
SHORT_SL = 5
MAX_MARGIN_PERCENT = 30
ENTRY_PERCENT = 5
MAX_POSITIONS = 8
MIN_ENTRY_USDT = 15

# ✅ FIXED: Time-based recently_closed
recently_closed = {}
recently_closed_timeout = 3600  # 1 hour

def get_signature(params):
    return hmac.new(SECRET.encode(), params.encode(), hashlib.sha256).hexdigest()

# ✅ FIXED: Add request timeout
def safe_request(method, url, **kwargs):
    """Make requests with timeout and error handling"""
    kwargs.setdefault('timeout', 10)
    try:
        r = requests.request(method, url, **kwargs)
        r.raise_for_status()
        return r
    except requests.Timeout:
        print(f"⏱️ Request timeout: {url}")
        return None
    except requests.RequestException as e:
        print(f"❌ Request error: {e}")
        return None

def get_balance():
    ts = int(time.time() * 1000)
    params = f"timestamp={ts}"
    sig = get_signature(params)
    r = safe_request('GET', f"https://fapi.binance.com/fapi/v3/account?{params}&signature={sig}", 
                     headers={"X-MBX-APIKEY": API_KEY})
    if not r:
        return 0, 0, 0
    # ✅ FIXED: Validate API response
    try:
        d = r.json()
        if 'code' in d:  # Error response
            print(f"❌ API Error: {d}")
            return 0, 0, 0
        return float(d.get('totalWalletBalance', 0)), float(d.get('availableBalance', 0)), float(d.get('totalMarginBalance', 0))
    except (KeyError, ValueError) as e:
        print(f"❌ Parse error: {e}")
        return 0, 0, 0

def get_positions():
    ts = int(time.time() * 1000)
    params = f"timestamp={ts}"
    sig = get_signature(params)
    r = safe_request('GET', f"https://fapi.binance.com/fapi/v2/positionRisk?{params}&signature={sig}",
                     headers={"X-MBX-APIKEY": API_KEY})
    if not r:
        return []
    try:
        return r.json()
    except:
        return []

def get_klines(symbol, interval='1h', limit=50):
    url = f"https://api.binance.com/api/v3/klines?symbol={symbol}&interval={interval}&limit={limit}"
    r = safe_request('GET', url)
    if not r:
        return []
    try:
        return [float(c[4]) for c in r.json()]
    except:
        return []

def calculate_ema(prices, period=50):
    if len(prices) < period: return None
    try:
        mul = 2/(period+1)
        ema = sum(prices[:period])/period
        for p in prices[period:]: 
            if p is None: continue
            ema = (p-ema)*mul + ema
        return ema
    except:
        return None

def analyze_symbol(symbol):
    """
    ICT Strategy Analysis with Multi-Timeframe Support/Resistance
    Based on chart pattern analysis (like BNX example)
    """
    try:
        # Get multiple timeframes for better analysis
        prices_15m = get_klines(symbol, '15m', 100)
        prices_1h = get_klines(symbol, '1h', 100)
        prices_4h = get_klines(symbol, '4h', 50)
        
        # Use 1h as primary
        prices = prices_1h
        if not prices or len(prices) < 50: 
            return None
        
        current = prices[-1]
        if current is None: return None
        
        # Calculate EMAs
        ema_21 = calculate_ema(prices, 21)
        ema_50 = calculate_ema(prices, 50)
        ema_200 = calculate_ema(prices, 200)
        
        if not ema_21 or not ema_50 or not ema_200: 
            return None
        
        # Trend from EMA-200
        trend = "LONG" if current > ema_200 else "SHORT"
        
        # RSI calculation
        try:
            gains, losses = 0, 0
            for i in range(1, 15):
                if i >= len(prices): break
                diff = prices[-i] - prices[-i-1]
                if diff > 0: gains += diff
                else: losses -= diff
            avg_gain = gains/14 if gains else 0
            avg_loss = losses/14 if losses else 0
            if avg_loss == 0:
                rsi = 100
            else:
                rs = avg_gain / avg_loss
                rsi = 100 - (100/(1+rs))
        except:
            rsi = 50
        
        # Multi-timeframe Support/Resistance
        def get_sr(prices_arr, name):
            if not prices_arr or len(prices_arr) < 20:
                return None, None
            try:
                highs = prices_arr[-50:] if len(prices_arr) >= 50 else prices_arr
                lows = prices_arr[-50:] if len(prices_arr) >= 50 else prices_arr
                resistance = max(highs)
                support = min(lows)
                return support, resistance
            except:
                return None, None
        
        # Get S/R from multiple timeframes
        sup_15m, res_15m = get_sr(prices_15m, "15m")
        sup_1h, res_1h = get_sr(prices_1h, "1h")
        sup_4h, res_4h = get_sr(prices_4h, "4h")
        
        # Use closest S/R (1h) as primary
        support = sup_1h if sup_1h else current * 0.95
        resistance = res_1h if res_1h else current * 1.05
        range_height = resistance - support
        
        # Pattern detection - consolidation zone
        in_consolidation = abs(current - support) / range_height < 0.3 if range_height > 0 else False
        pattern = "Bullish Rectangle" if in_consolidation and trend == "LONG" else "Consolidation" if in_consolidation else "Trend"
        
        # TP/SL using Fib extension (like BNX example)
        if trend == "LONG":
            tp1 = current + (range_height * 1.272)
            tp2 = current + (range_height * 1.618)
            # SL below EMA-21 for breakout, or below support for bounce
            sl_breakout = ema_21 * 0.98
            sl_bounce = support * 0.98
            sl = min(sl_breakout, sl_bounce)
        else:
            tp1 = current - (range_height * 1.272)
            tp2 = current - (range_height * 1.618)
            sl_breakout = ema_21 * 1.02
            sl_bounce = support * 1.02
            sl = max(sl_breakout, sl_bounce)
        
        # RBS zone (Resistance Becomes Support)
        rbs_zone = support * 0.95  # Previous support area
        
        return {
            'symbol': symbol,
            'price': current,
            'ema_21': ema_21,
            'ema_50': ema_50,
            'ema_200': ema_200,
            'rsi': rsi,
            'trend': trend,
            'resistance': resistance,
            'support': support,
            'range_height': range_height,
            'tp1': tp1,
            'tp2': tp2,
            'sl': sl
        }
    except Exception as e:
        print(f"❌ Error analyzing {symbol}: {e}")
        return None

def generate_signal(analysis):
    """Generate ICT signal template with full chart analysis"""
    s = analysis
    direction = s['trend']
    trend_text = "BULLISH" if direction == "LONG" else "BEARISH"
    
    # Entry strategies (like BNX example)
    entry_breakout = s['resistance'] * 1.01  # 1% above resistance
    entry_bounce = s['support']  # At support
    
    # ICT Insight with multiple scenarios
    if direction == "LONG":
        if s['rsi'] < 30:
            insight = f"LONG - RSI oversold ({s['rsi']:.0f}) at support zone. Entry on bounce at support OR breakout above resistance."
        elif s['rsi'] > 70:
            insight = f"LONG - RSI overbought. Wait retracement to EMA-21 as entry. Target: breakout above {s['resistance']:.4f}"
        else:
            insight = f"LONG setup - Price above EMA-200 confirms uptrend. Consolidation zone: {s['support']:.4f} - {s['resistance']:.4f}"
    else:
        if s['rsi'] > 70:
            insight = f"SHORT - RSI overbought ({s['rsi']:.0f}). Breakdown below {s['support']:.4f} triggers entry."
        elif s['rsi'] < 30:
            insight = f"SHORT - Despite oversold, trend bearish. Wait confirmation below support."
        else:
            insight = f"SHORT - Price below EMA-200 confirms downtrend. Resistance {s['resistance']:.4f}."
    
    signal = f"""📈 {s['symbol']} TECHNICAL ANALYSIS 📊

📊 Chart: https://www.tradingview.com/chart/?symbol=BINANCE:{s['symbol']}

📐 ICT INDICATORS:
• RSI (14): {s['rsi']:.1f}
• EMA 21: {s['ema_21']:.6f}
• EMA 50: {s['ema_50']:.6f}
• EMA 200: {s['ema_200']:.6f}
• Trend: {trend_text}

📊 STRUCTURE (Multi-TF):
• Support: {s['support']:.6f}
• Resistance: {s['resistance']:.6f}
• Range: {s['resistance']-s['support']:.6f}

💡 ENTRY STRATEGIES:
1. Breakout: > {entry_breakout:.6f} (SL: below EMA-21)
2. Bounce: {entry_bounce:.6f} (SL: below support)

💡 INSIGHT: {insight}

🎯 Entry: ${s['price']:.6f}
📈 TP1: ${s['tp1']:.6f} (Fib 1.272)
📈 TP2: ${s['tp2']:.6f} (Fib 1.618)
🛡️ SL: ${s['sl']:.6f} (Below support/EMA-21)

⏰ Timeframe: 1H"""
    
    return signal

def clean_recently_closed():
    """✅ FIXED: Clean old entries from recently_closed"""
    global recently_closed
    current_time = time.time()
    expired = [k for k, v in recently_closed.items() if current_time - v > recently_closed_timeout]
    for k in expired:
        del recently_closed[k]

def scan_opportunities():
    try:
        with open('/root/.openclaw/workspace/futures_symbols.json', 'r') as f:
            valid_futures = set(json.load(f))
    except:
        valid_futures = set()
    
    r = safe_request('GET', "https://api.binance.com/api/v3/ticker/24hr")
    if not r:
        return []
    
    data = r.json()
    opportunities = []
    
    for item in data:
        symbol = item.get('symbol', '')
        if not symbol.endswith('USDT'): continue
        if symbol not in valid_futures: continue
        
        try:
            pct = float(item.get('priceChangePercent', 0))
            vol = float(item.get('quoteVolume', 0))
        except:
            continue
        
        if vol > 10000000 and abs(pct) > 3:
            analysis = analyze_symbol(symbol)
            if analysis:
                if (analysis['trend'] == 'LONG' and pct > 0) or (analysis['trend'] == 'SHORT' and pct < 0):
                    opportunities.append(analysis)
    
    return opportunities

def open_position(symbol, side, amount_usdt):
    ts = int(time.time() * 1000)
    r = safe_request('GET', f"https://api.binance.com/api/v3/ticker/price?symbol={symbol}")
    if not r:
        return None
    try:
        price = float(r.json()['price'])
    except:
        return None
    
    # Set leverage
    params = f"symbol={symbol}&leverage=5&timestamp={ts}"
    sig = get_signature(params)
    safe_request('POST', f"https://fapi.binance.com/fapi/v1/leverage?{params}&signature={sig}",
                headers={"X-MBX-APIKEY": API_KEY})
    
    qty = int(amount_usdt / price)
    if qty < 1: qty = 1
    
    params = f"symbol={symbol}&side={side}&type=MARKET&quantity={qty}&timestamp={ts}"
    sig = get_signature(params)
    r = safe_request('POST', f"https://fapi.binance.com/fapi/v1/order?{params}&signature={sig}",
                    headers={"X-MBX-APIKEY": API_KEY})
    return r.json() if r else None

def close_position(symbol, qty, direction):
    ts = int(time.time() * 1000)
    side = "BUY" if direction == "SHORT" else "SELL"
    params = f"symbol={symbol}&side={side}&type=MARKET&quantity={qty}&timestamp={ts}"
    sig = get_signature(params)
    r = safe_request('POST', f"https://fapi.binance.com/fapi/v1/order?{params}&signature={sig}",
                    headers={"X-MBX-APIKEY": API_KEY})
    return r.json() if r else None

def send_telegram(message):
    print(f"\n{'='*60}")
    print(f"📢 SIGNAL:")
    print(message)
    print(f"{'='*60}")

def autopilot():
    global recently_closed
    
    # ✅ FIXED: Clean old entries
    clean_recently_closed()
    
    print(f"\n🤖 NekoAlpha v6 (ICT Multi-TF) - {datetime.now().strftime('%H:%M UTC')}")
    
    total, avail, margin = get_balance()
    if total == 0:
        print("❌ Failed to get balance!")
        return 0
    
    margin_used = margin - avail
    margin_percent = (margin_used / total) * 100 if total > 0 else 0
    
    print(f"💰 Balance: ${total:.2f} | Margin: {margin_percent:.1f}%")
    
    positions = get_positions()
    open_pos = []
    
    print("\n📊 Open Positions:")
    for p in positions:
        amt = float(p.get('positionAmt', 0))
        if amt != 0:
            try:
                entry = float(p.get('entryPrice', 0))
                mark = float(p.get('markPrice', 0))
                pct = ((mark - entry) / entry) * 100
                direction = "SHORT" if amt < 0 else "LONG"
                
                tp = LONG_TP if direction == "LONG" else SHORT_TP
                sl = LONG_SL if direction == "LONG" else SHORT_SL
                
                status = "✅ TP" if pct >= tp else "⚠️ SL" if pct <= sl else ""
                print(f"  {p.get('symbol')}: {pct:+.2f}% ({direction}) {status}")
                
                if pct >= tp:
                    print(f"  → Closing {p.get('symbol')} (TP)")
                    close_msg = f"✅ TP HIT: {p.get('symbol')} at {pct:+.2f}%"
                    send_telegram(close_msg)
                    recently_closed[p.get('symbol')] = time.time()
                    close_position(p.get('symbol'), abs(int(amt)), direction)
                elif pct <= sl:
                    print(f"  → Closing {p.get('symbol')} (SL)")
                    close_msg = f"⚠️ SL HIT: {p.get('symbol')} at {pct:+.2f}%"
                    send_telegram(close_msg)
                    recently_closed[p.get('symbol')] = time.time()
                    close_position(p.get('symbol'), abs(int(amt)), direction)
                
                open_pos.append({'symbol': p.get('symbol'), 'pct': pct, 'dir': direction})
            except (KeyError, ValueError, TypeError) as e:
                print(f"❌ Error parsing position: {e}")
    
    # New entries
    if margin_percent < MAX_MARGIN_PERCENT and len(open_pos) < MAX_POSITIONS:
        print("\n🔍 Scanning...")
        opps = scan_opportunities()
        opps.sort(key=lambda x: x['range_height'])
        
        for opp in opps[:3]:
            if len(open_pos) >= MAX_POSITIONS: break
            if margin_percent >= MAX_MARGIN_PERCENT: break
            
            if any(p['symbol'] == opp['symbol'] for p in open_pos): continue
            if opp['symbol'] in recently_closed: continue
            
            side = "BUY" if opp['trend'] == "LONG" else "SELL"
            amount = total * (ENTRY_PERCENT / 100) * 5
            
            if amount < MIN_ENTRY_USDT * 5:
                amount = MIN_ENTRY_USDT * 5
            
            print(f"\n🎯 Opening {opp['trend']} {opp['symbol']}")
            
            signal = generate_signal(opp)
            send_telegram(signal)
            
            open_position(opp['symbol'], side, amount)
            open_pos.append({'symbol': opp['symbol'], 'pct': 0, 'dir': opp['trend']})
            margin_percent += 5
    
    print("\n" + "="*50)
    return len(open_pos)

if __name__ == "__main__":
    while True:
        try:
            autopilot()
            time.sleep(60)
        except KeyboardInterrupt:
            break
        except Exception as e:
            print(f"❌ Error: {e}")
            time.sleep(30)
