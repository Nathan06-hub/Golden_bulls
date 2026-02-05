"""
Football Betting Analyzer - Web Interface
Application Flask avec interface mobile responsive
"""

from flask import Flask, render_template, request, jsonify
import requests
import math
import os
from datetime import datetime
from typing import Dict, List, Tuple, Optional
import json

app = Flask(__name__)

# --- CONFIGURATION ---
API_KEY = os.getenv('FOOTBALL_API_KEY', '3506889e741b493eacc1d7792f1200d4')
HEADERS = {'X-Auth-Token': API_KEY}
BASE_URL = "https://api.football-data.org/v4"

# Paramètres par défaut (modifiables via l'interface)
DEFAULT_CONFIG = {
    'facteur_domicile': 1.10,
    'max_buts': 10,
    'marge_value_bet': 1.05,
    'commission_exchange': 0.02,
    'competition': 'PL'
}

# --- FONCTIONS DE CALCUL ---

def calcul_poisson(lmbda: float, k: int) -> float:
    """Calcule la probabilité de Poisson"""
    if lmbda < 0:
        return 0
    try:
        return (math.pow(lmbda, k) * math.exp(-lmbda)) / math.factorial(k)
    except:
        return 0


def get_data(competition: str = "PL") -> Tuple[Optional[List], Optional[List]]:
    """Récupère les données du classement et des matchs"""
    try:
        url_standings = f"{BASE_URL}/competitions/{competition}/standings"
        url_matches = f"{BASE_URL}/competitions/{competition}/matches?status=SCHEDULED"
        
        standings = requests.get(url_standings, headers=HEADERS, timeout=10).json()['standings'][0]['table']
        matches = requests.get(url_matches, headers=HEADERS, timeout=10).json()['matches']
        
        return standings, matches
    except Exception as e:
        print(f"Erreur API : {e}")
        return None, None


def calculer_probs(s_dom: Dict, s_ext: Dict, moy_buts: float, config: Dict) -> Optional[Dict]:
    """Calcule les probabilités avec configuration personnalisée"""
    if s_dom['playedGames'] == 0 or s_ext['playedGames'] == 0:
        return None
    
    facteur_domicile = config.get('facteur_domicile', 1.10)
    max_buts = config.get('max_buts', 10)
    
    # Lambdas
    att_dom = s_dom['goalsFor'] / s_dom['playedGames']
    def_ext = s_ext['goalsAgainst'] / s_ext['playedGames']
    att_ext = s_ext['goalsFor'] / s_ext['playedGames']
    def_dom = s_dom['goalsAgainst'] / s_dom['playedGames']
    
    l_dom = (att_dom / moy_buts) * def_ext * facteur_domicile if moy_buts > 0 else att_dom * facteur_domicile
    l_ext = (att_ext / moy_buts) * def_dom if moy_buts > 0 else att_ext
    
    # Probabilités
    p_dom, p_nul, p_ext = 0, 0, 0
    score_max_prob = 0
    score_probable = "1-1"
    
    for d in range(max_buts):
        for e in range(max_buts):
            prob = calcul_poisson(l_dom, d) * calcul_poisson(l_ext, e)
            
            if prob > score_max_prob:
                score_max_prob = prob
                score_probable = f"{d}-{e}"
            
            if d > e: p_dom += prob
            elif d == e: p_nul += prob
            else: p_ext += prob
    
    total = p_dom + p_nul + p_ext
    if total > 0:
        p_dom, p_nul, p_ext = p_dom/total, p_nul/total, p_ext/total
    
    return {
        'p_dom': p_dom,
        'p_nul': p_nul,
        'p_ext': p_ext,
        'lambda_dom': l_dom,
        'lambda_ext': l_ext,
        'score_probable': score_probable,
        'cote_juste_dom': 1/p_dom if p_dom > 0 else 999,
        'cote_juste_nul': 1/p_nul if p_nul > 0 else 999,
        'cote_juste_ext': 1/p_ext if p_ext > 0 else 999
    }


def calculer_matched_betting(mise_back: float, cote_back: float, cote_lay: float, commission: float) -> Dict:
    """Calcule le matched betting"""
    mise_lay = (mise_back * cote_back) / (cote_lay - commission)
    responsabilite = mise_lay * (cote_lay - 1)
    
    gain_back = mise_back * (cote_back - 1)
    perte_lay = responsabilite
    resultat_si_back_gagne = gain_back - perte_lay
    
    gain_lay = mise_lay * (1 - commission)
    resultat_si_back_perd = gain_lay
    
    profit_garanti = min(resultat_si_back_gagne, resultat_si_back_perd)
    
    return {
        'mise_lay': mise_lay,
        'responsabilite': responsabilite,
        'resultat_si_back_gagne': resultat_si_back_gagne,
        'resultat_si_back_perd': resultat_si_back_perd,
        'profit_garanti': profit_garanti,
        'taux_conversion': (profit_garanti / mise_back) * 100 if mise_back > 0 else 0
    }


# --- ROUTES API ---

@app.route('/')
def index():
    """Page d'accueil"""
    return render_template('index.html')


@app.route('/api/predictions', methods=['POST'])
def get_predictions():
    """API : Récupère les prévisions pour une compétition"""
    data = request.json
    competition = data.get('competition', 'PL')
    config = data.get('config', DEFAULT_CONFIG)
    
    standings, matches = get_data(competition)
    
    if not standings or not matches:
        return jsonify({'error': 'Impossible de récupérer les données'}), 500
    
    # Calculer moyenne de buts
    total_buts = sum(t['goalsFor'] for t in standings)
    total_matchs = sum(t['playedGames'] for t in standings)
    moy_buts = total_buts / total_matchs if total_matchs > 0 else 1.4
    
    predictions = []
    
    for match in matches[:20]:  # Limiter à 20 matchs
        dom_nom = match['homeTeam']['shortName']
        ext_nom = match['awayTeam']['shortName']
        
        s_dom = next((t for t in standings if t['team']['shortName'] == dom_nom), None)
        s_ext = next((t for t in standings if t['team']['shortName'] == ext_nom), None)
        
        if not s_dom or not s_ext:
            continue
        
        probs = calculer_probs(s_dom, s_ext, moy_buts, config)
        
        if not probs:
            continue
        
        date_match = datetime.fromisoformat(match['utcDate'].replace('Z', '+00:00'))
        
        predictions.append({
            'match_id': match['id'],
            'domicile': dom_nom,
            'exterieur': ext_nom,
            'date': date_match.strftime('%d/%m/%Y'),
            'heure': date_match.strftime('%H:%M'),
            'probabilites': {
                'domicile': round(probs['p_dom'] * 100, 2),
                'nul': round(probs['p_nul'] * 100, 2),
                'exterieur': round(probs['p_ext'] * 100, 2)
            },
            'cotes_justes': {
                'domicile': round(probs['cote_juste_dom'], 2),
                'nul': round(probs['cote_juste_nul'], 2),
                'exterieur': round(probs['cote_juste_ext'], 2)
            },
            'lambdas': {
                'domicile': round(probs['lambda_dom'], 2),
                'exterieur': round(probs['lambda_ext'], 2)
            },
            'score_probable': probs['score_probable']
        })
    
    return jsonify({
        'success': True,
        'competition': competition,
        'moy_buts_ligue': round(moy_buts, 2),
        'nb_matchs': len(predictions),
        'predictions': predictions
    })


@app.route('/api/analyze_match', methods=['POST'])
def analyze_match():
    """API : Analyse détaillée d'un match avec value bet detection"""
    data = request.json
    
    dom = data.get('domicile')
    ext = data.get('exterieur')
    cotes_bookmaker = data.get('cotes_bookmaker', {})
    competition = data.get('competition', 'PL')
    config = data.get('config', DEFAULT_CONFIG)
    
    standings, _ = get_data(competition)
    
    if not standings:
        return jsonify({'error': 'Impossible de récupérer les données'}), 500
    
    s_dom = next((t for t in standings if dom.lower() in t['team']['shortName'].lower()), None)
    s_ext = next((t for t in standings if ext.lower() in t['team']['shortName'].lower()), None)
    
    if not s_dom or not s_ext:
        return jsonify({'error': 'Équipe non trouvée'}), 404
    
    total_buts = sum(t['goalsFor'] for t in standings)
    total_matchs = sum(t['playedGames'] for t in standings)
    moy_buts = total_buts / total_matchs if total_matchs > 0 else 1.4
    
    probs = calculer_probs(s_dom, s_ext, moy_buts, config)
    
    if not probs:
        return jsonify({'error': 'Erreur de calcul'}), 500
    
    # Analyse value bets
    marge = config.get('marge_value_bet', 1.05)
    value_bets = []
    
    issues = ['domicile', 'nul', 'exterieur']
    cotes_justes = [probs['cote_juste_dom'], probs['cote_juste_nul'], probs['cote_juste_ext']]
    probas = [probs['p_dom'], probs['p_nul'], probs['p_ext']]
    
    for i, issue in enumerate(issues):
        cote_bm = cotes_bookmaker.get(issue, 0)
        if cote_bm > 0 and cote_bm > (cotes_justes[i] * marge):
            valeur = ((cote_bm / cotes_justes[i]) - 1) * 100
            esperance = (cote_bm * probas[i]) - 1
            value_bets.append({
                'issue': issue,
                'cote_bookmaker': cote_bm,
                'cote_juste': round(cotes_justes[i], 2),
                'valeur_pct': round(valeur, 2),
                'esperance_pct': round(esperance * 100, 2)
            })
    
    return jsonify({
        'success': True,
        'match': f"{s_dom['team']['shortName']} vs {s_ext['team']['shortName']}",
        'statistiques': {
            'domicile': {
                'equipe': s_dom['team']['shortName'],
                'matchs': s_dom['playedGames'],
                'buts_marques': s_dom['goalsFor'],
                'buts_encaisses': s_dom['goalsAgainst'],
                'position': s_dom['position']
            },
            'exterieur': {
                'equipe': s_ext['team']['shortName'],
                'matchs': s_ext['playedGames'],
                'buts_marques': s_ext['goalsFor'],
                'buts_encaisses': s_ext['goalsAgainst'],
                'position': s_ext['position']
            }
        },
        'probabilites': {
            'domicile': round(probs['p_dom'] * 100, 2),
            'nul': round(probs['p_nul'] * 100, 2),
            'exterieur': round(probs['p_ext'] * 100, 2)
        },
        'cotes_justes': {
            'domicile': round(probs['cote_juste_dom'], 2),
            'nul': round(probs['cote_juste_nul'], 2),
            'exterieur': round(probs['cote_juste_ext'], 2)
        },
        'lambdas': {
            'domicile': round(probs['lambda_dom'], 2),
            'exterieur': round(probs['lambda_ext'], 2)
        },
        'score_probable': probs['score_probable'],
        'value_bets': value_bets,
        'nb_value_bets': len(value_bets)
    })


@app.route('/api/matched_betting', methods=['POST'])
def calculate_matched_betting():
    """API : Calcule le matched betting"""
    data = request.json
    
    mise_back = data.get('mise_back', 5000)
    cote_back = data.get('cote_back', 2.0)
    cote_lay = data.get('cote_lay', 2.1)
    commission = data.get('commission', 0.02)
    
    result = calculer_matched_betting(mise_back, cote_back, cote_lay, commission)
    
    return jsonify({
        'success': True,
        'mise_back': mise_back,
        'cote_back': cote_back,
        'cote_lay': cote_lay,
        'commission': commission * 100,
        'mise_lay': round(result['mise_lay'], 0),
        'responsabilite': round(result['responsabilite'], 0),
        'resultat_si_back_gagne': round(result['resultat_si_back_gagne'], 0),
        'resultat_si_back_perd': round(result['resultat_si_back_perd'], 0),
        'profit_garanti': round(result['profit_garanti'], 0),
        'taux_conversion': round(result['taux_conversion'], 2)
    })


@app.route('/api/config', methods=['GET', 'POST'])
def manage_config():
    """Gérer la configuration"""
    if request.method == 'POST':
        new_config = request.json
        # Valider et enregistrer la configuration
        return jsonify({'success': True, 'config': new_config})
    else:
        return jsonify(DEFAULT_CONFIG)


if __name__ == '__main__':
    # Pour développement local
    app.run(host='0.0.0.0', port=5000, debug=True)
    
    # Pour production, utilisez un serveur WSGI comme Gunicorn :
    # gunicorn -w 4 -b 0.0.0.0:5000 app:app
