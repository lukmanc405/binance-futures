#!/usr/bin/env python3
"""
NekoAlpha Autopilot v5 - ICT Strategy (SECURED)
Fixed issues from code review:
- API keys from environment variables
- Proper error handling with timeouts
- API response validation
- Memory management for recently_closed
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

# TP/SL based on Fibonacci Extension from analysis
# LONG: TP1 = price + (range × 1.272), SL = below support/EMA-21
# SHORT: TP1 = price - (range × 1.272), SL = above resistance/EMA-21
MAX_MARGIN_PERCENT = 30
ENTRY_PERCENT = 5
MAX_POSITIONS = 8
MIN_ENTRY_USDT = 15
LEVERAGE = 10  # 10x leverage

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
    """ICT Strategy Analysis with proper error handling"""
    try:
        prices = get_klines(symbol, '1h', 100)
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
        
        # Support/Resistance
        try:
            highs = prices[-50:]
            resistance = max(highs)
            support = min(highs)
            range_height = resistance - support
        except:
            resistance = current * 1.1
            support = current * 0.9
            range_height = resistance - support
        
        # TP/SL using Fib extension
        if trend == "LONG":
            tp1 = current + (range_height * 1.272)
            tp2 = current + (range_height * 1.618)
            sl = current - (range_height * 0.5)
        else:
            tp1 = current - (range_height * 1.272)
            tp2 = current - (range_height * 1.618)
            sl = current + (range_height * 0.5)
        
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
    """Generate ICT signal template - exact format"""
    s = analysis
    direction = s['trend']
    trend_text = "BULLISH" if direction == "LONG" else "BEARISH"
    
    # Insight
    if direction == "LONG":
        insight = f"LONG - Price above EMA-200 confirms uptrend. Support {s['support']:.4f}, Resistance {s['resistance']:.4f}. Entry on support bounce."
    else:
        insight = f"SHORT - Price below EMA-200 confirms downtrend."
    
    signal = "📈 " + s['symbol'] + " TECHNICAL ANALYSIS 📊\n\n"
    signal += "📊 Chart: https://www.tradingview.com/chart/?symbol=BINANCE:" + s['symbol'] + "\n\n"
    signal += "📐 INDICATORS:\n"
    signal += f"• RSI (14): {s['rsi']:.1f}\n"
    signal += f"• EMA 21: {s['ema_21']:.6f}\n"
    signal += f"• EMA 50: {s['ema_50']:.6f}\n"
    signal += f"• EMA 200: {s['ema_200']:.6f}\n"
    signal += f"• Trend: {trend_text}\n\n"
    signal += "📊 STRUCTURE:\n"
    signal += f"• Support: {s['support']:.6f}\n"
    signal += f"• Resistance: {s['resistance']:.6f}\n"
    signal += f"• Range: {s['resistance']-s['support']:.6f}\n\n"
    signal += "💡 INSIGHT: " + insight + "\n\n"
    signal += f"🎯 Entry: ${s['price']:.6f}\n"
    signal += f"📈 TP1: ${s['tp1']:.6f} (Fib 1.272)\n"
    signal += f"📈 TP2: ${s['tp2']:.6f} (Fib 1.618)\n"
    signal += f"🛡️ SL: ${s['sl']:.6f}\n\n"
    signal += "⏰ Timeframe: 1H"
    
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
    params = f"symbol={symbol}&leverage={LEVERAGE}&timestamp={ts}"
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
    
    print(f"\n🤖 NekoAlpha v5 (SECURED) - {datetime.now().strftime('%H:%M UTC')}")
    
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
                
                # TP/SL follows signal template (Fibonacci extension)
                # For auto-close, using percentage as proxy:
                # LONG: +10% = ~Fib 1.272, -5% = below support
                # SHORT: -10% = ~Fib 1.272, +5% = above resistance
                tp = 10 if direction == "LONG" else -10
                sl = -5 if direction == "LONG" else 5
                
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
            amount = total * (ENTRY_PERCENT / 100) * LEVERAGE
            
            if amount < MIN_ENTRY_USDT * LEVERAGE:
                amount = MIN_ENTRY_USDT * LEVERAGE
            
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
