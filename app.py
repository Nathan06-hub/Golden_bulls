"""
app.py
Interface web Streamlit pour BRVM Bot Ultimate
Version équilibrée : moderne, intuitive, fonctionnalités essentielles
"""

import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import plotly.express as px
from pathlib import Path
from datetime import datetime
import sys

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
    .buy-strong {
        background-color: #ff4444;
        color: white;
        padding: 0.5rem 1rem;
        border-radius: 5px;
        font-weight: bold;
    }
    .buy {
        background-color: #00C851;
        color: white;
        padding: 0.5rem 1rem;
        border-radius: 5px;
        font-weight: bold;
    }
    .watch {
        background-color: #ffbb33;
        color: white;
        padding: 0.5rem 1rem;
        border-radius: 5px;
        font-weight: bold;
    }
</style>
""", unsafe_allow_html=True)

# ============================================================================
# FONCTION DE CHARGEMENT DES DONNÉES (AVEC CACHE)
# ============================================================================

@st.cache_data(ttl=3600)  # Cache pendant 1h
def charger_donnees():
    """Charge et analyse les données BRVM"""
    df = load_brvm_data()
    if df is None:
        return None, None
    
    analyseur = AnalyseurBRVM(capital=1000000)
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
        min_value=100000,
        max_value=100000000,
        value=1000000,
        step=100000,
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

df_raw, df_analysis = charger_donnees()

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

tab1, tab2, tab3 = st.tabs(["🏆 Top Opportunités", "📊 Analyse Détaillée", "📈 Graphiques"])

# ============================================================================
# TAB 1: TOP OPPORTUNITÉS
# ============================================================================

with tab1:
    st.markdown("### 🏆 Meilleures Opportunités d'Investissement")
    
    # Sélecteur du nombre d'opportunités à afficher
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
            
            # Explication détaillée
            st.markdown("#### 💡 Analyse")
            explication = expliquer_signal(row)
            st.info(explication)
            
            # Risk Management
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
    
    # Sélection des colonnes à afficher
    colonnes_affichees = st.multiselect(
        "Colonnes à afficher",
        df_filtered.columns.tolist(),
        default=['Valeur', 'Prix', 'Score', 'Signal', 'RSI', 'Var_14j_%', 'Nb_Actions', 'Montant_FCFA']
    )
    
    if colonnes_affichees:
        # Formater le DataFrame pour l'affichage
        df_display = df_filtered[colonnes_affichees].copy()
        
        # Appliquer un style conditionnel
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
        
        # Bouton de téléchargement
        csv = df_display.to_csv(index=False).encode('utf-8')
        st.download_button(
            label="📥 Télécharger en CSV",
            data=csv,
            file_name=f'brvm_analyse_{datetime.now().strftime("%Y%m%d")}.csv',
            mime='text/csv',
        )
    
    st.markdown("---")
    
    # Statistiques par signal
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
    
    # Sélection de l'entreprise
    entreprise = st.selectbox(
        "Sélectionner une entreprise",
        df_analysis['Valeur'].unique()
    )
    
    # Filtrer les données de l'entreprise
    df_entreprise = df_raw[df_raw['Valeur'] == entreprise].copy()
    df_entreprise = df_entreprise.sort_values('Date')
    
    if len(df_entreprise) > 0:
        # Calculer les indicateurs pour le graphique
        df_entreprise['RSI'] = calculer_rsi(df_entreprise['Close'], 14)
        mm20, mm50 = calculer_moyennes_mobiles(df_entreprise['Close'])
        df_entreprise['MM20'] = mm20
        df_entreprise['MM50'] = mm50
        
        # Graphique du prix avec moyennes mobiles
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
        
        # Lignes de référence RSI
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
                
