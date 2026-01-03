import streamlit as st
import pandas as pd
from requests import get
from bs4 import BeautifulSoup as bs
import time
import re

# Je configure la page Streamlit
st.set_page_config(page_title="Application Web Scraping", layout="wide")

# Je crée le titre principal
st.title("Application de Web Scraping - Animaux")

# Je crée la sidebar avec le formulaire
st.sidebar.header("Configuration")

# Je crée le champ pour le nombre de pages
nombre_pages = st.sidebar.number_input(
    "Nombre de pages à scraper",
    min_value=1,
    max_value=100,
    value=1,
    step=1
)

# Je crée le selectbox pour les options
option_choisie = st.sidebar.selectbox(
    "Choisissez une option",
    [
        "Scraper et nettoyer des données",
        "Télécharger des données déjà scrapées",
        "Voir un dashboard des données",
        "Évaluer l'application"
    ]
)

# Je stocke le nombre de pages dans session_state
if 'nombre_pages' not in st.session_state:
    st.session_state.nombre_pages = nombre_pages
else:
    st.session_state.nombre_pages = nombre_pages

# Fonction pour scraper les données d'une catégorie
def scraper_categorie(url_base, nombre_pages, nom_colonne):
    """
    Scrape les données d'une catégorie d'animaux sur plusieurs pages
    """
    tous_les_items = []
    
    # Je crée une progress bar
    progress_bar = st.progress(0)
    status_text = st.empty()
    
    for page_num in range(1, nombre_pages + 1):
        # Je construis l'URL de la page
        if page_num == 1:
            url = url_base
        else:
            url = f"{url_base}?page={page_num}"
        
        status_text.text(f"Je scrape la page {page_num}/{nombre_pages}...")
        
        try:
            # Je fais la requête HTTP avec un User-Agent : Permet d'éviter d'être bloqué par le site
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
            }
            response = get(url, headers=headers)
            
            # Je parse le HTML avec BeautifulSoup
            soup = bs(response.content, 'html.parser')
            
            # Je trouve toutes les cartes d'annonces selon la structure HTML
            cartes = soup.find_all('div', 'col s6 m4 l3')
            
            status_text.text(f"Je scrape la page {page_num}/{nombre_pages}... {len(cartes)} annonces trouvées")
            
            # Je boucle sur chaque carte
            for idx, carte in enumerate(cartes):
                try:
                    # Je vérifie si je dois récupérer le détail du produit
                    if nom_colonne == "Details":
                        # Je récupère le lien vers la page de détail
                        lien_element = carte.find('a', 'card-image ad__card-image waves-block waves-light')
                        if lien_element:
                            carte_lien = 'https://sn.coinafrique.com' + lien_element.get('href')
                            
                            status_text.text(f"Page {page_num}/{nombre_pages} - Annonce {idx+1}/{len(cartes)} - Récupération du détail...")
                            
                            # Je fais une requête pour récupérer la page de détail
                            response_detail = get(carte_lien, headers=headers, timeout=10)
                            soup_detail = bs(response_detail.content, 'html.parser')
                            
                            # Je récupère le détail du produit
                            detail_box = soup_detail.find('div', 'ad__info__box ad__info__box-descriptions')
                            
                            # Je récupère tous les paragraphes
                            paragraphes = detail_box.find_all('p')
                            # Le premier p contient "Détails du produit", je prends le deuxième
                            nom = paragraphes[1].text.strip()
                            
                            # J'attends un peu pour ne pas surcharger le serveur
                            time.sleep(1)
                        else:
                            # Si je ne trouve pas le lien, je prends le nom de la carte
                            nom = carte.find('p', 'ad__card-description').text.strip()
                    else:
                        # Je récupère simplement le nom depuis ad__card-description
                        nom = carte.find('p', 'ad__card-description').text.strip()
                    
                    # J'extrais le prix depuis ad__card-price
                    prix = carte.find('p', class_='ad__card-price').text.strip('CFA')
                    
                    # J'extrais l'adresse depuis ad__card-location
                    adresse = carte.find('p', class_='ad__card-location').find('span').text.strip()
                    
                    # J'extrais l'image depuis ad__card-img
                    image_lien = carte.find('img', 'ad__card-img').get('src')
                    
                    # J'ajoute les données à ma liste seulement si j'ai au moins un nom
                    tous_les_items.append({
                        nom_colonne: nom,
                        'Prix': prix,
                        'Adresse': adresse,
                        'Image_lien': image_lien
                    })
                    
                except Exception as e:
                    # Je continue si une annonce pose problème
                    continue
            
            # Je mets à jour la progress bar
            progress_bar.progress(page_num / nombre_pages)
            
            # J'attends un peu entre chaque page pour ne pas surcharger le serveur
            time.sleep(2)
            
        except Exception as e:
            st.error(f"Erreur lors du scraping de la page {page_num}: {str(e)}")
            continue
    
    progress_bar.empty()
    status_text.empty()
    
    return tous_les_items

# Fonction pour nettoyer les données
def nettoyer_donnees(df):
    """
    Nettoie les données scrapées
    """
    # Je supprime les doublons
    df = df.drop_duplicates()
    
    # Je nettoie les prix avant de les convertir en numérique
    if 'Prix' in df.columns:
        # Je garde seulement les chiffres du prix
        df['Prix_nettoye'] = df['Prix'].str.replace(r'[^\d]', '', regex=True)
        # Je convertis en numérique
        df['Prix_nettoye'] = pd.to_numeric(df['Prix_nettoye'], errors='coerce').fillna(0).astype(int)
    
    # Je nettoie les adresses (supprime espaces superflus)
    if 'Adresse' in df.columns:
        df['Adresse'] = df['Adresse'].str.strip().str.replace(r'\s+', ' ', regex=True)
    
    # Je sélectionne et traite les colonnes numériques en une seule opération
    colonne_numeriques = df.select_dtypes(include=['number']).columns
    if len(colonne_numeriques) > 0:
        df[colonne_numeriques] = df[colonne_numeriques].fillna(df[colonne_numeriques].median())
    
    # Je sélectionne et traite les colonnes textes en une seule opération
    colonne_textes = df.select_dtypes(include=['object']).columns
    if len(colonne_textes) > 0:
        df[colonne_textes] = df[colonne_textes].fillna('N/A')
    
    # Je supprime les lignes complètement vides
    df = df.dropna(how='all')
    
    return df

# OPTION 1: Scraper et nettoyer des données
if option_choisie == "Scraper et nettoyer des données":
    st.header("Scraper et nettoyer des données")
    st.write(f"Nombre de pages sélectionnées: {st.session_state.nombre_pages}")
    
    # Je crée 4 colonnes pour les boutons
    col1, col2, col3, col4 = st.columns(4)
    
    # Je réinitialise le flag de scraping si le nombre de pages change
    if 'nombre_pages_precedent' not in st.session_state:
        st.session_state.nombre_pages_precedent = nombre_pages
    
    if st.session_state.nombre_pages_precedent != nombre_pages:
        st.session_state.nombre_pages_precedent = nombre_pages
        # Je supprime la catégorie pour forcer un nouveau clic
        if 'categorie' in st.session_state:
            del st.session_state.categorie
        if 'scraping_lance' in st.session_state:
            del st.session_state.scraping_lance
    
    with col1:
        if st.button("Données sur les chiens", width='stretch'):
            st.session_state.categorie = "chiens"
            st.session_state.scraping_lance = True
            
    with col2:
        if st.button("Données sur les moutons", width='stretch'):
            st.session_state.categorie = "moutons"
            st.session_state.scraping_lance = True
            
    with col3:
        if st.button("Poules, lapins et pigeons", width='stretch'):
            st.session_state.categorie = "poules"
            st.session_state.scraping_lance = True            
    with col4:
        if st.button("Autres animaux", width='stretch'):
            st.session_state.categorie = "autres"
            st.session_state.scraping_lance = True
    
    # Je gère le scraping selon la catégorie choisie
    if 'categorie' in st.session_state and 'scraping_lance' in st.session_state and st.session_state.scraping_lance:
        categorie = st.session_state.categorie
        
        # Je définis les URLs et noms de colonnes
        urls_config = {
            "chiens": {
                "url": "https://sn.coinafrique.com/categorie/chiens",
                "nom_colonne": "Nom"
            },
            "moutons": {
                "url": "https://sn.coinafrique.com/categorie/moutons",
                "nom_colonne": "Nom"
            },
            "poules": {
                "url": "https://sn.coinafrique.com/categorie/poules-lapins-et-pigeons",
                "nom_colonne": "Details"
            },
            "autres": {
                "url": "https://sn.coinafrique.com/categorie/autres-animaux",
                "nom_colonne": "Nom"
            }
        }
        
        config = urls_config[categorie]
        
        st.subheader(f"Scraping des données: {categorie.capitalize()}")
        
        with st.spinner("Je scrape les données..."):
            # Je scrape les données
            donnees = scraper_categorie(
                config['url'],
                st.session_state.nombre_pages,
                config['nom_colonne']
            )
            
            if donnees:
                # Je crée un DataFrame
                df = pd.DataFrame(donnees)
                
                # Je nettoie les données
                df_nettoye = nettoyer_donnees(df)
                
                st.success(f"J'ai scrapé {len(df_nettoye)} annonces!")
                
                # J'affiche les données
                st.subheader("Données nettoyées")
                st.dataframe(df_nettoye, width='stretch')
                
                # Je réinitialise le flag de scraping pour permettre un nouveau scraping
                st.session_state.scraping_lance = False
                
            else:
                st.warning("Aucune donnée n'a été scrapée. Le site a peut-être changé de structure.")

# OPTION 2: Télécharger des données déjà scrapées
elif option_choisie == "Télécharger des données déjà scrapées":
    st.header("Télécharger des données déjà scrapées (Web Scraper)")
    
    st.info("Cette section permet de télécharger des données qui ont été préalablement scrapées avec Web Scraper (extension Chrome).")
    
    # Je définis les chemins vers les fichiers CSV
    fichiers_csv = {
        "chiens": "data/chiens.csv",
        "moutons": "data/moutons.csv",
        "poules": "data/poules.csv",
        "autres": "data/autres.csv"
    }
    
    # Je charge les données depuis les fichiers CSV
    donnees_brutes = {}
    fichiers_manquants = []
    
    for categorie, chemin in fichiers_csv.items():
        try:
            # Je charge le fichier CSV
            df = pd.read_csv(chemin)
            
            # Je supprime les colonnes ajoutées par Web Scraper (web-scraper-order et web-scraper-start-url)
            if 'web_scraper_order' in df.columns:
                df = df.drop('web_scraper_order', axis=1)
            if 'web_scraper_start_url' in df.columns:
                df = df.drop('web_scraper_start_url', axis=1)
            if 'lien_detail' in df.columns:
                df = df.drop('lien_detail', axis=1)
            
            donnees_brutes[categorie] = df
        except FileNotFoundError:
            # Si le fichier n'existe pas, je note qu'il est manquant
            fichiers_manquants.append(categorie)
            donnees_brutes[categorie] = None
    
    # J'affiche un avertissement si des fichiers sont manquants
    if fichiers_manquants:
        st.warning(f"Fichiers manquants: {', '.join(fichiers_manquants)}. Veuillez scraper ces données avec Web Scraper et les placer dans le dossier 'data/'.")
    
    # Je crée des onglets pour chaque catégorie
    tab1, tab2, tab3, tab4 = st.tabs(["Chiens", "Moutons", "Poules/Lapins/Pigeons", "Autres animaux"])
    
    with tab1:
        st.subheader("Données brutes - Chiens")
        if donnees_brutes["chiens"] is not None:
            st.dataframe(donnees_brutes["chiens"], use_container_width=True)
            
            # J'affiche le nombre de lignes
            st.caption(f"{len(donnees_brutes['chiens'])} annonces trouvées")
            
            # Je permets le téléchargement
            csv = donnees_brutes["chiens"].to_csv(index=False).encode('utf-8')
            st.download_button(
                label="Télécharger (CSV)",
                data=csv,
                file_name="donnees_chiens_brutes.csv",
                mime="text/csv",
                key="btn_chiens"
            )
        else:
            st.error("Fichier 'chiens.csv' non trouvé dans le dossier 'data/'")
    
    with tab2:
        st.subheader("Données brutes - Moutons")
        if donnees_brutes["moutons"] is not None:
            st.dataframe(donnees_brutes["moutons"], use_container_width=True)
            st.caption(f"{len(donnees_brutes['moutons'])} annonces trouvées")
            
            csv = donnees_brutes["moutons"].to_csv(index=False).encode('utf-8')
            st.download_button(
                label="Télécharger (CSV)",
                data=csv,
                file_name="donnees_moutons_brutes.csv",
                mime="text/csv",
                key="btn_moutons"
            )
        else:
            st.error("Fichier 'moutons.csv' non trouvé dans le dossier 'data/'")
    
    with tab3:
        st.subheader("Données brutes - Poules/Lapins/Pigeons")
        if donnees_brutes["poules"] is not None:
            st.dataframe(donnees_brutes["poules"], use_container_width=True)
            st.caption(f"{len(donnees_brutes['poules'])} annonces trouvées")
            
            csv = donnees_brutes["poules"].to_csv(index=False).encode('utf-8')
            st.download_button(
                label="Télécharger (CSV)",
                data=csv,
                file_name="donnees_poules_brutes.csv",
                mime="text/csv",
                key="btn_poules"
            )
        else:
            st.error("Fichier 'poules.csv' non trouvé dans le dossier 'data/'")
    
    with tab4:
        st.subheader("Données brutes - Autres animaux")
        if donnees_brutes["autres"] is not None:
            st.dataframe(donnees_brutes["autres"], use_container_width=True)
            st.caption(f"{len(donnees_brutes['autres'])} annonces trouvées")
            
            csv = donnees_brutes["autres"].to_csv(index=False).encode('utf-8')
            st.download_button(
                label="Télécharger (CSV)",
                data=csv,
                file_name="donnees_autres_brutes.csv",
                mime="text/csv",
                key="btn_autres"
            )
        else:
            st.error("Fichier 'autres.csv' non trouvé dans le dossier 'data/'")

# OPTION 3: Voir un dashboard des données
elif option_choisie == "Voir un dashboard des données":
    st.header("Dashboard des données nettoyées")
    
    # Je définis les chemins vers les fichiers CSV
    fichiers_csv = {
        "chiens": "data/chiens.csv",
        "moutons": "data/moutons.csv",
        "poules": "data/poules.csv",
        "autres": "data/autres.csv"
    }
    
    # Je charge et nettoie les données depuis les fichiers CSV
    donnees_nettoyees = {}
    fichiers_manquants = []
    
    for categorie, chemin in fichiers_csv.items():
        try:
            # Je charge le fichier CSV
            df = pd.read_csv(chemin)
            
            # Je supprime les colonnes ajoutées par Web Scraper
            if 'web_scraper_order' in df.columns:
                df = df.drop('web_scraper_order', axis=1)
            if 'web_scraper_start_url' in df.columns:
                df = df.drop('web_scraper_start_url', axis=1)
            if 'lien_detail' in df.columns:
                df = df.drop('lien_detail', axis=1)
            
            # Je nettoie les données
            df_nettoye = nettoyer_donnees(df)
            
            donnees_nettoyees[categorie] = df_nettoye
        except FileNotFoundError:
            # Si le fichier n'existe pas, je note qu'il est manquant
            fichiers_manquants.append(categorie)
            donnees_nettoyees[categorie] = None
    
    # J'affiche un avertissement si des fichiers sont manquants
    if fichiers_manquants:
        st.warning(f"Fichiers manquants: {', '.join(fichiers_manquants)}. Veuillez scraper ces données avec Web Scraper et les placer dans le dossier 'data/'.")
    
    # Je crée un selectbox pour choisir la catégorie
    categorie_dashboard = st.selectbox(
        "Choisissez une catégorie à visualiser",
        ["Chiens", "Moutons", "Poules/Lapins/Pigeons", "Autres animaux"]
    )
    
    # Je mappe la sélection
    mapping = {
        "Chiens": "chiens",
        "Moutons": "moutons",
        "Poules/Lapins/Pigeons": "poules",
        "Autres animaux": "autres"
    }
    
    categorie_selectionnee = mapping[categorie_dashboard]
    
    # Je vérifie si les données sont disponibles
    if donnees_nettoyees[categorie_selectionnee] is not None:
        df_selected = donnees_nettoyees[categorie_selectionnee]
        
        # J'affiche le tableau de données
        st.subheader("Tableau des données")
        st.dataframe(df_selected, use_container_width=True)
        
        # J'affiche un graphique simple avec les prix
        if 'Prix_nettoye' in df_selected.columns:
            st.subheader("Distribution des prix")
            
            # Je filtre les prix valides (supérieurs à 0)
            df_prix = df_selected[df_selected['Prix_nettoye'] > 0].copy()
            
            if len(df_prix) > 0:
                # Je prends la première colonne (Nom ou Details) comme index
                premiere_colonne = df_prix.columns[0]
                
                # Je limite à 20 premières lignes pour la lisibilité
                if len(df_prix) > 20:
                    df_prix = df_prix.head(20)
                    st.caption("Affichage des 20 premières annonces")
                
                st.bar_chart(df_prix.set_index(premiere_colonne)['Prix_nettoye'])
            else:
                st.info("Aucun prix valide à afficher")
        
        # J'affiche la répartition par ville
        if 'Adresse' in df_selected.columns:
            st.subheader("Répartition géographique")
            
            # Je filtre les adresses valides
            adresses_valides = df_selected[df_selected['Adresse'] != 'N/A']['Adresse']
            
            if len(adresses_valides) > 0:
                ville_counts = adresses_valides.value_counts()
                st.bar_chart(ville_counts)
            else:
                st.info("Aucune adresse valide à afficher")
    else:
        st.error(f"Fichier '{categorie_selectionnee}.csv' non trouvé dans le dossier 'data/'")

# OPTION 4: Formulaire d'évaluation
elif option_choisie == "Évaluer l'application":
    st.header("Évaluation de l'application")
    
    st.write("---")
    
    st.write("Merci d'évaluer cette application de web scraping!")
    
    st.write("---")
    
    # Je crée deux colonnes pour les deux options
    col1, col2 = st.columns(2)
    
    with col1:
        st.write("Cliquez sur le lien ci-dessous pour remplir le formulaire via Kobo Toolbox:")
        
        # Je crée un lien fictif (à remplacer par ton vrai lien Kobo)
        kobo_link = "https://ee.kobotoolbox.org/x/PvlymFPC"
        st.markdown(f"""
            <a href="{kobo_link}" target="_blank" style="text-decoration: none;">
                <button style="background-color: #0066cc; color: white; padding: 15px 32px; 
                              font-size: 16px; border: none; border-radius: 4px; cursor: pointer;">
                    Ouvrir le formulaire Kobo
                </button>
            </a>
        """, unsafe_allow_html=True)
    
    with col2:
        st.write("Cliquez sur le lien ci-dessous pour remplir le formulaire via Google Forms:")
        
        # Je crée un lien fictif (à remplacer par ton vrai lien Google Forms)
        google_link = "https://forms.gle/g3ai6HqfGkWU5WzD9"
        st.markdown(f"""
            <a href="{google_link}" target="_blank" style="text-decoration: none;">
                <button style="background-color: #34a853; color: white; padding: 15px 32px; 
                              font-size: 16px; border: none; border-radius: 4px; cursor: pointer;">
                    Ouvrir le formulaire Google
                </button>
            </a>
        """, unsafe_allow_html=True)
    
    st.write("---")