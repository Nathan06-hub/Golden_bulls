# 🚀 GUIDE DE DÉPLOIEMENT - BRVM Bot Ultimate Web

Ce guide t'explique comment déployer ton bot BRVM sur le web **gratuitement** avec Streamlit Cloud.

---

## 📋 PRÉREQUIS

1. ✅ Un compte GitHub (gratuit)
2. ✅ Ton dossier `brvm_bot` avec les données
3. ✅ Les 3 fichiers :
   - `app.py` (interface web)
   - `brvm_bot_ultimate.py` (moteur d'analyse)
   - `requirements_web.txt` (dépendances)

---

## 🎯 ÉTAPE 1 : CRÉER UN COMPTE GITHUB

1. Va sur https://github.com
2. Clique sur "Sign up"
3. Crée ton compte (gratuit)
4. Confirme ton email

---

## 🎯 ÉTAPE 2 : CRÉER UN REPOSITORY

1. Une fois connecté, clique sur le **+** en haut à droite
2. Sélectionne **"New repository"**
3. Paramètres :
   - **Repository name** : `brvm-bot-web`
   - **Description** : `Analyse technique BRVM avec interface web`
   - **Public** (coché)
   - **Add README** (coché)
   - Clique sur **"Create repository"**

---

## 🎯 ÉTAPE 3 : UPLOADER LES FICHIERS

### Option A : Via l'interface web (plus simple)

1. Dans ton nouveau repository, clique sur **"Add file"** > **"Upload files"**

2. Upload ces fichiers :
   ```
   app.py
   brvm_bot_ultimate.py
   requirements_web.txt
   ```

3. Upload aussi le dossier **brvm_data/** complet :
   - Sélectionne tous les fichiers CSV dans brvm_data/
   - Upload-les dans un dossier brvm_data/

4. Clique sur **"Commit changes"**

### Option B : Via Git (plus avancé)

```bash
# Dans ton terminal Termux
cd ~/storage/shared/AppProjects/brvm_bot

# Initialiser Git
git init
git add app.py brvm_bot_ultimate.py requirements_web.txt brvm_data/
git commit -m "Initial commit - BRVM Bot Web"

# Lier au repository GitHub
git remote add origin https://github.com/TON_USERNAME/brvm-bot-web.git
git branch -M main
git push -u origin main
```

---

## 🎯 ÉTAPE 4 : DÉPLOYER SUR STREAMLIT CLOUD

1. Va sur https://streamlit.io/cloud

2. Clique sur **"Sign up"** ou **"Sign in with GitHub"**

3. Autorise Streamlit à accéder à ton compte GitHub

4. Clique sur **"New app"**

5. Configuration :
   - **Repository** : `TON_USERNAME/brvm-bot-web`
   - **Branch** : `main`
   - **Main file path** : `app.py`
   - **App URL** : `brvm-bot` (ou ce que tu veux)

6. Clique sur **"Deploy!"**

7. ⏳ Attends 2-3 minutes que l'app se déploie

8. 🎉 **C'EST EN LIGNE !**

---

## 🌐 TON APP EST DISPONIBLE À :

```
https://TON_APP_NAME.streamlit.app
```

Exemple : `https://brvm-bot.streamlit.app`

---

## 🔄 METTRE À JOUR L'APP

Chaque fois que tu modifies un fichier sur GitHub, l'app se met à jour automatiquement !

### Via l'interface GitHub :

1. Va sur ton repository
2. Clique sur le fichier à modifier
3. Clique sur l'icône ✏️ (Edit)
4. Fais tes modifications
5. Clique sur "Commit changes"
6. ✅ L'app se met à jour automatiquement en 1-2 minutes

### Via Git (Termux) :

```bash
cd ~/storage/shared/AppProjects/brvm_bot

# Modifier les fichiers localement
nano app.py  # ou autre

# Envoyer les modifications
git add .
git commit -m "Mise à jour de l'interface"
git push

# ✅ L'app se met à jour automatiquement
```

---

## 📊 FONCTIONNALITÉS DE L'INTERFACE

### Page 1 : Top Opportunités 🏆
- Affiche les meilleures opportunités d'achat
- Explications détaillées de chaque signal
- Informations de risk management
- Positions recommandées

### Page 2 : Analyse Détaillée 📊
- Tableau complet de toutes les entreprises
- Filtres par signal et score
- Export CSV
- Statistiques et graphiques

### Page 3 : Graphiques 📈
- Visualisation du prix avec moyennes mobiles
- Graphique RSI interactif
- Sélection d'entreprise
- Informations en temps réel

### Sidebar ⚙️
- Configuration du capital
- Filtres de signal
- Filtre de score minimum

---

## 🎨 PERSONNALISATION

### Changer le logo

Dans `app.py`, ligne ~55, remplace :
```python
st.image("https://via.placeholder.com/300x100/1f77b4/ffffff?text=BRVM+BOT")
```

Par ton propre logo :
```python
st.image("chemin/vers/ton/logo.png")
```

### Changer les couleurs

Modifie le CSS personnalisé dans `app.py` (lignes 25-50)

### Ajouter des fonctionnalités

Modifie `app.py` et commit sur GitHub !

---

## ⚠️ LIMITATIONS STREAMLIT CLOUD (Gratuit)

- ✅ Bande passante illimitée
- ✅ Uptime illimité
- ⚠️ 1 GB de RAM (largement suffisant pour ton app)
- ⚠️ Apps privées limitées (mais public = illimité)

---

## 🐛 DÉPANNAGE

### L'app ne démarre pas

1. Vérifie que tous les fichiers sont bien uploadés
2. Vérifie que `requirements_web.txt` est présent
3. Vérifie que le dossier `brvm_data/` contient les CSV
4. Consulte les logs dans Streamlit Cloud

### Erreur "Module not found"

Ajoute le module manquant dans `requirements_web.txt`

### Les données ne s'affichent pas

Vérifie que le dossier `brvm_data/` est bien présent sur GitHub

---

## 📱 PARTAGER TON APP

Ton app est publique et accessible à tous via :
```
https://TON_APP_NAME.streamlit.app
```

Tu peux partager ce lien :
- Sur WhatsApp
- Par email
- Sur les réseaux sociaux
- Au jury du concours !

---

## 🎯 PROCHAINES ÉTAPES

1. ✅ Déploie l'app
2. ✅ Teste toutes les fonctionnalités
3. ✅ Partage le lien avec le jury
4. 🏆 Impressionne tout le monde !

---

## 💡 SUPPORT

Si tu as des problèmes :
1. Consulte la documentation Streamlit : https://docs.streamlit.io
2. Vérifie les logs dans le dashboard Streamlit Cloud
3. Contacte le support Streamlit (très réactif)

---

**🎉 Bonne chance pour le concours !**

Les Bullionaires 🏆
