import requests
import pandas as pd
import time

import os

TOKEN = os.getenv("TOKEN")
CHAT_ID = os.getenv("CHAT_ID")

pairs = [
"EURUSD","GBPUSD","AUDUSD","NZDUSD","USDJPY","USDCAD","USDCHF",
"EURJPY","GBPJPY","EURGBP",

"BTCUSDT","ETHUSDT","SOLUSDT","BNBUSDT","XRPUSDT",
"ADAUSDT","DOGEUSDT","AVAXUSDT","LINKUSDT","MATICUSDT"
]

# enviar mensaje telegram
def send_signal(message):

    url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"

    data = {
        "chat_id": CHAT_ID,
        "text": message
    }

    requests.post(url,data=data)

# obtener datos mercado
def get_candles(pair,interval):

    url=f"https://api.binance.com/api/v3/klines?symbol={pair}&interval={interval}&limit=100"

    data=requests.get(url).json()

    df=pd.DataFrame(data)

    df["close"]=df[4].astype(float)
    df["open"]=df[1].astype(float)

    return df

# calcular RSI
def calculate_rsi(df,period=14):

    delta=df["close"].diff()

    gain=(delta.where(delta>0,0)).rolling(period).mean()
    loss=(-delta.where(delta<0,0)).rolling(period).mean()

    rs=gain/loss

    rsi=100-(100/(1+rs))

    return rsi

# analizar mercado
def analyze(pair):

    df1=get_candles(pair,"1m")
    df5=get_candles(pair,"5m")
    df15=get_candles(pair,"15m")

    df1["ma9"]=df1["close"].rolling(9).mean()
    df1["ma21"]=df1["close"].rolling(21).mean()

    df1["rsi"]=calculate_rsi(df1)

    last=df1.iloc[-1]

    trend15=df15["close"].iloc[-1] > df15["close"].rolling(20).mean().iloc[-1]
    trend5=df5["close"].iloc[-1] > df5["close"].rolling(20).mean().iloc[-1]

    body=abs(last["close"]-last["open"])

    # evitar mercado lateral
    if abs(last["ma9"]-last["ma21"]) < 0.00005:
        return None

    # evitar velas pequeñas
    if body < 0.0001:
        return None

    # señal CALL
    if trend15 and trend5 and last["ma9"]>last["ma21"] and last["rsi"]<35:
        return "CALL"

    # señal PUT
    if not trend15 and not trend5 and last["ma9"]<last["ma21"] and last["rsi"]>65:
        return "PUT"

    return None

print("BOT INICIADO")

while True:
    print("Analizando mercado...")

    for pair in pairs:
        print("Analizando:", pair)

        try:

            signal=analyze(pair)

            if signal:

                # alerta previa
                aviso = f"""
                ⚠️ POSIBLE SEÑAL

                Par: {pair}
                Prepararse para próxima vela
                """
                send_signal(aviso)

                time.sleep(20)

                message=f"""
                🚨 SEÑAL BINARIA

                Par: {pair}
                Dirección: {signal}
                Expiración: 3 minutos
                Entrada: próxima vela
                """

                send_signal(message)
        except:

            pass

    time.sleep(60)