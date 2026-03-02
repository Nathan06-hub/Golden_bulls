"""
recup.py - Mise à jour données BRVM
GUID chargé depuis guid.txt + détection expiration
"""
import requests
import pandas as pd
import os, sys, time
from datetime import datetime

DATA_DIR = "brvm_data"
GUID_FILE = "guid.txt"

TICKERS_BRVM = [
    "BOAB.bj", "BOABF.bf", "BOAM.ml", "BOAN.ne", "BOAS.sn",
    "BICC.ci", "BNBC.ci", "ECOC.ci", "ETIT.tg", "SGBC.ci", "SIBC.ci",
    "ABJC.ci", "CABC.ci", "CFAC.ci", "NEIC.ci", "NTLC.ci", "ONTBF.bf",
    "PALC.ci", "PRSC.ci", "SAFC.ci", "SCRC.ci", "SDCC.ci",
    "SIVC.ci", "SLBC.ci", "SMBC.ci", "SNTS.sn", "SOGC.ci",
    "SPHC.ci", "STAC.ci", "STBC.ci", "TTLS.sn",
    "UNLC.ci", "UNXC.ci", "CBIBF.bf", "FTSC.ci", "NSBC.ci", "ORGT.tg", "SHEC.ci"
]

def charger_guid():
    """
    Charge le GUID depuis guid.txt.
    
    Pour obtenir un GUID valide :
    1. Ouvre https://www.sikafinance.com dans Chrome
    2. F12 → onglet Network (Réseau)
    3. Tape le nom d'une action dans la recherche
    4. Dans les requêtes, trouve 'GetTicksEOD'
    5. Copie la valeur du paramètre 'guid' dans l'URL
    6. Colle-la dans guid.txt
    """
    if not os.path.exists(GUID_FILE):
        print(f"❌ Fichier '{GUID_FILE}' introuvable !")
        print("   Crée un fichier guid.txt à la racine du projet")
        print("   et colle ton GUID dedans (voir instructions ci-dessus)")
        sys.exit(1)
    
    with open(GUID_FILE) as f:
        guid = f.read().strip()
    
    if not guid or "COLLE" in guid.upper():
        print("❌ GUID vide ou non rempli dans guid.txt")
        sys.exit(1)
    
    return guid

def tester_guid(guid):
    """Vérifie que le GUID est encore valide"""
    print("🔑 Test du GUID...")
    url = f"https://www.sikafinance.com/api/charting/GetTicksEOD?symbol=SNTS.sn&length=5&period=0&guid={guid}"
    headers = {"User-Agent": "Mozilla/5.0", "Referer": "https://www.sikafinance.com/"}
    
    try:
        r = requests.get(url, headers=headers, timeout=10)
        if r.status_code in (401, 403):
            print("❌ GUID expiré — renouvelle-le dans guid.txt")
            return False
        data = r.json()
        if "QuoteTab" not in data or not data["QuoteTab"]:
            print("❌ GUID invalide — aucune donnée reçue")
            return False
        print("✅ GUID valide !")
        return True
    except Exception as e:
        print(f"❌ Erreur de connexion : {e}")
        return False

def update_ticker(ticker, guid):
    path = os.path.join(DATA_DIR, f"{ticker}.csv")
    
    try:
        df_old = pd.DataFrame()
        if os.path.exists(path):
            df_old = pd.read_csv(path)
            df_old["d"] = pd.to_datetime(df_old["d"])  # ✅ CORRECTION BUG DATE
        
        url = f"https://www.sikafinance.com/api/charting/GetTicksEOD?symbol={ticker}&length=1825&period=0&guid={guid}"
        headers = {"User-Agent": "Mozilla/5.0", "Referer": "https://www.sikafinance.com/"}
        r = requests.get(url, headers=headers, timeout=15)
        
        if r.status_code in (401, 403):
            return "guid_expired"
        if r.status_code != 200:
            print(f"❌ {ticker} : HTTP {r.status_code}")
            return "error"
        
        data = r.json()
        if "QuoteTab" not in data or not data["QuoteTab"]:
            print(f"⚠️  {ticker} : pas de données")
            return "no_data"
        
        df_new = pd.DataFrame(data["QuoteTab"])
        df_new["d"] = pd.to_datetime(df_new["d"])  # ✅ CORRECTION BUG DATE
        
        if not df_old.empty:
            last_date = df_old["d"].max()
            df_new = df_new[df_new["d"] > last_date]
        
        if df_new.empty:
            print(f"   {ticker} : déjà à jour")
            return "up_to_date"
        
        df_combined = pd.concat([df_old, df_new]).sort_values("d")
        df_combined.to_csv(path, index=False)
        print(f"📥 {ticker} : +{len(df_new)} lignes")
        return "updated"
    
    except Exception as e:
        print(f"⚠️  {ticker} : {e}")
        return "error"

def main():
    print("=" * 60)
    print(f"🚀 Mise à jour BRVM — {datetime.now().strftime('%Y-%m-%d %H:%M')}")
    print("=" * 60)
    
    os.makedirs(DATA_DIR, exist_ok=True)
    guid = charger_guid()
    
    if not tester_guid(guid):
        sys.exit(1)
    
    stats = {"updated": 0, "up_to_date": 0, "error": 0, "no_data": 0}
    
    for ticker in TICKERS_BRVM:
        result = update_ticker(ticker, guid)
        if result == "guid_expired":
            print("\n🛑 GUID expiré — relance après renouvellement dans guid.txt")
            break
        stats[result] = stats.get(result, 0) + 1
        time.sleep(1)
    
    print(f"\n✅ Terminé | Mis à jour: {stats['updated']} | Déjà OK: {stats['up_to_date']} | Erreurs: {stats['error']}")

if __name__ == "__main__":
    main()
