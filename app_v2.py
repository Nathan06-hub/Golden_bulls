"""
app.py
Interface web Streamlit pour BRVM Bot Ultimate
Version complète avec simulateur de trading et mise à jour des données
"""

import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import plotly.express as px
from pathlib import Path
from datetime import datetime
import sys
import io

# Ajouter le chemin pour importer le bot
sys.path.insert(0, str(Path(__file__).parent))

from brvm_bot_ultimate import (
    load_brvm_data,
    AnalyseurBRVM,
    expliquer_signal,
    calculer_rsi,
    calculer_moyennes_mobiles
)

# ============================================================================
# CONFIGURATION DE LA PAGE
# ============================================================================

st.set_page_config(
    page_title="BRVM Bot Ultimate",
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="expanded"
)

# CSS personnalisé
st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        font-weight: bold;
        color: #1f77b4;
        text-align: center;
        margin-bottom: 2rem;
    }
    .metric-card {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        padding: 1.5rem;
        border-radius: 10px;
        color: white;
        text-align: center;
    }
</style>
""", unsafe_allow_html=True)

# ============================================================================
# FONCTION DE CHARGEMENT DES DONNÉES (AVEC CACHE)
# ============================================================================

@st.cache_data(ttl=3600)  # Cache pendant 1h
def charger_donnees(capital):
    """Charge et analyse les données BRVM"""
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
    st.image("https://via.placeholder.com/300x100/1f77b4/ffffff?text=BRVM+BOT", use_container_width=True)
    st.markdown("### ⚙️ Configuration")
    
    capital = st.number_input(
        "💰 Capital disponible (FCFA)",
        min_value=1000000,
        max_value=100000000,
        value=20000000,  # 20 millions FCFA par défaut
        step=1000000,
        format="%d"
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
    st.info("""
    **BRVM Bot Ultimate**
    
    Analyse technique avancée de la Bourse Régionale des Valeurs Mobilières (BRVM).
    
    Développé par **Les Bullionaires** 🏆
    """)

# ============================================================================
# CHARGEMENT DES DONNÉES
# ============================================================================

df_raw, df_analysis = charger_donnees(capital)

if df_raw is None or df_analysis is None:
    st.error("❌ Impossible de charger les données. Vérifie que le dossier brvm_data/ existe et contient des fichiers CSV.")
    st.stop()

# Appliquer les filtres
if signal_filter:
    df_filtered = df_analysis[df_analysis['Signal'].isin(signal_filter)]
else:
    df_filtered = df_analysis

df_filtered = df_filtered[df_filtered['Score'] >= score_min]

# ============================================================================
# HEADER
# ============================================================================

st.markdown('<p class="main-header">📈 BRVM Bot Ultimate</p>', unsafe_allow_html=True)
st.markdown(f"<p style='text-align: center; color: gray;'>Dernière mise à jour : {datetime.now().strftime('%d/%m/%Y %H:%M')}</p>", unsafe_allow_html=True)

# ============================================================================
# MÉTRIQUES PRINCIPALES
# ============================================================================

col1, col2, col3, col4 = st.columns(4)

with col1:
    st.metric(
        "🏢 Entreprises analysées",
        len(df_analysis),
        delta=None
    )

with col2:
    achats_forts = len(df_analysis[df_analysis['Signal'] == '🔥 ACHAT FORT'])
    st.metric(
        "🔥 Opportunités ACHAT FORT",
        achats_forts,
        delta=f"{(achats_forts/len(df_analysis)*100):.1f}%"
    )

with col3:
    prix_moyen = df_analysis['Prix'].mean()
    st.metric(
        "💰 Prix moyen",
        f"{prix_moyen:,.0f} FCFA",
        delta=None
    )

with col4:
    rsi_moyen = df_analysis['RSI'].mean()
    st.metric(
        "📊 RSI moyen",
        f"{rsi_moyen:.1f}",
        delta="Neutre" if 40 <= rsi_moyen <= 60 else ("Survendu" if rsi_moyen < 40 else "Surachat")
    )

st.markdown("---")

# ============================================================================
# ONGLETS PRINCIPAUX
# ============================================================================

tab1, tab2, tab3, tab4, tab5 = st.tabs([
    "🏆 Top Opportunités", 
    "📊 Analyse Détaillée", 
    "📈 Graphiques",
    "💼 Simulateur de Trading",
    "🔄 Mise à jour"
])

# ============================================================================
# TAB 1: TOP OPPORTUNITÉS
# ============================================================================

with tab1:
    st.markdown("### 🏆 Meilleures Opportunités d'Investissement")
    
    top_n = st.slider("Nombre d'opportunités à afficher", 5, 20, 10)
    
    for idx, row in df_filtered.head(top_n).iterrows():
        with st.expander(f"**{row['Signal']} - {row['Valeur']}** | Score: {row['Score']}/10", expanded=(idx < 3)):
            col1, col2, col3 = st.columns([2, 2, 2])
            
            with col1:
                st.markdown("#### 💰 Informations Prix")
                st.metric("Prix actuel", f"{row['Prix']:,.0f} FCFA")
                st.metric("Variation 14j", f"{row['Var_14j_%']:+.2f}%")
                
            with col2:
                st.markdown("#### 📊 Indicateurs Techniques")
                st.metric("RSI", f"{row['RSI']:.1f}")
                st.metric("MM20", f"{row['MM20']:,.0f} FCFA")
                st.metric("MM50", f"{row['MM50']:,.0f} FCFA")
                
            with col3:
                st.markdown("#### 🎯 Position Recommandée")
                st.metric("Nombre d'actions", f"{row['Nb_Actions']}")
                st.metric("Montant", f"{row['Montant_FCFA']:,.0f} FCFA")
                st.metric("Ratio R/R", f"{row['Ratio_RR']:.2f}")
            
            st.markdown("#### 💡 Analyse")
            explication = expliquer_signal(row)
            st.info(explication)
            
            st.markdown("#### 🛡️ Gestion du Risque")
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("Stop Loss", f"{row['Stop_Loss']:,.0f} FCFA", delta="-5%")
            with col2:
                st.metric("Take Profit", f"{row['Take_Profit']:,.0f} FCFA", delta="+10%")
            with col3:
                st.metric("Trailing Stop", f"{row['Trailing_Stop']:,.0f} FCFA", delta="-3%")

# ============================================================================
# TAB 2: ANALYSE DÉTAILLÉE
# ============================================================================

with tab2:
    st.markdown("### 📊 Tableau d'Analyse Complet")
    
    colonnes_affichees = st.multiselect(
        "Colonnes à afficher",
        df_filtered.columns.tolist(),
        default=['Valeur', 'Prix', 'Score', 'Signal', 'RSI', 'Var_14j_%', 'Nb_Actions', 'Montant_FCFA']
    )
    
    if colonnes_affichees:
        df_display = df_filtered[colonnes_affichees].copy()
        
        def highlight_signal(row):
            if '🔥 ACHAT FORT' in str(row['Signal']):
                return ['background-color: #ffcccc'] * len(row)
            elif '✅ ACHAT' in str(row['Signal']):
                return ['background-color: #ccffcc'] * len(row)
            elif '⚠️ SURVEILLER' in str(row['Signal']):
                return ['background-color: #ffffcc'] * len(row)
            else:
                return [''] * len(row)
        
        st.dataframe(
            df_display.style.apply(highlight_signal, axis=1),
            use_container_width=True,
            height=500
        )
        
        csv = df_display.to_csv(index=False).encode('utf-8')
        st.download_button(
            label="📥 Télécharger en CSV",
            data=csv,
            file_name=f'brvm_analyse_{datetime.now().strftime("%Y%m%d")}.csv',
            mime='text/csv',
        )
    
    st.markdown("---")
    st.markdown("### 📈 Répartition des Signaux")
    
    signal_counts = df_analysis['Signal'].value_counts()
    
    fig = px.pie(
        values=signal_counts.values,
        names=signal_counts.index,
        title="Distribution des signaux de trading",
        color_discrete_sequence=px.colors.qualitative.Set3
    )
    st.plotly_chart(fig, use_container_width=True)

# ============================================================================
# TAB 3: GRAPHIQUES
# ============================================================================

with tab3:
    st.markdown("### 📈 Visualisations Graphiques")
    
    entreprise = st.selectbox(
        "Sélectionner une entreprise",
        df_analysis['Valeur'].unique()
    )
    
    df_entreprise = df_raw[df_raw['Valeur'] == entreprise].copy()
    df_entreprise = df_entreprise.sort_values('Date')
    
    if len(df_entreprise) > 0:
        df_entreprise['RSI'] = calculer_rsi(df_entreprise['Close'], 14)
        mm20, mm50 = calculer_moyennes_mobiles(df_entreprise['Close'])
        df_entreprise['MM20'] = mm20
        df_entreprise['MM50'] = mm50
        
        # Graphique du prix
        fig1 = go.Figure()
        
        fig1.add_trace(go.Scatter(
            x=df_entreprise['Date'],
            y=df_entreprise['Close'],
            name='Prix',
            line=dict(color='blue', width=2)
        ))
        
        fig1.add_trace(go.Scatter(
            x=df_entreprise['Date'],
            y=df_entreprise['MM20'],
            name='MM20',
            line=dict(color='orange', width=1, dash='dash')
        ))
        
        fig1.add_trace(go.Scatter(
            x=df_entreprise['Date'],
            y=df_entreprise['MM50'],
            name='MM50',
            line=dict(color='red', width=1, dash='dash')
        ))
        
        fig1.update_layout(
            title=f'Évolution du prix - {entreprise}',
            xaxis_title='Date',
            yaxis_title='Prix (FCFA)',
            hovermode='x unified',
            height=400
        )
        
        st.plotly_chart(fig1, use_container_width=True)
        
        # Graphique RSI
        fig2 = go.Figure()
        
        fig2.add_trace(go.Scatter(
            x=df_entreprise['Date'],
            y=df_entreprise['RSI'],
            name='RSI',
            line=dict(color='purple', width=2)
        ))
        
        fig2.add_hline(y=70, line_dash="dash", line_color="red", annotation_text="Surachat (70)")
        fig2.add_hline(y=30, line_dash="dash", line_color="green", annotation_text="Survente (30)")
        
        fig2.update_layout(
            title=f'RSI (14 jours) - {entreprise}',
            xaxis_title='Date',
            yaxis_title='RSI',
            hovermode='x unified',
            height=300
        )
        
        st.plotly_chart(fig2, use_container_width=True)
        
        # Informations actuelles
        st.markdown("### 📊 Informations Actuelles")
        
        info_entreprise = df_analysis[df_analysis['Valeur'] == entreprise].iloc[0]
        
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric("Score", f"{info_entreprise['Score']}/10")
        with col2:
            st.metric("Signal", info_entreprise['Signal'])
        with col3:
            st.metric("Prix actuel", f"{info_entreprise['Prix']:,.0f} FCFA")
        with col4:
            st.metric("RSI", f"{info_entreprise['RSI']:.1f}")

# ============================================================================
# TAB 4: SIMULATEUR DE TRADING
# ============================================================================

with tab4:
    st.markdown("### 💼 Simulateur de Portefeuille de Trading")
    st.info("🎯 Simule un portefeuille d'investissement basé sur les signaux BRVM Bot")
    
    # Configuration
    col1, col2 = st.columns(2)
    
    with col1:
        capital_simulation = st.number_input(
            "💰 Capital de simulation (FCFA)",
            min_value=1000000,
            max_value=100000000,
            value=capital,
            step=1000000,
            key="sim_capital"
        )
    
    with col2:
        strategie = st.selectbox(
            "📈 Stratégie d'investissement",
            [
                "🔥 Seulement ACHAT FORT", 
                "✅ ACHAT FORT + ACHAT", 
                "⚠️ Tous signaux positifs (≥3)"
            ]
        )
    
    # Sélection des entreprises selon la stratégie
    if "Seulement ACHAT FORT" in strategie:
        df_sim = df_analysis[df_analysis['Signal'] == '🔥 ACHAT FORT'].copy()
    elif "ACHAT FORT + ACHAT" in strategie:
        df_sim = df_analysis[df_analysis['Signal'].str.contains('ACHAT', na=False)].copy()
    else:
        df_sim = df_analysis[df_analysis['Score'] >= 3].copy()
    
    if len(df_sim) == 0:
        st.warning("⚠️ Aucune opportunité trouvée pour cette stratégie")
    else:
        st.markdown(f"#### 🎯 {len(df_sim)} opportunités sélectionnées")
        
        # Calcul de la répartition
        nb_positions = len(df_sim)
        capital_par_position = capital_simulation / nb_positions
        
        # Construction du portefeuille
        portefeuille = []
        capital_investi_total = 0
        
        for idx, row in df_sim.iterrows():
            nb_actions = int(capital_par_position / row['Prix'])
            montant_investi = nb_actions * row['Prix']
            capital_investi_total += montant_investi
            
            gain_tp = (row['Take_Profit'] - row['Prix']) * nb_actions
            perte_sl = (row['Prix'] - row['Stop_Loss']) * nb_actions
            
            portefeuille.append({
                'Entreprise': row['Valeur'],
                'Signal': row['Signal'],
                'Score': row['Score'],
                'Prix_Achat': row['Prix'],
                'Nb_Actions': nb_actions,
                'Montant_Investi': montant_investi,
                'Stop_Loss': row['Stop_Loss'],
                'Take_Profit': row['Take_Profit'],
                'Gain_si_TP': gain_tp,
                'Perte_si_SL': perte_sl
            })
        
        df_portefeuille = pd.DataFrame(portefeuille)
        
        # Métriques du portefeuille
        st.markdown("### 📊 Vue d'ensemble du portefeuille")
        
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric("💰 Capital total", f"{capital_simulation:,.0f} FCFA")
        
        with col2:
            st.metric("💵 Capital investi", f"{capital_investi_total:,.0f} FCFA")
        
        with col3:
            capital_restant = capital_simulation - capital_investi_total
            st.metric("🏦 Liquidités", f"{capital_restant:,.0f} FCFA")
        
        with col4:
            taux_invest = (capital_investi_total / capital_simulation) * 100
            st.metric("📈 Taux investi", f"{taux_invest:.1f}%")
        
        st.markdown("---")
        
        # Potentiel de gains/pertes
        gain_total_tp = df_portefeuille['Gain_si_TP'].sum()
        perte_totale_sl = df_portefeuille['Perte_si_SL'].sum()
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            rendement_tp = (gain_total_tp / capital_investi_total) * 100
            st.metric(
                "🎯 Si tous TP atteints",
                f"+{gain_total_tp:,.0f} FCFA",
                delta=f"+{rendement_tp:.1f}%"
            )
        
        with col2:
            rendement_sl = (perte_totale_sl / capital_investi_total) * 100
            st.metric(
                "🛡️ Si tous SL touchés",
                f"{perte_totale_sl:,.0f} FCFA",
                delta=f"{rendement_sl:.1f}%"
            )
        
        with col3:
            ratio_rr = abs(gain_total_tp / perte_totale_sl) if perte_totale_sl != 0 else 0
            st.metric("⚖️ Ratio R/R global", f"{ratio_rr:.2f}x")
        
        st.markdown("---")
        
        # Tableau du portefeuille
        st.markdown("### 📋 Détail du portefeuille")
        
        df_display_port = df_portefeuille.copy()
        df_display_port['Prix_Achat'] = df_display_port['Prix_Achat'].apply(lambda x: f"{x:,.0f} FCFA")
        df_display_port['Montant_Investi'] = df_display_port['Montant_Investi'].apply(lambda x: f"{x:,.0f} FCFA")
        df_display_port['Stop_Loss'] = df_display_port['Stop_Loss'].apply(lambda x: f"{x:,.0f} FCFA")
        df_display_port['Take_Profit'] = df_display_port['Take_Profit'].apply(lambda x: f"{x:,.0f} FCFA")
        df_display_port['Gain_si_TP'] = df_display_port['Gain_si_TP'].apply(lambda x: f"+{x:,.0f} FCFA")
        df_display_port['Perte_si_SL'] = df_display_port['Perte_si_SL'].apply(lambda x: f"{x:,.0f} FCFA")
        
        st.dataframe(df_display_port, use_container_width=True, height=400)
        
        # Graphique de répartition
        st.markdown("### 📊 Répartition du capital investi")
        
        fig = px.pie(
            df_portefeuille,
            values='Montant_Investi',
            names='Entreprise',
            title=f'Répartition sur {len(df_portefeuille)} positions',
            hole=0.3
        )
        st.plotly_chart(fig, use_container_width=True)
        
        # Export
        csv_port = df_portefeuille.to_csv(index=False).encode('utf-8')
        st.download_button(
            label="📥 Télécharger le portefeuille (CSV)",
            data=csv_port,
            file_name=f'portefeuille_brvm_{datetime.now().strftime("%Y%m%d_%H%M")}.csv',
            mime='text/csv',
        )

# ============================================================================
# TAB 5: MISE À JOUR DES DONNÉES
# ============================================================================

with tab5:
    st.markdown("### 🔄 Mise à jour des données BRVM")
    
    st.info("""
    📌 **Trois façons de mettre à jour les données :**
    1. Upload manuel de fichiers CSV
    2. Script automatique (recup.py)
    3. Synchronisation GitHub (pour version en ligne)
    """)
    
    # Option 1: Upload manuel
    st.markdown("#### 📤 Option 1: Upload manuel de fichiers CSV")
    st.markdown("Format attendu : fichiers CSV au format SikaFinance (colonnes: d, o, h, l, c, v)")
    
    uploaded_files = st.file_uploader(
        "Sélectionne un ou plusieurs fichiers CSV",
        type=['csv'],
        accept_multiple_files=True,
        help="Format SikaFinance avec colonnes: d (date), c (close), etc."
    )
    
    if uploaded_files:
        st.success(f"✅ {len(uploaded_files)} fichier(s) sélectionné(s)")
        
        # Prévisualisation
        with st.expander("👁️ Prévisualiser les fichiers"):
            for uploaded_file in uploaded_files:
                st.markdown(f"**{uploaded_file.name}**")
                df_preview = pd.read_csv(uploaded_file)
                st.dataframe(df_preview.head(), use_container_width=True)
                uploaded_file.seek(0)  # Reset file pointer
        
        if st.button("💾 Sauvegarder dans brvm_data/", type="primary"):
            saved_count = 0
            data_dir = Path("brvm_data")
            data_dir.mkdir(exist_ok=True)
            
            for uploaded_file in uploaded_files:
                try:
                    file_path = data_dir / uploaded_file.name
                    with open(file_path, "wb") as f:
                        f.write(uploaded_file.getbuffer())
                    saved_count += 1
                    st.success(f"✅ {uploaded_file.name} sauvegardé")
                except Exception as e:
                    st.error(f"❌ Erreur avec {uploaded_file.name}: {e}")
            
            if saved_count > 0:
                st.success(f"🎉 {saved_count} fichier(s) ajouté(s) avec succès!")
                st.info("🔄 Clique sur 'Actualiser l'analyse' ci-dessous pour voir les nouvelles données")
    
    st.markdown("---")
    
    # Option 2: Script automatique
    st.markdown("#### 🤖 Option 2: Script automatique (recup.py)")
    
    with st.expander("📖 Comment utiliser recup.py"):
        st.code("""
# Sur Termux ou ordinateur
cd brvm_bot
python3 recup.py

# Les données seront mises à jour dans brvm_data/
# Puis actualise l'app web
        """, language="bash")
    
    st.markdown("---")
    
    # Option 3: Synchronisation GitHub
    st.markdown("#### 🔗 Option 3: Synchronisation GitHub (app en ligne)")
    
    with st.expander("📖 Déploiement sur Streamlit Cloud"):
        st.markdown("""
        **Pour l'app hébergée sur Streamlit Cloud :**
        
        1. Mets à jour tes fichiers CSV localement
        2. Upload-les sur ton repository GitHub
        3. Streamlit Cloud détectera les changements
        4. L'app se mettra à jour automatiquement (1-2 min)
        
        **Ou via Git :**
        ```bash
        git add brvm_data/*.csv
        git commit -m "Mise à jour des données BRVM"
        git push
        ```
        """)
    
    # Bouton de rechargement
    st.markdown("---")
    st.markdown("#### 🔄 Actualiser l'analyse")
    
    col1, col2 = st.columns(2)
    
    with col1:
        if st.button("🔄 Actualiser l'analyse", type="primary", use_container_width=True):
            st.cache_data.clear()
            st.success("✅ Cache vidé ! Actualisation...")
            st.rerun()
    
    with col2:
        if st.button("🗑️ Vider tout le cache", use_container_width=True):
            st.cache_data.clear()
            st.cache_resource.clear()
            st.success("✅ Tous les caches vidés !")
    
    st.markdown("---")
    
    # Informations sur les données actuelles
    st.markdown("#### 📊 Informations sur les données actuelles")
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("📁 Entreprises", len(df_analysis))
    
    with col2:
        date_debut = df_raw['Date'].min().strftime('%d/%m/%Y')
        st.metric("📅 Début", date_debut)
    
    with col3:
        date_fin = df_raw['Date'].max().strftime('%d/%m/%Y')
        st.metric("📅 Fin", date_fin)
    
    with col4:
        st.metric("📊 Points", f"{len(df_raw):,}")
    
    # Liste des entreprises
    with st.expander("📋 Liste complète des entreprises disponibles"):
        entreprises = sorted(df_analysis['Valeur'].unique())
        
        # Afficher en colonnes
        n_cols = 4
        cols = st.columns(n_cols)
        
        for i, entreprise in enumerate(entreprises):
            col_idx = i % n_cols
            cols[col_idx].write(f"• {entreprise}")
    
    # Instructions pour ajouter de nouvelles entreprises
    with st.expander("➕ Comment ajouter de nouvelles entreprises ?"):
        st.markdown("""
        **Méthode recommandée :**
        
        1. **Télécharge les données depuis SikaFinance**
           - Va sur https://www.sikafinance.com
           - Cherche l'entreprise voulue
           - Export les données historiques (CSV)
        
        2. **Renomme le fichier**
           - Format: `TICKER.pays.csv`
           - Exemples: `SONATEL.sn.csv`, `BICC.ci.csv`
        
        3. **Upload via l'option 1 ci-dessus**
        
        4. **Actualise l'analyse** (bouton ci-dessus)
        
        ✅ La nouvelle entreprise apparaîtra dans toutes les analyses !
        """)

# ============================================================================
# FOOTER
# ============================================================================

st.markdown("---")
st.markdown("""
<div style='text-align: center; color: gray; padding: 2rem;'>
    <p><strong>BRVM Bot Ultimate</strong> - Développé par Les Bullionaires 🏆</p>
    <p>Analyse technique de la BRVM basée sur RSI, moyennes mobiles et momentum</p>
    <p style='font-size: 0.8rem;'>⚠️ Ceci n'est pas un conseil en investissement. Toujours faire ses propres recherches.</p>
</div>
""", unsafe_allow_html=True)
