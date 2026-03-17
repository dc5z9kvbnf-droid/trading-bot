import requests
import pandas as pd
import time
import os

TOKEN = os.getenv("TOKEN")
CHAT_ID = os.getenv("CHAT_ID")

pairs = ["BTCUSDT","ETHUSDT","SOLUSDT","XRPUSDT","ADAUSDT"]

# telegram
def send_signal(msg):
    url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
    requests.post(url, data={"chat_id": CHAT_ID, "text": msg})

# datos BYBIT
def get_data(pair, interval="1"):
    url = f"https://api.bybit.com/v5/market/kline?category=linear&symbol={pair}&interval={interval}&limit=100"
    data = requests.get(url).json()

    if "result" not in data:
        print("Error datos", pair)
        return None

    df = pd.DataFrame(data["result"]["list"])

    if df.empty:
        return None

    df["close"] = df[4].astype(float)
    return df

# EMA
def ema(series, n):
    return series.ewm(span=n).mean()

# RSI
def rsi(df, period=14):
    delta = df["close"].diff()
    gain = (delta.where(delta > 0, 0)).rolling(period).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(period).mean()
    rs = gain / loss
    return 100 - (100 / (1 + rs))

# tendencia (15m)
def trend(pair):
    df = get_data(pair, "15")

    if df is None:
        return None

    df["ema50"] = ema(df["close"], 50)
    last = df.iloc[-1]

    if last["close"] > last["ema50"]:
        return "CALL"
    else:
        return "PUT"

# entrada (1m)
def entry(pair, direction):
    df = get_data(pair, "1")

    if df is None:
        return False

    df["ema9"] = ema(df["close"], 9)
    df["ema21"] = ema(df["close"], 21)
    df["rsi"] = rsi(df)

    last = df.iloc[-1]

    if direction == "CALL":
        return last["ema9"] > last["ema21"] and last["rsi"] < 60

    if direction == "PUT":
        return last["ema9"] < last["ema21"] and last["rsi"] > 40

    return False

print("BOT ACTIVO")
send_signal("🤖 BOT ACTIVO EN RAILWAY")

while True:
    print("Analizando...")

    for pair in pairs:
        try:
            dir = trend(pair)

            if dir:
                send_signal(f"⚠️ PREPARAR {pair} {dir}")
                time.sleep(5)

                if entry(pair, dir):
                    send_signal(f"""
🚨 ENTRA YA

Par: {pair}
Dirección: {dir}
Entrada: próxima vela
Expiración: 3 minutos
""")

                time.sleep(5)

        except Exception as e:
            print("ERROR:", e)

    time.sleep(60)