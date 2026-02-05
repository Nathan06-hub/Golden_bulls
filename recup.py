import requests
import pandas as pd
import os
import time

# Dossier de données
DATA_DIR = "brvm_data"
if not os.path.exists(DATA_DIR):
    os.makedirs(DATA_DIR)

# Liste des tickers BRVM
TICKERS_BRVM_COMPLET = [
    # Banques
    "BOAB.bj", "BOABF.bf", "BOAM.ml", "BOAN.ne", "BOAS.sn",
    "BICC.ci", "BNBC.ci", "ECOC.ci", "ETIT.tg", "SGBC.ci", "SIBC.ci",

    # Industrie & Services
    "ABJC.ci", "CABC.ci", "CFAC.ci", "NEIC.ci", "NTLC.ci", "ONTBF.bf",
    "PALC.ci", "PRSC.ci", "SAFC.ci", "SCRC.ci", "SDCC.ci",
    "SIVC.ci", "SLBC.ci", "SMBC.ci", "SNTS.sn", "SOGC.ci",
    "SPHC.ci", "STAC.ci", "STBC.ci", "TTLS.sn",
    "UNLC.ci", "UNXC.ci",

    # Autres
    "CBIBF.bf", "FTSC.ci", "NSBC.ci", "ORGT.tg", "SHEC.ci"
]

# GUID à mettre à jour manuellement si nécessaire
GUID = "TON_GUID_ACTUEL"

def update_ticker(ticker, guid):
    path = os.path.join(DATA_DIR, f"{ticker}.csv")
    try:
        # Charger les anciennes données si elles existent
        if os.path.exists(path):
            df_old = pd.read_csv(path)
        else:
            df_old = pd.DataFrame()

        # Télécharger les nouvelles données
        url = f"https://www.sikafinance.com/api/charting/GetTicksEOD?symbol={ticker}&length=1825&period=0&guid={guid}"
        headers = {"User-Agent": "Mozilla/5.0", "Referer": "https://www.sikafinance.com/"}
        r = requests.get(url, headers=headers)
        if r.status_code != 200:
            print(f"❌ {ticker} : Erreur {r.status_code}")
            return
        data = r.json()
        if "QuoteTab" not in data or not data["QuoteTab"]:
            print(f"⚠️ {ticker} : Données absentes")
            return

        df_new = pd.DataFrame(data["QuoteTab"])

        # Ajouter uniquement les lignes nouvelles
        if not df_old.empty:
            last_date = df_old["d"].max()  # On reste avec 'd' pour date
            df_new = df_new[df_new["d"] > last_date]

        if df_new.empty:
            print(f"📥 {ticker} : pas de nouvelles lignes")
            return

        df_combined = pd.concat([df_old, df_new], ignore_index=True)
        df_combined.to_csv(path, index=False)
        print(f"📥 {ticker} mis à jour ({len(df_new)} nouvelles lignes)")

    except Exception as e:
        print(f"⚠️ {ticker} : {e}")

def main():
    print("🚀 Mise à jour BRVM en cours...")
    for ticker in TICKERS_BRVM_COMPLET:
        update_ticker(ticker, GUID)
        time.sleep(1)
    print("✅ Mise à jour terminée")

if __name__ == "__main__":
    main()
