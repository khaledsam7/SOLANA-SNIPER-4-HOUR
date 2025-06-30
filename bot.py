# bot.py

import ccxt
import pandas as pd
import numpy as np
import schedule
import time
from ta.momentum import StochasticOscillator
from ta.trend import MACD
from config import *

def initialize_client():
    return ccxt.mexc({
        'apiKey': API_KEY,
        'secret': API_SECRET,
        'enableRateLimit': True,
        'options': {
            'defaultType': 'swap'
        }
    })

def fetch_ohlcv(client, pair):
    symbol = pair.replace('_', '/') + ':SWAP'
    candles = client.fetch_ohlcv(symbol, timeframe='4h', limit=200)
    df = pd.DataFrame(candles, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
    df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
    return df

def calculate_indicators(df):
    stoch = StochasticOscillator(high=df['high'], low=df['low'], close=df['close'], window=14, smooth_window=3)
    df['stoch_k'] = stoch.stoch()
    df['stoch_d'] = stoch.stoch_signal()
    macd = MACD(close=df['close'])
    df['macd'] = macd.macd()
    df['macd_signal'] = macd.macd_signal()
    df['wt_cross'] = df['macd'] - df['macd_signal']
    return df

def generate_signal(df):
    latest = df.iloc[-1]
    prev = df.iloc[-2]

    buy_signal = (
        latest['stoch_k'] > latest['stoch_d'] and
        prev['stoch_k'] < prev['stoch_d'] and
        latest['stoch_k'] < 20 and
        latest['wt_cross'] > 0 and
        prev['wt_cross'] < 0
    )
    return 'buy' if buy_signal else None

def calculate_order_size(client, pair, balance_pct):
    balance_info = client.fetch_balance({'type': 'swap'})
    coin = pair.split('_')[0]
    balance = balance_info['total'].get(coin, 0)
    position_size = balance * (balance_pct / 100)
    return round(position_size, 2)

def place_order(client, side, amount, price, pair):
    symbol = pair.replace('_', '/') + ':SWAP'
    order = client.create_order(
        symbol=symbol,
        type='market',
        side=side,
        amount=amount,
        params={'leverage': LEVERAGE}
    )
    print(f"Placed {side.upper()} order: {order}")
    return order

def run_bot():
    try:
        print("Checking for trade setup...")
        client = initialize_client()
        df = fetch_ohlcv(client, PAIR)
        df = calculate_indicators(df)
        signal = generate_signal(df)

        if signal == 'buy':
            print("✅ Buy Signal Detected!")
            size = calculate_order_size(client, PAIR, POSITION_SIZE_PERCENTAGE)
            market_price = df['close'].iloc[-1]
            place_order(client, 'buy', size, market_price, PAIR)
        else:
            print("No signal yet.")

    except Exception as e:
        print(f"⚠️ Error: {e}")

schedule.every(CHECK_INTERVAL_MINUTES).minutes.do(run_bot)

print("🔁 Bot started... running every", CHECK_INTERVAL_MINUTES, "minutes.")
print("✅ Sniper Bot is running...")
run_bot()

while True:
    schedule.run_pending()
    time.sleep(1)
