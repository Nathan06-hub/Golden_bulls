#!/usr/bin/env python3
"""
brvm_bot_ultimate.py
Version hybride optimale :
- Utilise les vraies données BRVM (format SikaFinance)
- Analyse technique avancée avec scoring 0-10
- Explications détaillées et pédagogiques
- Calcul des positions et risk management
- Export Excel professionnel
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

CAPITAL = 1000000  # Capital disponible en FCFA
STOP_LOSS_PCT = -5.0  # Stop Loss à -5%
TAKE_PROFIT_PCT = 10.0  # Take Profit à +10%
POSITION_SIZE_PCT = 10.0  # 10% du capital par position

# ============================================================================
# CHARGEMENT DES DONNÉES
# ============================================================================

def load_brvm_data():
    """Charge toutes les données BRVM depuis brvm_data/"""
    print("=" * 80)
    print("📥 CHARGEMENT DES DONNÉES BRVM")
    print("=" * 80)
    
    if not DATA_DIR.exists():
        print(f"\n❌ Dossier de données introuvable: {DATA_DIR}")
        print("💡 Assure-toi que brvm_data/ contient les fichiers CSV")
        return None
    
    csv_files = list(DATA_DIR.glob("*.csv"))
    
    if not csv_files:
        print(f"\n❌ Aucun fichier CSV trouvé dans {DATA_DIR}")
        return None
    
    print(f"\n📂 {len(csv_files)} fichiers trouvés")
    
    all_data = []
    
    for csv_file in csv_files:
        try:
            # Lire le CSV
            df = pd.read_csv(csv_file)
            
            # Vérifier le format (colonnes: d, o, h, l, c, v)
            if not all(col in df.columns for col in ['d', 'c']):
                print(f"   ⚠️  {csv_file.name}: format incorrect, skip")
                continue
            
            # Extraire le ticker du nom de fichier (ex: SNTS.sn.csv -> SNTS)
            ticker = csv_file.stem.split('.')[0].upper()
            
            # Standardiser les colonnes
            standard_df = pd.DataFrame({
                'Date': pd.to_datetime(df['d'], unit='D', origin='1900-01-01'),
                'Valeur': ticker,
                'Open': df['o'] if 'o' in df.columns else df['c'],
                'High': df['h'] if 'h' in df.columns else df['c'],
                'Low': df['l'] if 'l' in df.columns else df['c'],
                'Close': df['c'],
                'Volume': df['v'] if 'v' in df.columns else 0
            })
            
            all_data.append(standard_df)
            print(f"   ✓ {ticker}: {len(standard_df)} points")
            
        except Exception as e:
            print(f"   ❌ {csv_file.name}: Erreur - {e}")
            continue
    
    if not all_data:
        print("\n❌ Aucune donnée valide chargée")
        return None
    
    # Fusionner tout
    merged_df = pd.concat(all_data, ignore_index=True)
    merged_df = merged_df.sort_values(['Valeur', 'Date'])
    
    print(f"\n✅ Données chargées avec succès")
    print(f"   • Total lignes: {len(merged_df):,}")
    print(f"   • Entreprises: {merged_df['Valeur'].nunique()}")
    print(f"   • Période: {merged_df['Date'].min().date()} → {merged_df['Date'].max().date()}")
    
    return merged_df


# ============================================================================
# INDICATEURS TECHNIQUES
# ============================================================================

def calculer_rsi(prices, period=14):
    """Calcule le RSI (Relative Strength Index)"""
    delta = prices.diff()
    gain = delta.clip(lower=0)
    loss = -delta.clip(upper=0)
    
    avg_gain = gain.rolling(window=period).mean()
    avg_loss = loss.rolling(window=period).mean()
    
    rs = avg_gain / avg_loss
    rsi = 100 - (100 / (1 + rs))
    
    return rsi


def calculer_moyennes_mobiles(prices):
    """Calcule les moyennes mobiles"""
    mm20 = prices.rolling(window=20).mean()
    mm50 = prices.rolling(window=50).mean()
    return mm20, mm50


# ============================================================================
# SYSTÈME DE SCORING
# ============================================================================

def calculer_score(rsi, mm20, mm50, prix, variation):
    """
    Calcule un score de 0 à 10 basé sur plusieurs critères
    
    Critères:
    - RSI < 30 = +3 pts (survente forte)
    - RSI < 40 = +2 pts (survente modérée)
    - RSI < 50 = +1 pt (légèrement survendu)
    
    - MM20 > MM50 = +2 pts (tendance haussière)
    - Prix > MM20 = +1 pt (au-dessus de la moyenne)
    
    - Variation > 5% = +3 pts (forte hausse)
    - Variation > 2% = +2 pts (hausse modérée)
    - Variation > 0% = +1 pt (hausse légère)
    - Variation < -5% = -1 pt (forte baisse)
    """
    score = 0
    
    # Critère RSI (0-3 points)
    if pd.notna(rsi):
        if rsi < 30:
            score += 3
        elif rsi < 40:
            score += 2
        elif rsi < 50:
            score += 1
    
    # Critère moyennes mobiles (0-3 points)
    if pd.notna(mm20) and pd.notna(mm50):
        if mm20 > mm50:
            score += 2
        if prix > mm20:
            score += 1
    
    # Critère variation (0-4 points)
    if variation > 5:
        score += 3
    elif variation > 2:
        score += 2
    elif variation > 0:
        score += 1
    elif variation < -5:
        score -= 1
    
    return max(0, min(10, score))


def generer_signal(score):
    """Génère un signal d'achat basé sur le score"""
    if score >= 7:
        return "🔥 ACHAT FORT"
    elif score >= 5:
        return "✅ ACHAT"
    elif score >= 3:
        return "⚠️ SURVEILLER"
    else:
        return "❌ ATTENTE"


def expliquer_signal(row):
    """Génère une explication détaillée du signal"""
    explications = []
    
    # Explication RSI
    if row['RSI'] < 30:
        explications.append("🔥 RSI très bas (survente forte) - excellente opportunité")
    elif row['RSI'] < 40:
        explications.append("📉 RSI bas (survente modérée) - bonne opportunité")
    elif row['RSI'] > 70:
        explications.append("⚠️ RSI élevé (surachat) - risque de correction")
    
    # Explication tendance
    if pd.notna(row['MM20']) and pd.notna(row['MM50']):
        if row['MM20'] > row['MM50']:
            explications.append("📈 Tendance haussière confirmée (MM20 > MM50)")
        else:
            explications.append("📉 Tendance baissière ou neutre (MM20 < MM50)")
    
    # Explication variation
    if row['Var_14j_%'] > 5:
        explications.append(f"🚀 Forte hausse récente (+{row['Var_14j_%']:.1f}%)")
    elif row['Var_14j_%'] > 2:
        explications.append(f"⬆️ Hausse modérée (+{row['Var_14j_%']:.1f}%)")
    elif row['Var_14j_%'] < -5:
        explications.append(f"⬇️ Forte baisse récente ({row['Var_14j_%']:.1f}%)")
    
    if not explications:
        explications.append("➖ Marché neutre - pas de signal fort")
    
    return " | ".join(explications)


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
        """Analyse toutes les entreprises"""
        print("\n" + "=" * 80)
        print("🤖 ANALYSE TECHNIQUE BRVM")
        print("=" * 80)
        print(f"💰 Capital: {self.capital:,} FCFA")
        print(f"📉 Stop Loss: {self.stop_loss_pct}%")
        print(f"📈 Take Profit: {self.take_profit_pct}%")
        print(f"💼 Taille position: {self.position_size_pct}% du capital")
        
        print(f"\n📊 Calcul des indicateurs techniques...")
        
        resultats = []
        
        for valeur in df['Valeur'].unique():
            valeur_data = df[df['Valeur'] == valeur].copy()
            valeur_data = valeur_data.sort_values('Date')
            
            # Besoin d'au moins 50 points pour calculer les indicateurs
            if len(valeur_data) < 50:
                continue
            
            # Prix actuel
            prix_actuel = valeur_data['Close'].iloc[-1]
            date_actuelle = valeur_data['Date'].iloc[-1]
            
            # Calcul des indicateurs
            rsi = calculer_rsi(valeur_data['Close'], 14)
            mm20, mm50 = calculer_moyennes_mobiles(valeur_data['Close'])
            
            rsi_actuel = rsi.iloc[-1]
            mm20_actuel = mm20.iloc[-1]
            mm50_actuel = mm50.iloc[-1]
            
            # Variation sur 14 jours
            if len(valeur_data) >= 14:
                prix_14j = valeur_data['Close'].iloc[-14]
                variation = ((prix_actuel - prix_14j) / prix_14j) * 100
            else:
                variation = 0
            
            # Calcul du score
            score = calculer_score(rsi_actuel, mm20_actuel, mm50_actuel, 
                                  prix_actuel, variation)
            
            # Signal
            signal = generer_signal(score)
            
            # Risk Management
            stop_loss = prix_actuel * (1 + self.stop_loss_pct / 100)
            take_profit = prix_actuel * (1 + self.take_profit_pct / 100)
            trailing_stop = prix_actuel * 0.97  # -3% trailing
            
            # Calcul de la position
            position_size = self.capital * (self.position_size_pct / 100)
            nb_actions = int(position_size / prix_actuel)
            montant = nb_actions * prix_actuel
            
            # Potentiel de gain/perte
            gain_potentiel = (take_profit - prix_actuel) * nb_actions
            perte_potentielle = (prix_actuel - stop_loss) * nb_actions
            ratio_risk_reward = abs(gain_potentiel / perte_potentielle) if perte_potentielle != 0 else 0
            
            resultats.append({
                'Valeur': valeur,
                'Prix': prix_actuel,
                'RSI': round(rsi_actuel, 1) if pd.notna(rsi_actuel) else 0,
                'MM20': round(mm20_actuel, 0) if pd.notna(mm20_actuel) else 0,
                'MM50': round(mm50_actuel, 0) if pd.notna(mm50_actuel) else 0,
                'Var_14j_%': round(variation, 2),
                'Score': score,
                'Signal': signal,
                'Stop_Loss': round(stop_loss, 0),
                'Take_Profit': round(take_profit, 0),
                'Trailing_Stop': round(trailing_stop, 0),
                'Nb_Actions': nb_actions,
                'Montant_FCFA': round(montant, 0),
                'Gain_Potentiel': round(gain_potentiel, 0),
                'Perte_Potentielle': round(perte_potentielle, 0),
                'Ratio_RR': round(ratio_risk_reward, 2),
                'Date_Analyse': date_actuelle.date()
            })
        
        results_df = pd.DataFrame(resultats)
        results_df = results_df.sort_values('Score', ascending=False)
        
        print(f"✅ {len(results_df)} entreprises analysées")
        
        return results_df
    
    def afficher_opportunites(self, df, top_n=10):
        """Affiche les meilleures opportunités"""
        print("\n" + "=" * 80)
        print(f"🏆 TOP {top_n} OPPORTUNITÉS D'ACHAT")
        print("=" * 80)
        
        # Statistiques
        achats_forts = len(df[df['Signal'] == '🔥 ACHAT FORT'])
        achats = len(df[df['Signal'] == '✅ ACHAT'])
        surveiller = len(df[df['Signal'] == '⚠️ SURVEILLER'])
        
        print(f"\n📊 Résumé des signaux:")
        print(f"   • {achats_forts} signaux ACHAT FORT 🔥")
        print(f"   • {achats} signaux ACHAT ✅")
        print(f"   • {surveiller} à surveiller ⚠️")
        
        print(f"\n🎯 TOP {top_n} PAR SCORE:\n")
        
        for idx, row in df.head(top_n).iterrows():
            print(f"{row['Signal']} - {row['Valeur']}")
            print(f"   💰 Prix actuel: {row['Prix']:,.0f} FCFA")
            print(f"   📊 Score: {row['Score']}/10 | RSI: {row['RSI']:.1f} | Variation 14j: {row['Var_14j_%']:+.2f}%")
            
            # Explication détaillée
            explication = expliquer_signal(row)
            print(f"   💡 {explication}")
            
            # Risk Management
            print(f"   🛡️ Stop Loss: {row['Stop_Loss']:,.0f} FCFA ({self.stop_loss_pct}%)")
            print(f"   🎯 Take Profit: {row['Take_Profit']:,.0f} FCFA (+{self.take_profit_pct}%)")
            print(f"   📉 Trailing Stop: {row['Trailing_Stop']:,.0f} FCFA (-3%)")
            
            # Position recommandée
            print(f"   💵 Position recommandée: {row['Nb_Actions']} actions = {row['Montant_FCFA']:,.0f} FCFA")
            print(f"   📈 Gain potentiel: +{row['Gain_Potentiel']:,.0f} FCFA")
            print(f"   📉 Perte potentielle: {row['Perte_Potentielle']:,.0f} FCFA")
            print(f"   ⚖️ Ratio Risk/Reward: {row['Ratio_RR']:.2f}\n")
    
    def exporter_excel(self, df):
        """Exporte les résultats vers Excel"""
        OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
        output_file = OUTPUT_DIR / "BRVM_ANALYSE_COMPLETE.xlsx"
        
        print(f"\n💾 Export Excel: {output_file}")
        
        with pd.ExcelWriter(output_file, engine='openpyxl') as writer:
            # Feuille 1: Classement complet
            df.to_excel(writer, sheet_name='Classement Complet', index=False)
            
            # Feuille 2: Opportunités (ACHAT FORT + ACHAT)
            opportunites = df[df['Signal'].str.contains('ACHAT', na=False)]
            opportunites.to_excel(writer, sheet_name='Opportunités', index=False)
            
            # Feuille 3: À surveiller
            surveiller = df[df['Signal'] == '⚠️ SURVEILLER']
            surveiller.to_excel(writer, sheet_name='À Surveiller', index=False)
            
            # Feuille 4: Statistiques
            stats = pd.DataFrame({
                'Métrique': [
                    'Date analyse',
                    'Total entreprises analysées',
                    'Signaux ACHAT FORT',
                    'Signaux ACHAT',
                    'À surveiller',
                    'Attente',
                    'Capital disponible (FCFA)',
                    'Prix moyen marché',
                    'RSI moyen',
                    'Score moyen',
                    'Meilleure opportunité',
                    'Score max'
                ],
                'Valeur': [
                    datetime.now().strftime('%Y-%m-%d %H:%M'),
                    len(df),
                    len(df[df['Signal'] == '🔥 ACHAT FORT']),
                    len(df[df['Signal'] == '✅ ACHAT']),
                    len(df[df['Signal'] == '⚠️ SURVEILLER']),
                    len(df[df['Signal'] == '❌ ATTENTE']),
                    f"{self.capital:,}",
                    f"{df['Prix'].mean():,.0f} FCFA",
                    f"{df['RSI'].mean():.1f}",
                    f"{df['Score'].mean():.1f}/10",
                    df.iloc[0]['Valeur'] if len(df) > 0 else 'N/A',
                    f"{df['Score'].max()}/10" if len(df) > 0 else 'N/A'
                ]
            })
            stats.to_excel(writer, sheet_name='Statistiques', index=False)
        
        print(f"✅ Fichier Excel créé avec succès!")
        print(f"\n📱 Pour récupérer sur mobile:")
        print(f"   cp {output_file} /sdcard/Download/")


# ============================================================================
# PROGRAMME PRINCIPAL
# ============================================================================

def main():
    print("=" * 80)
    print("🚀 BRVM BOT ULTIMATE - Analyse Technique Avancée")
    print("=" * 80)
    print(f"📅 Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # 1. Charger les données
    df = load_brvm_data()
    
    if df is None or len(df) == 0:
        print("\n❌ Impossible de charger les données")
        print("\n💡 Assure-toi que:")
        print("   1. Le dossier brvm_data/ existe")
        print("   2. Il contient des fichiers CSV au format SikaFinance")
        print("   3. Les fichiers ont les colonnes: d, c (minimum)")
        return
    
    # 2. Analyser
    analyseur = AnalyseurBRVM(capital=CAPITAL)
    resultats = analyseur.analyser(df)
    
    if resultats is None or len(resultats) == 0:
        print("\n❌ Aucun résultat d'analyse")
        return
    
    # 3. Afficher les opportunités
    analyseur.afficher_opportunites(resultats, top_n=10)
    
    # 4. Exporter vers Excel
    analyseur.exporter_excel(resultats)
    
    print("\n" + "=" * 80)
    print("✅ ANALYSE TERMINÉE AVEC SUCCÈS!")
    print("=" * 80)
    print("\n💡 Prochaines étapes:")
    print("   1. Consulte le fichier Excel pour voir toutes les opportunités")
    print("   2. Vérifie les explications détaillées de chaque signal")
    print("   3. Applique le risk management (Stop Loss / Take Profit)")


if __name__ == "__main__":
    main()
