"""
app.py
Interface web Streamlit pour BRVM Bot Ultimate
Version mise à jour avec MACD, Bollinger, ATR, Volume
"""

import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import plotly.express as px
from pathlib import Path
from datetime import datetime
import sys

sys.path.insert(0, str(Path(__file__).parent))

from brvm_bot_ultimate import (
    load_brvm_data,
    AnalyseurBRVM,
    expliquer_signal,
    calculer_rsi,
    calculer_moyennes_mobiles,
    calculer_macd,
    calculer_bollinger,
    calculer_atr
)

# ============================================================================
# CONFIG PAGE
# ============================================================================

st.set_page_config(
    page_title="BRVM Bot Ultimate",
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="expanded"
)

st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        font-weight: bold;
        color: #1f77b4;
        text-align: center;
        margin-bottom: 2rem;
    }
</style>
""", unsafe_allow_html=True)

# ============================================================================
# CHARGEMENT
# ============================================================================

@st.cache_data(ttl=3600)
def charger_donnees(capital):
    df = load_brvm_data()
    if df is None:
        return None, None
    analyseur = AnalyseurBRVM(capital=capital)
    resultats = analyseur.analyser(df)
    return df, resultats

# ============================================================================
# SIDEBAR
# ============================================================================

with st.sidebar:
    st.markdown("### ⚙️ Configuration")

    capital = st.number_input(
        "💰 Capital disponible (FCFA)",
        min_value=1000000, max_value=100000000,
        value=20000000, step=1000000, format="%d"
    )

    st.markdown("---")
    st.markdown("### 📊 Filtres")

    signal_filter = st.multiselect(
        "Filtrer par signal",
        ["🔥 ACHAT FORT", "✅ ACHAT", "⚠️ SURVEILLER", "❌ ATTENTE"],
        default=["🔥 ACHAT FORT", "✅ ACHAT"]
    )

    score_min = st.slider("Score minimum", 0, 10, 0)

    st.markdown("---")
    st.markdown("### ℹ️ À propos")
    st.info("**BRVM Bot Ultimate**\n\nAnalyse technique avancée de la BRVM.\n\nDéveloppé par **Les Bullionaires** 🏆")

# ============================================================================
# CHARGEMENT DES DONNÉES
# ============================================================================

df_raw, df_analysis = charger_donnees(capital)

if df_raw is None or df_analysis is None:
    st.error("❌ Impossible de charger les données. Vérifie que brvm_data/ contient des fichiers CSV.")
    st.stop()

if signal_filter:
    df_filtered = df_analysis[df_analysis['Signal'].isin(signal_filter)]
else:
    df_filtered = df_analysis

df_filtered = df_filtered[df_filtered['Score'] >= score_min]

# ============================================================================
# HEADER
# ============================================================================

st.markdown('<p class="main-header">📈 BRVM Bot Ultimate</p>', unsafe_allow_html=True)
st.markdown(
    f"<p style='text-align:center;color:gray;'>Dernière mise à jour : {datetime.now().strftime('%d/%m/%Y %H:%M')}</p>",
    unsafe_allow_html=True
)

# ============================================================================
# MÉTRIQUES PRINCIPALES
# ============================================================================

col1, col2, col3, col4 = st.columns(4)

with col1:
    st.metric("🏢 Entreprises analysées", len(df_analysis))

with col2:
    achats_forts = len(df_analysis[df_analysis['Signal'] == '🔥 ACHAT FORT'])
    st.metric("🔥 ACHAT FORT", achats_forts,
              delta=f"{achats_forts/len(df_analysis)*100:.1f}%")

with col3:
    st.metric("💰 Prix moyen", f"{df_analysis['Prix'].mean():,.0f} FCFA")

with col4:
    rsi_moyen = df_analysis['RSI'].mean()
    label = "Neutre" if 40 <= rsi_moyen <= 60 else ("Survendu" if rsi_moyen < 40 else "Surachat")
    st.metric("📊 RSI moyen", f"{rsi_moyen:.1f}", delta=label)

st.markdown("---")

# ============================================================================
# ONGLETS
# ============================================================================

tab1, tab2, tab3, tab4, tab5 = st.tabs([
    "🏆 Top Opportunités",
    "📊 Analyse Détaillée",
    "📈 Graphiques",
    "💼 Simulateur",
    "🔄 Mise à jour"
])

# ============================================================================
# TAB 1 : TOP OPPORTUNITÉS
# ============================================================================

with tab1:
    st.markdown("### 🏆 Meilleures Opportunités")

    top_n = st.slider("Nombre d'opportunités", 5, 20, 10)

    for i, (idx, row) in enumerate(df_filtered.head(top_n).iterrows()):
        with st.expander(
            f"**{row['Signal']} — {row['Valeur']}** | Score: {row['Score']}/10",
            expanded=(i < 3)
        ):
            col1, col2, col3 = st.columns(3)

            with col1:
                st.markdown("#### 💰 Prix")
                st.metric("Prix actuel", f"{row['Prix']:,.0f} FCFA")
                st.metric("Variation 14j", f"{row['Var_14j_%']:+.2f}%")
                st.metric("ATR", f"{row['ATR']:,.0f} FCFA")

            with col2:
                st.markdown("#### 📊 Indicateurs")
                st.metric("RSI", f"{row['RSI']:.1f}")
                st.metric("MACD Hist", f"{row['MACD_Hist']:+.2f}")
                st.metric("Bollinger %B", f"{row['BB_PctB']:.2f}")
                st.metric("Volume x", f"{row['Volume_Ratio']:.1f}")

            with col3:
                st.markdown("#### 🎯 Position")
                st.metric("Nb actions", f"{row['Nb_Actions']}")
                st.metric("Montant", f"{row['Montant_FCFA']:,.0f} FCFA")
                st.metric("Ratio R/R", f"{row['Ratio_RR']:.2f}x")

            st.markdown("#### 💡 Analyse")
            st.info(expliquer_signal(row))

            st.markdown("#### 🛡️ Gestion du risque")
            c1, c2, c3 = st.columns(3)
            with c1:
                st.metric("Stop Loss", f"{row['Stop_Loss']:,.0f} FCFA")
            with c2:
                st.metric("Take Profit", f"{row['Take_Profit']:,.0f} FCFA")
            with c3:
                st.metric("Trailing Stop", f"{row['Trailing_Stop']:,.0f} FCFA")

# ============================================================================
# TAB 2 : ANALYSE DÉTAILLÉE
# ============================================================================

with tab2:
    st.markdown("### 📊 Tableau d'Analyse Complet")

    colonnes_defaut = [
        'Valeur', 'Prix', 'Score', 'Signal', 'RSI',
        'MACD_Hist', 'BB_PctB', 'ATR', 'Volume_Ratio',
        'Var_14j_%', 'Nb_Actions', 'Montant_FCFA', 'Ratio_RR'
    ]

    colonnes_affichees = st.multiselect(
        "Colonnes à afficher",
        df_filtered.columns.tolist(),
        default=[c for c in colonnes_defaut if c in df_filtered.columns]
    )

    if colonnes_affichees:
        df_display = df_filtered[colonnes_affichees].copy()

        def highlight_signal(row):
            if 'Signal' not in row.index:
                return [''] * len(row)
            if '🔥 ACHAT FORT' in str(row['Signal']):
                return ['background-color: #ffdddd'] * len(row)
            elif '✅ ACHAT' in str(row['Signal']):
                return ['background-color: #ddffdd'] * len(row)
            elif '⚠️ SURVEILLER' in str(row['Signal']):
                return ['background-color: #ffffcc'] * len(row)
            return [''] * len(row)

        st.dataframe(
            df_display.style.apply(highlight_signal, axis=1),
            use_container_width=True, height=500
        )

        csv = df_display.to_csv(index=False).encode('utf-8')
        st.download_button(
            "📥 Télécharger CSV", csv,
            file_name=f'brvm_{datetime.now().strftime("%Y%m%d")}.csv',
            mime='text/csv'
        )

    st.markdown("---")
    st.markdown("### 📈 Répartition des signaux")
    signal_counts = df_analysis['Signal'].value_counts()
    fig = px.pie(
        values=signal_counts.values, names=signal_counts.index,
        title="Distribution des signaux",
        color_discrete_sequence=px.colors.qualitative.Set3
    )
    st.plotly_chart(fig, use_container_width=True)

# ============================================================================
# TAB 3 : GRAPHIQUES
# ============================================================================

with tab3:
    st.markdown("### 📈 Analyse Graphique")

    entreprise = st.selectbox("Sélectionner une entreprise", df_analysis['Valeur'].unique())
    df_e = df_raw[df_raw['Valeur'] == entreprise].copy().sort_values('Date')

    if len(df_e) >= 60:

        close = df_e['Close']
        df_e['RSI']       = calculer_rsi(close)
        df_e['MM20'], df_e['MM50'] = calculer_moyennes_mobiles(close)
        _, _, df_e['MACD_Hist'] = calculer_macd(close)
        df_e['BB_H'], _, df_e['BB_L'], df_e['BB_PctB'] = calculer_bollinger(close)
        df_e['ATR'] = calculer_atr(df_e['High'], df_e['Low'], close)

        # ── Graphique 1 : Prix + MM + Bollinger ──────────────────────────────
        fig1 = go.Figure()
        fig1.add_trace(go.Scatter(x=df_e['Date'], y=df_e['BB_H'],
            name='BB Haute', line=dict(color='lightgray', width=1, dash='dot')))
        fig1.add_trace(go.Scatter(x=df_e['Date'], y=df_e['BB_L'],
            name='BB Basse', line=dict(color='lightgray', width=1, dash='dot'),
            fill='tonexty', fillcolor='rgba(200,200,200,0.1)'))
        fig1.add_trace(go.Scatter(x=df_e['Date'], y=close,
            name='Prix', line=dict(color='#1f77b4', width=2)))
        fig1.add_trace(go.Scatter(x=df_e['Date'], y=df_e['MM20'],
            name='MM20', line=dict(color='orange', width=1, dash='dash')))
        fig1.add_trace(go.Scatter(x=df_e['Date'], y=df_e['MM50'],
            name='MM50', line=dict(color='red', width=1, dash='dash')))
        fig1.update_layout(
            title=f'Prix + Moyennes Mobiles + Bollinger — {entreprise}',
            xaxis_title='Date', yaxis_title='Prix (FCFA)',
            hovermode='x unified', height=420
        )
        st.plotly_chart(fig1, use_container_width=True)

        # ── Graphique 2 : RSI ─────────────────────────────────────────────────
        fig2 = go.Figure()
        fig2.add_trace(go.Scatter(x=df_e['Date'], y=df_e['RSI'],
            name='RSI', line=dict(color='purple', width=2)))
        fig2.add_hline(y=70, line_dash="dash", line_color="red",
                       annotation_text="Surachat 70")
        fig2.add_hline(y=30, line_dash="dash", line_color="green",
                       annotation_text="Survente 30")
        fig2.update_layout(
            title=f'RSI (14j) — {entreprise}',
            xaxis_title='Date', yaxis_title='RSI',
            hovermode='x unified', height=280
        )
        st.plotly_chart(fig2, use_container_width=True)

        # ── Graphique 3 : MACD ────────────────────────────────────────────────
        fig3 = go.Figure()
        colors = ['#2ecc71' if v >= 0 else '#e74c3c' for v in df_e['MACD_Hist']]
        fig3.add_trace(go.Bar(x=df_e['Date'], y=df_e['MACD_Hist'],
            name='MACD Histogramme', marker_color=colors))
        fig3.add_hline(y=0, line_color="gray", line_width=1)
        fig3.update_layout(
            title=f'MACD Histogramme — {entreprise}',
            xaxis_title='Date', yaxis_title='MACD',
            hovermode='x unified', height=260
        )
        st.plotly_chart(fig3, use_container_width=True)

        # ── Graphique 4 : ATR ─────────────────────────────────────────────────
        fig4 = go.Figure()
        fig4.add_trace(go.Scatter(x=df_e['Date'], y=df_e['ATR'],
            name='ATR', line=dict(color='brown', width=1.5)))
        fig4.update_layout(
            title=f'ATR (14j) — Volatilité — {entreprise}',
            xaxis_title='Date', yaxis_title='ATR (FCFA)',
            hovermode='x unified', height=240
        )
        st.plotly_chart(fig4, use_container_width=True)

        # ── Infos actuelles ───────────────────────────────────────────────────
        st.markdown("### 📊 Snapshot actuel")
        info = df_analysis[df_analysis['Valeur'] == entreprise].iloc[0]

        c1, c2, c3, c4, c5 = st.columns(5)
        c1.metric("Score", f"{info['Score']}/10")
        c2.metric("Signal", info['Signal'])
        c3.metric("RSI", f"{info['RSI']:.1f}")
        c4.metric("MACD Hist", f"{info['MACD_Hist']:+.2f}")
        c5.metric("BB %B", f"{info['BB_PctB']:.2f}")

    else:
        st.warning("⚠️ Pas assez de données pour cet actif (minimum 60 points).")

# ============================================================================
# TAB 4 : SIMULATEUR
# ============================================================================

with tab4:
    st.markdown("### 💼 Simulateur de Portefeuille")
    st.info("🎯 Simule un portefeuille basé sur les signaux BRVM Bot")

    col1, col2 = st.columns(2)
    with col1:
        capital_sim = st.number_input(
            "💰 Capital de simulation (FCFA)",
            min_value=1000000, max_value=100000000,
            value=capital, step=1000000, key="sim_capital"
        )
    with col2:
        strategie = st.selectbox("📈 Stratégie", [
            "🔥 Seulement ACHAT FORT",
            "✅ ACHAT FORT + ACHAT",
            "⚠️ Tous signaux positifs (score ≥ 3)"
        ])

    if "Seulement ACHAT FORT" in strategie:
        df_sim = df_analysis[df_analysis['Signal'] == '🔥 ACHAT FORT'].copy()
    elif "ACHAT FORT + ACHAT" in strategie:
        df_sim = df_analysis[df_analysis['Signal'].str.contains('ACHAT', na=False)].copy()
    else:
        df_sim = df_analysis[df_analysis['Score'] >= 3].copy()

    if len(df_sim) == 0:
        st.warning("⚠️ Aucune opportunité pour cette stratégie")
    else:
        st.markdown(f"#### 🎯 {len(df_sim)} positions sélectionnées")

        capital_par_pos = capital_sim / len(df_sim)
        portefeuille = []
        capital_investi = 0

        for _, row in df_sim.iterrows():
            nb = int(capital_par_pos / row['Prix'])
            montant = nb * row['Prix']
            capital_investi += montant

            portefeuille.append({
                'Entreprise':    row['Valeur'],
                'Signal':        row['Signal'],
                'Score':         row['Score'],
                'Prix_Achat':    row['Prix'],
                'Nb_Actions':    nb,
                'Montant':       montant,
                'Stop_Loss':     row['Stop_Loss'],
                'Take_Profit':   row['Take_Profit'],
                'Ratio_RR':      row['Ratio_RR'],
                'Gain_si_TP':    (row['Take_Profit'] - row['Prix']) * nb,
                'Perte_si_SL':   (row['Prix'] - row['Stop_Loss']) * nb,
            })

        df_port = pd.DataFrame(portefeuille)

        # Métriques
        c1, c2, c3, c4 = st.columns(4)
        c1.metric("💰 Capital total",   f"{capital_sim:,.0f} FCFA")
        c2.metric("💵 Capital investi", f"{capital_investi:,.0f} FCFA")
        c3.metric("🏦 Liquidités",      f"{capital_sim - capital_investi:,.0f} FCFA")
        c4.metric("📈 Taux investi",    f"{capital_investi/capital_sim*100:.1f}%")

        st.markdown("---")

        gain_total = df_port['Gain_si_TP'].sum()
        perte_total = df_port['Perte_si_SL'].sum()

        c1, c2, c3 = st.columns(3)
        c1.metric("🎯 Si tous TP",  f"+{gain_total:,.0f} FCFA",
                  delta=f"+{gain_total/capital_investi*100:.1f}%")
        c2.metric("🛡️ Si tous SL", f"-{perte_total:,.0f} FCFA",
                  delta=f"-{perte_total/capital_investi*100:.1f}%")
        ratio_global = abs(gain_total/perte_total) if perte_total > 0 else 0
        c3.metric("⚖️ R/R global", f"{ratio_global:.2f}x")

        st.markdown("---")
        st.markdown("### 📋 Détail du portefeuille")
        st.dataframe(df_port, use_container_width=True, height=400)

        st.markdown("### 📊 Répartition du capital")
        fig = px.pie(df_port, values='Montant', names='Entreprise',
                     title=f'Répartition sur {len(df_port)} positions', hole=0.3)
        st.plotly_chart(fig, use_container_width=True)

        csv_port = df_port.to_csv(index=False).encode('utf-8')
        st.download_button(
            "📥 Télécharger portefeuille CSV", csv_port,
            file_name=f'portefeuille_{datetime.now().strftime("%Y%m%d_%H%M")}.csv',
            mime='text/csv'
        )

# ============================================================================
# TAB 5 : MISE À JOUR
# ============================================================================

with tab5:
    st.markdown("### 🔄 Mise à jour des données BRVM")

    st.info("""
    📌 **Comment mettre à jour les données :**
    1. Récupère ton GUID depuis SikaFinance (F12 → Network → GetTicksEOD)
    2. Colle-le dans `guid.txt` à la racine du projet
    3. Lance `python recup.py` sur ton ordinateur ou Termux
    4. Clique sur **Actualiser l'analyse** ci-dessous
    """)

    st.markdown("#### 📤 Upload manuel de fichiers CSV")
    uploaded_files = st.file_uploader(
        "Sélectionne des fichiers CSV (format SikaFinance)",
        type=['csv'], accept_multiple_files=True
    )

    if uploaded_files:
        st.success(f"✅ {len(uploaded_files)} fichier(s) sélectionné(s)")

        with st.expander("👁️ Prévisualiser"):
            for f in uploaded_files:
                st.markdown(f"**{f.name}**")
                st.dataframe(pd.read_csv(f).head(), use_container_width=True)
                f.seek(0)

        if st.button("💾 Sauvegarder dans brvm_data/", type="primary"):
            data_dir = Path("brvm_data")
            data_dir.mkdir(exist_ok=True)
            for f in uploaded_files:
                try:
                    (data_dir / f.name).write_bytes(f.getbuffer())
                    st.success(f"✅ {f.name} sauvegardé")
                except Exception as e:
                    st.error(f"❌ {f.name} : {e}")

    st.markdown("---")

    with st.expander("🔑 Comment obtenir ton GUID SikaFinance"):
        st.markdown("""
        1. Ouvre **https://www.sikafinance.com** dans Chrome
        2. Appuie sur **F12** → onglet **Network** (Réseau)
        3. Tape le nom d'une action dans la barre de recherche du site
        4. Dans les requêtes réseau, clique sur **GetTicksEOD**
        5. Copie la valeur du paramètre `guid` dans l'URL
        6. Colle-la dans un fichier **`guid.txt`** à la racine du projet
        7. Lance `python recup.py`
        """)

    st.markdown("---")
    st.markdown("#### 🔄 Actualiser l'analyse")

    c1, c2 = st.columns(2)
    with c1:
        if st.button("🔄 Actualiser", type="primary", use_container_width=True):
            st.cache_data.clear()
            st.rerun()
    with c2:
        if st.button("🗑️ Vider le cache", use_container_width=True):
            st.cache_data.clear()
            st.cache_resource.clear()
            st.success("✅ Cache vidé !")

    st.markdown("---")
    st.markdown("#### 📊 Données actuelles")

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("📁 Entreprises", len(df_analysis))
    c2.metric("📅 Début", df_raw['Date'].min().strftime('%d/%m/%Y'))
    c3.metric("📅 Fin",   df_raw['Date'].max().strftime('%d/%m/%Y'))
    c4.metric("📊 Points", f"{len(df_raw):,}")

    with st.expander("📋 Liste des entreprises"):
        entreprises = sorted(df_analysis['Valeur'].unique())
        cols = st.columns(4)
        for i, e in enumerate(entreprises):
            cols[i % 4].write(f"• {e}")

# ============================================================================
# FOOTER
# ============================================================================

st.markdown("---")
st.markdown("""
<div style='text-align:center;color:gray;padding:1.5rem;'>
    <p><strong>BRVM Bot Ultimate</strong> — Développé par Les Bullionaires 🏆</p>
    <p>RSI · MM20/50 · MACD · Bollinger · ATR · Volume</p>
    <p style='font-size:0.8rem;'>⚠️ Pas un conseil en investissement. Fais toujours tes propres recherches.</p>
</div>
""", unsafe_allow_html=True)
```

---

### `requirements.txt` — final
```
streamlit
pandas
numpy
requests
plotly
openpyxl
```

---

### Structure finale du projet
```
brvm_bot/
├── brvm_bot_ultimate.py   ← moteur d'analyse (MACD, Bollinger, ATR)
├── app.py                 ← dashboard Streamlit mis à jour
├── recup.py               ← récupération données + gestion GUID
├── guid.txt               ← ton GUID SikaFinance (à remplir)
├── requirements.txt       ← dépendances corrigées
└── brvm_data/             ← tes fichiers CSV
    ├── SNTS.sn.csv
    ├── SGBC.ci.csv
    └── ...
