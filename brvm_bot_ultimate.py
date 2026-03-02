#!/usr/bin/env python3
"""
brvm_bot_ultimate.py
Version corrigée + indicateurs avancés :
- RSI, MM20/MM50
- MACD (signal de croisement)
- Bandes de Bollinger (position relative)
- ATR (volatilité adaptative pour SL/TP)
- Volume ratio
- Scoring cohérent 0-10
"""

import os
import pandas as pd
import numpy as np
from pathlib import Path
from datetime import datetime

# ============================================================================
# CONFIGURATION
# ============================================================================

BASE_DIR = Path(__file__).parent
DATA_DIR = BASE_DIR / "brvm_data"
OUTPUT_DIR = BASE_DIR / "output"

CAPITAL = 1000000
STOP_LOSS_PCT = -5.0
TAKE_PROFIT_PCT = 10.0
POSITION_SIZE_PCT = 10.0

# ============================================================================
# CHARGEMENT DES DONNÉES
# ============================================================================

def load_brvm_data():
    print("=" * 80)
    print("📥 CHARGEMENT DES DONNÉES BRVM")
    print("=" * 80)

    if not DATA_DIR.exists():
        print(f"\n❌ Dossier introuvable: {DATA_DIR}")
        return None

    csv_files = list(DATA_DIR.glob("*.csv"))
    if not csv_files:
        print(f"\n❌ Aucun fichier CSV dans {DATA_DIR}")
        return None

    print(f"\n📂 {len(csv_files)} fichiers trouvés")
    all_data = []

    for csv_file in csv_files:
        try:
            df = pd.read_csv(csv_file)

            if not all(col in df.columns for col in ['d', 'c']):
                print(f"   ⚠️  {csv_file.name}: format incorrect, skip")
                continue

            ticker = csv_file.stem.split('.')[0].upper()

            standard_df = pd.DataFrame({
                'Date':   pd.to_datetime(df['d']),          # ✅ CORRECTION BUG DATE
                'Valeur': ticker,
                'Open':   df.get('o', df['c']),
                'High':   df.get('h', df['c']),
                'Low':    df.get('l', df['c']),
                'Close':  df['c'],
                'Volume': df.get('v', 0)
            })

            all_data.append(standard_df)
            print(f"   ✓ {ticker}: {len(standard_df)} points")

        except Exception as e:
            print(f"   ❌ {csv_file.name}: {e}")
            continue

    if not all_data:
        print("\n❌ Aucune donnée valide")
        return None

    merged = pd.concat(all_data, ignore_index=True)
    merged = merged.sort_values(['Valeur', 'Date'])

    print(f"\n✅ {len(merged):,} lignes | {merged['Valeur'].nunique()} entreprises")
    print(f"   Période: {merged['Date'].min().date()} → {merged['Date'].max().date()}")
    return merged


# ============================================================================
# INDICATEURS TECHNIQUES
# ============================================================================

def calculer_rsi(prices, period=14):
    """RSI classique"""
    delta = prices.diff()
    gain = delta.clip(lower=0).rolling(period).mean()
    loss = (-delta.clip(upper=0)).rolling(period).mean()
    rs = gain / loss
    return 100 - (100 / (1 + rs))


def calculer_moyennes_mobiles(prices):
    """MM20 et MM50"""
    return prices.rolling(20).mean(), prices.rolling(50).mean()


def calculer_macd(prices, fast=12, slow=26, signal=9):
    """
    MACD = EMA(12) - EMA(26)
    Signal = EMA(9) du MACD
    Histogramme = MACD - Signal
    
    Retourne : (macd_line, signal_line, histogram)
    """
    ema_fast = prices.ewm(span=fast, adjust=False).mean()
    ema_slow = prices.ewm(span=slow, adjust=False).mean()
    macd_line = ema_fast - ema_slow
    signal_line = macd_line.ewm(span=signal, adjust=False).mean()
    histogram = macd_line - signal_line
    return macd_line, signal_line, histogram


def calculer_bollinger(prices, period=20, nb_std=2):
    """
    Bandes de Bollinger
    
    Retourne : (bande_haute, moyenne, bande_basse, %B)
    %B = position du prix dans les bandes (0=bas, 1=haut, <0 ou >1 = hors bandes)
    """
    moyenne = prices.rolling(period).mean()
    std = prices.rolling(period).std()
    haute = moyenne + (nb_std * std)
    basse = moyenne - (nb_std * std)
    
    # %B : où se situe le prix dans les bandes
    pct_b = (prices - basse) / (haute - basse)
    
    return haute, moyenne, basse, pct_b


def calculer_atr(high, low, close, period=14):
    """
    ATR (Average True Range) — mesure la volatilité réelle
    
    Utilisé pour adapter les Stop Loss / Take Profit à la volatilité du titre
    """
    prev_close = close.shift(1)
    tr = pd.concat([
        high - low,
        (high - prev_close).abs(),
        (low - prev_close).abs()
    ], axis=1).max(axis=1)
    
    return tr.rolling(period).mean()


# ============================================================================
# SYSTÈME DE SCORING (0-10)
# ============================================================================

def calculer_score(rsi, mm20, mm50, prix, variation, volume_ratio,
                   macd_hist, pct_b):
    """
    Score cohérent basé sur 5 critères indépendants :
    
    1. RSI         (0 à 3 pts) : survente = opportunité
    2. Tendance MM (0 à 2 pts) : MM20 > MM50 + prix > MM20
    3. MACD        (0 à 2 pts) : croisement haussier
    4. Bollinger   (0 à 2 pts) : prix proche ou sous la bande basse
    5. Volume      (0 à 1 pt)  : volume élevé = signal plus fiable
    
    Pénalités : surachat RSI, forte baisse récente
    """
    score = 0

    # ── 1. RSI (max 3 pts) ──────────────────────────────────────────────────
    if pd.notna(rsi):
        if rsi < 30:
            score += 3    # Survente forte → excellente opportunité
        elif rsi < 40:
            score += 2    # Survente modérée
        elif rsi < 50:
            score += 1    # Légèrement sous la moyenne
        elif rsi > 70:
            score -= 2    # Surachat → pénalité

    # ── 2. Tendance MM (max 2 pts) ──────────────────────────────────────────
    if pd.notna(mm20) and pd.notna(mm50):
        if mm20 > mm50:
            score += 1    # Tendance haussière (golden cross)
        if pd.notna(prix) and prix > mm20:
            score += 1    # Prix au-dessus de la MM court terme

    # ── 3. MACD (max 2 pts) ─────────────────────────────────────────────────
    if pd.notna(macd_hist):
        if macd_hist > 0:
            score += 1    # Histogramme positif = momentum haussier
        # Bonus si l'histogramme est en train de monter (croisement récent)
        # (on ne peut pas calculer ça ici sans historique, voir analyser())

    # ── 4. Bollinger %B (max 2 pts) ─────────────────────────────────────────
    if pd.notna(pct_b):
        if pct_b < 0:
            score += 2    # Prix sous la bande basse → survente technique
        elif pct_b < 0.2:
            score += 1    # Prix proche de la bande basse

    # ── 5. Volume (max 1 pt) ────────────────────────────────────────────────
    if pd.notna(volume_ratio) and volume_ratio > 1.5:
        score += 1        # Volume anormalement élevé = signal plus fiable

    # ── Pénalité momentum baissier ──────────────────────────────────────────
    if variation < -5:
        score -= 1

    return max(0, min(10, score))


def generer_signal(score):
    if score >= 7:
        return "🔥 ACHAT FORT"
    elif score >= 5:
        return "✅ ACHAT"
    elif score >= 3:
        return "⚠️ SURVEILLER"
    else:
        return "❌ ATTENTE"


def expliquer_signal(row):
    """Explication lisible de chaque signal"""
    parts = []

    # RSI
    if row['RSI'] < 30:
        parts.append("🔥 RSI en survente forte (<30)")
    elif row['RSI'] < 40:
        parts.append("📉 RSI survendu (<40)")
    elif row['RSI'] > 70:
        parts.append("⚠️ RSI en surachat (>70)")

    # MACD
    if pd.notna(row.get('MACD_Hist')):
        if row['MACD_Hist'] > 0:
            parts.append("📈 MACD haussier")
        else:
            parts.append("📉 MACD baissier")

    # Bollinger
    if pd.notna(row.get('BB_PctB')):
        if row['BB_PctB'] < 0:
            parts.append("🎯 Prix sous la bande Bollinger basse (survente)")
        elif row['BB_PctB'] < 0.2:
            parts.append("📊 Prix proche de la bande Bollinger basse")
        elif row['BB_PctB'] > 0.8:
            parts.append("⚠️ Prix proche de la bande Bollinger haute")

    # Tendance
    if pd.notna(row['MM20']) and pd.notna(row['MM50']):
        if row['MM20'] > row['MM50']:
            parts.append("✅ Tendance haussière (MM20 > MM50)")
        else:
            parts.append("➡️ Tendance baissière (MM20 < MM50)")

    # Volatilité
    if pd.notna(row.get('ATR')):
        atr_pct = (row['ATR'] / row['Prix']) * 100
        if atr_pct > 3:
            parts.append(f"⚡ Titre volatil (ATR={atr_pct:.1f}%)")

    # Variation
    if row['Var_14j_%'] > 3:
        parts.append(f"🚀 Hausse récente (+{row['Var_14j_%']:.1f}%)")
    elif row['Var_14j_%'] < -5:
        parts.append(f"⬇️ Baisse récente ({row['Var_14j_%']:.1f}%)")

    if not parts:
        parts.append("➖ Pas de signal fort")

    return " | ".join(parts)


# ============================================================================
# ANALYSE PRINCIPALE
# ============================================================================

class AnalyseurBRVM:
    def __init__(self, capital=CAPITAL):
        self.capital = capital
        self.stop_loss_pct = STOP_LOSS_PCT
        self.take_profit_pct = TAKE_PROFIT_PCT
        self.position_size_pct = POSITION_SIZE_PCT

    def analyser(self, df):
        print("\n" + "=" * 80)
        print("🤖 ANALYSE TECHNIQUE BRVM")
        print("=" * 80)

        resultats = []

        for valeur in df['Valeur'].unique():
            data = df[df['Valeur'] == valeur].copy().sort_values('Date')

            # Minimum 60 points pour avoir tous les indicateurs (MACD slow=26 + signal=9 + marge)
            if len(data) < 60:
                continue

            close = data['Close']
            high  = data['High']
            low   = data['Low']
            prix  = close.iloc[-1]
            date  = data['Date'].iloc[-1]

            # ── Indicateurs ─────────────────────────────────────────────────
            rsi_s               = calculer_rsi(close, 14)
            mm20, mm50          = calculer_moyennes_mobiles(close)
            macd_l, macd_sig, macd_hist = calculer_macd(close)
            bb_h, bb_m, bb_l, pct_b     = calculer_bollinger(close)
            atr_s               = calculer_atr(high, low, close, 14)

            rsi_val      = rsi_s.iloc[-1]
            mm20_val     = mm20.iloc[-1]
            mm50_val     = mm50.iloc[-1]
            macd_hist_val = macd_hist.iloc[-1]
            pct_b_val    = pct_b.iloc[-1]
            atr_val      = atr_s.iloc[-1]

            # ── Variation 14j ────────────────────────────────────────────────
            variation = 0
            if len(data) >= 14:
                prix_14j  = close.iloc[-14]
                variation = ((prix - prix_14j) / prix_14j) * 100

            # ── Volume ratio ─────────────────────────────────────────────────
            vol_actuel = data['Volume'].iloc[-1]
            vol_moyen  = data['Volume'].tail(20).mean()
            vol_ratio  = (vol_actuel / vol_moyen) if vol_moyen > 0 else 1.0

            # ── Score & Signal ───────────────────────────────────────────────
            score  = calculer_score(rsi_val, mm20_val, mm50_val, prix,
                                    variation, vol_ratio, macd_hist_val, pct_b_val)
            signal = generer_signal(score)

            # ── Risk Management adaptatif (basé sur ATR) ─────────────────────
            # Si on a un ATR valide, on adapte le SL/TP à la volatilité réelle
            if pd.notna(atr_val) and atr_val > 0:
                stop_loss    = prix - (2.0 * atr_val)   # SL = 2x ATR sous le prix
                take_profit  = prix + (4.0 * atr_val)   # TP = 4x ATR au-dessus (ratio 1:2)
            else:
                stop_loss    = prix * (1 + self.stop_loss_pct / 100)
                take_profit  = prix * (1 + self.take_profit_pct / 100)

            trailing_stop = prix * 0.97

            # ── Position ─────────────────────────────────────────────────────
            position_size = self.capital * (self.position_size_pct / 100)
            nb_actions    = int(position_size / prix)
            montant       = nb_actions * prix

            gain_potentiel   = (take_profit - prix) * nb_actions
            perte_potentielle = (prix - stop_loss) * nb_actions
            ratio_rr = abs(gain_potentiel / perte_potentielle) if perte_potentielle > 0 else 0

            resultats.append({
                'Valeur':           valeur,
                'Prix':             prix,
                'RSI':              round(rsi_val, 1) if pd.notna(rsi_val) else 0,
                'MM20':             round(mm20_val, 0) if pd.notna(mm20_val) else 0,
                'MM50':             round(mm50_val, 0) if pd.notna(mm50_val) else 0,
                'MACD_Hist':        round(macd_hist_val, 2) if pd.notna(macd_hist_val) else 0,
                'BB_PctB':          round(pct_b_val, 3) if pd.notna(pct_b_val) else 0.5,
                'ATR':              round(atr_val, 0) if pd.notna(atr_val) else 0,
                'Volume_Ratio':     round(vol_ratio, 2),
                'Var_14j_%':        round(variation, 2),
                'Score':            score,
                'Signal':           signal,
                'Stop_Loss':        round(stop_loss, 0),
                'Take_Profit':      round(take_profit, 0),
                'Trailing_Stop':    round(trailing_stop, 0),
                'Nb_Actions':       nb_actions,
                'Montant_FCFA':     round(montant, 0),
                'Gain_Potentiel':   round(gain_potentiel, 0),
                'Perte_Potentielle':round(perte_potentielle, 0),
                'Ratio_RR':         round(ratio_rr, 2),
                'Date_Analyse':     date.date()
            })

        results_df = pd.DataFrame(resultats).sort_values('Score', ascending=False)
        print(f"✅ {len(results_df)} entreprises analysées")
        return results_df

    def afficher_opportunites(self, df, top_n=10):
        print(f"\n🏆 TOP {top_n} OPPORTUNITÉS\n" + "=" * 80)

        for _, row in df.head(top_n).iterrows():
            atr_pct = (row['ATR'] / row['Prix'] * 100) if row['Prix'] > 0 else 0
            print(f"\n{row['Signal']} — {row['Valeur']}  |  Score: {row['Score']}/10")
            print(f"   💰 Prix: {row['Prix']:,.0f} FCFA  |  Var 14j: {row['Var_14j_%']:+.2f}%")
            print(f"   📊 RSI: {row['RSI']:.1f}  |  MACD hist: {row['MACD_Hist']:+.2f}  |  BB%B: {row['BB_PctB']:.2f}")
            print(f"   📈 MM20: {row['MM20']:,.0f}  |  MM50: {row['MM50']:,.0f}")
            print(f"   ⚡ ATR: {row['ATR']:,.0f} FCFA ({atr_pct:.1f}%)  |  Volume x{row['Volume_Ratio']:.1f}")
            print(f"   💡 {expliquer_signal(row)}")
            print(f"   🛡️ SL: {row['Stop_Loss']:,.0f}  |  TP: {row['Take_Profit']:,.0f}  |  R/R: {row['Ratio_RR']:.2f}x")
            print(f"   💵 {row['Nb_Actions']} actions = {row['Montant_FCFA']:,.0f} FCFA")

    def exporter_excel(self, df):
        OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
        output_file = OUTPUT_DIR / "BRVM_ANALYSE_COMPLETE.xlsx"

        with pd.ExcelWriter(output_file, engine='openpyxl') as writer:
            df.to_excel(writer, sheet_name='Classement Complet', index=False)
            df[df['Signal'].str.contains('ACHAT', na=False)].to_excel(
                writer, sheet_name='Opportunités', index=False)
            df[df['Signal'] == '⚠️ SURVEILLER'].to_excel(
                writer, sheet_name='À Surveiller', index=False)

            stats = pd.DataFrame({
                'Métrique': [
                    'Date analyse', 'Entreprises analysées',
                    'ACHAT FORT', 'ACHAT', 'Surveiller', 'Attente',
                    'Capital (FCFA)', 'RSI moyen', 'Score moyen', 'Meilleure opportunité'
                ],
                'Valeur': [
                    datetime.now().strftime('%Y-%m-%d %H:%M'),
                    len(df),
                    len(df[df['Signal'] == '🔥 ACHAT FORT']),
                    len(df[df['Signal'] == '✅ ACHAT']),
                    len(df[df['Signal'] == '⚠️ SURVEILLER']),
                    len(df[df['Signal'] == '❌ ATTENTE']),
                    f"{self.capital:,}",
                    f"{df['RSI'].mean():.1f}",
                    f"{df['Score'].mean():.1f}/10",
                    df.iloc[0]['Valeur'] if len(df) > 0 else 'N/A'
                ]
            })
            stats.to_excel(writer, sheet_name='Statistiques', index=False)

        print(f"✅ Excel exporté : {output_file}")


# ============================================================================
# MAIN
# ============================================================================

def main():
    print("=" * 80)
    print("🚀 BRVM BOT ULTIMATE")
    print(f"📅 {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 80)

    df = load_brvm_data()
    if df is None or len(df) == 0:
        print("❌ Pas de données")
        return

    analyseur = AnalyseurBRVM(capital=CAPITAL)
    resultats = analyseur.analyser(df)

    if resultats is None or len(resultats) == 0:
        print("❌ Aucun résultat")
        return

    analyseur.afficher_opportunites(resultats, top_n=10)
    analyseur.exporter_excel(resultats)

    print("\n✅ ANALYSE TERMINÉE")


if __name__ == "__main__":
    main()
