import requests
import pandas as pd
import time
import os

TOKEN = os.getenv("TOKEN")
CHAT_ID = os.getenv("CHAT_ID")

pairs = [
    "BTCUSDT","ETHUSDT","SOLUSDT","BNBUSDT","XRPUSDT",
    "ADAUSDT","DOGEUSDT","AVAXUSDT","MATICUSDT","DOTUSDT"
]

# enviar mensaje telegram
def send_signal(message):
    url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
    data = {"chat_id": CHAT_ID, "text": message}
    requests.post(url, data=data)

# obtener datos
def get_data(pair, interval):
    url = f"https://api.binance.com/api/v3/klines?symbol={pair}&interval={interval}&limit=100"
    data = requests.get(url).json()
    df = pd.DataFrame(data)

    df["close"] = df[4].astype(float)
    return df

# EMA
def ema(series, period):
    return series.ewm(span=period, adjust=False).mean()

# RSI
def rsi(df, period=14):
    delta = df["close"].diff()
    gain = (delta.where(delta > 0, 0)).rolling(period).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(period).mean()
    rs = gain / loss
    return 100 - (100 / (1 + rs))

# analizar tendencia (1H y 15M)
def trend(pair):
    df1h = get_data(pair, "1h")
    df15 = get_data(pair, "15m")

    df1h["ema50"] = ema(df1h["close"], 50)
    df15["ema50"] = ema(df15["close"], 50)

    t1h = df1h["close"].iloc[-1] > df1h["ema50"].iloc[-1]
    t15 = df15["close"].iloc[-1] > df15["ema50"].iloc[-1]

    if t1h and t15:
        return "CALL"
    elif not t1h and not t15:
        return "PUT"
    else:
        return None

# entrada en 1 minuto
def entry(pair, direction):
    df = get_data(pair, "1m")

    df["ema9"] = ema(df["close"], 9)
    df["ema21"] = ema(df["close"], 21)
    df["rsi"] = rsi(df)

    last = df.iloc[-1]

    if direction == "CALL":
        if last["ema9"] > last["ema21"] and last["rsi"] < 55:
            return True

    if direction == "PUT":
        if last["ema9"] < last["ema21"] and last["rsi"] > 45:
            return True

    return False

print("BOT PRO ACTIVO")
send_signal("🤖 BOT PRO ACTIVO")

while True:
    print("Analizando mercado...")

    for pair in pairs:
        try:
            direction = trend(pair)

            if direction:
                # AVISO PREVIO
                send_signal(f"⚠️ PREPARAR\nPar: {pair}\nPosible: {direction}")

                time.sleep(10)

                # CONFIRMACIÓN
                if entry(pair, direction):
                    send_signal(f"""
🚨 ENTRA YA

Par: {pair}
Dirección: {direction}
Entrada: próxima vela
Expiración: 3 minutos
""")

                time.sleep(5)

        except Exception as e:
            print("ERROR:", e)

    time.sleep(60)