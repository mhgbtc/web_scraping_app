# Application de Web Scraping - Animaux

Application Streamlit pour scraper et analyser des données d'annonces d'animaux depuis CoinAfrique Sénégal.

## Fonctionnalités

1. **Scraper et nettoyer des données** : Scrape des annonces sur plusieurs pages
2. **Télécharger des données pré-scrapées** : Accède à des données déjà collectées
3. **Dashboard** : Visualise les statistiques des données
4. **Évaluation** : Formulaires pour évaluer l'application

## Installation locale

1. Clone ce repository
```bash
git clone <url-du-repo>
cd <nom-du-repo>
```

2. Installe les dépendances
```bash
pip install -r requirements.txt
```

3. Lance l'application
```bash
streamlit run app.py
```

## Déploiement sur Streamlit Cloud

1. Créer un compte sur [Streamlit Cloud](https://streamlit.io/cloud)

2. Connecter votre repository GitHub

3. Configurer le déploiement :
   - **Main file path**: `app.py`
   - **Python version**: 3.14.2 ou supérieur

4. Cliquer sur "Deploy"

## Technologies utilisées

- **Streamlit** : Framework pour l'interface web
- **BeautifulSoup** : Parsing HTML
- **Pandas** : Manipulation de données
- **Requests** : Requêtes HTTP
