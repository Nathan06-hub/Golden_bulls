import os
import pandas as pd
import numpy as np

# =========================
# CONFIG
# =========================

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(BASE_DIR, "brvm_data")

TOP_N = 15  # top 10 / 20 possible

# =========================
# INDICATEURS
# =========================

def compute_rsi(series, period=14):
    delta = series.diff()
    gain = delta.clip(lower=0)
    loss = -delta.clip(upper=0)

    avg_gain = gain.rolling(period).mean()
    avg_loss = loss.rolling(period).mean()

    rs = avg_gain / avg_loss
    rsi = 100 - (100 / (1 + rs))
    return rsi

# =========================
# LOAD & MERGE
# =========================

def load_data():
    frames = []

    for file in os.listdir(DATA_DIR):
        if file.endswith(".csv"):
            df = pd.read_csv(os.path.join(DATA_DIR, file))
            df.columns = ["date", "open", "high", "low", "close", "volume"]
            df["ticker"] = file.replace(".csv", "")
            frames.append(df)

    return pd.concat(frames, ignore_index=True)

# =========================
# ANALYSE AVANCÉE
# =========================

def analyse(df):
    results = []

    for ticker, data in df.groupby("ticker"):
        data = data.sort_values("date")

        data["MA20"] = data["close"].rolling(20).mean()
        data["MA50"] = data["close"].rolling(50).mean()
        data["RSI"] = compute_rsi(data["close"])

        last = data.iloc[-1]

        price = last["close"]
        rsi = last["RSI"]
        ma20 = last["MA20"]
        ma50 = last["MA50"]

        # === SIGNAL ===
        if rsi < 30 and ma20 > ma50:
            signal = "BUY"
            reason = "RSI survendu + tendance haussière"
        elif rsi > 70:
            signal = "SELL"
            reason = "RSI suracheté"
        else:
            signal = "HOLD"
            reason = "Marché neutre"

        # === RISK MANAGEMENT ===
        stop_loss = price * 0.95
        take_profit = price * 1.10
        trailing_sl = price * 0.97

        results.append({
            "Ticker": ticker,
            "Prix": round(price, 2),
            "RSI": round(rsi, 2),
            "MA20": round(ma20, 2),
            "MA50": round(ma50, 2),
            "Signal": signal,
            "Stop Loss": round(stop_loss, 2),
            "Take Profit": round(take_profit, 2),
            "Trailing SL": round(trailing_sl, 2),
            "Pourquoi": reason
        })

    return pd.DataFrame(results)

# =========================
# MAIN
# =========================

def main():
    print("📥 Chargement des données BRVM...")
    df = load_data()

    print("📊 Analyse avancée...")
    analysis = analyse(df)

    # Classement par opportunité
    top = analysis.sort_values(
        by=["Signal", "RSI"],
        ascending=[True, True]
    ).head(TOP_N)

    print(f"\n🏆 TOP {TOP_N} OPPORTUNITÉS BRVM\n")
    print(top)

    # Export
    output = os.path.join(BASE_DIR, "BRVM_TOP_OPPORTUNITES.csv")
    top.to_csv(output, index=False)
    print(f"\n💾 Exporté vers {output}")

# =========================
# RUN
# =========================

if __name__ == "__main__":
    main()
