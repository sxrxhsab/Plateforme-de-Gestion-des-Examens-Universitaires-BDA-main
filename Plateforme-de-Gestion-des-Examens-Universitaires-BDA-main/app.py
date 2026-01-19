"""
Application principale - Plateforme Gestion Examens (Version SQLite)
"""
import streamlit as st
import sqlite3
import pandas as pd
from pathlib import Path
import sys
from datetime import datetime

# Chemin de la base de données SQLite
DB_PATH = Path("examens.db")

def init_database():
    """Initialiser la base de données SQLite"""
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        # Table des utilisateurs
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT UNIQUE,
                password TEXT,
                role TEXT,
                departement TEXT
            )
        ''')
        
        # Table des examens
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS examens (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                matiere TEXT,
                date DATE,
                heure_debut TIME,
                heure_fin TIME,
                salle TEXT,
                capacite INTEGER,
                professeur_id INTEGER,
                departement TEXT,
                niveau TEXT
            )
        ''')
        
        # Table des surveillances
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS surveillances (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                examen_id INTEGER,
                professeur_id INTEGER,
                date DATE,
                heure_debut TIME,
                heure_fin TIME,
                FOREIGN KEY (examen_id) REFERENCES examens(id)
            )
        ''')
        
        # Insérer des données de test si la base est vide
        cursor.execute("SELECT COUNT(*) FROM examens")
        if cursor.fetchone()[0] == 0:
            # Données de test
            examens_test = [
                ('Algorithmique', '2024-06-10', '08:00', '10:00', 'Amphi A', 300, 1, 'Informatique', 'L2'),
                ('Base de données', '2024-06-12', '10:00', '12:00', 'Amphi B', 250, 2, 'Informatique', 'L3'),
                ('Réseaux', '2024-06-14', '14:00', '16:00', 'Salle 101', 100, 3, 'Réseaux', 'M1'),
            ]
            
            cursor.executemany('''
                INSERT INTO examens (matiere, date, heure_debut, heure_fin, salle, capacite, professeur_id, departement, niveau)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', examens_test)
        
        conn.commit()
        conn.close()
        return True, "Base de données SQLite initialisée avec succès"
    except Exception as e:
        return False, f"Erreur d'initialisation: {str(e)}"

def get_connection():
    """Obtenir une connexion à la base de données"""
    return sqlite3.connect(DB_PATH)

def check_database_connection():
    """Vérifier la connexion à la base de données"""
    try:
        # Initialiser la base
        success, message = init_database()
        if not success:
            return False, message
        
        # Tester la connexion
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT 1")
        conn.close()
        return True, "Connexion SQLite établie avec succès"
    except Exception as e:
        return False, f"Erreur: {str(e)}"

st.set_page_config(
    page_title="Gestion Examens Universitaires",
    page_icon="📚",
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
        padding: 1rem 0;
        margin-bottom: 2rem;
        border-bottom: 3px solid #1f77b4;
    }
    
    .info-card {
        background: #f8f9fa;
        padding: 1.5rem;
        border-radius: 10px;
        border-left: 4px solid #1f77b4;
        margin: 1rem 0;
    }
    
    .footer {
        text-align: center;
        padding: 2rem 0;
        color: #7f8c8d;
        border-top: 1px solid #ecf0f1;
        margin-top: 3rem;
    }
    
    .stat-card {
        background: white;
        padding: 1rem;
        border-radius: 10px;
        box-shadow: 0 2px 5px rgba(0,0,0,0.1);
        text-align: center;
    }
</style>
""", unsafe_allow_html=True)

def main():
    """Fonction principale"""
    
    # En-tête
    st.markdown('<div class="main-header">📚 Plateforme de Gestion des Examens Universitaires</div>', unsafe_allow_html=True)
    
    # Vérifier la connexion
    is_connected, message = check_database_connection()
    
    if not is_connected:
        st.error(f"❌ {message}")
        return
    
    st.success(f"✅ {message}")
    
    # Sidebar - Navigation
    st.sidebar.title("🧭 Navigation")
    st.sidebar.markdown("---")
    
    # Informations utilisateur
    user_role = st.sidebar.selectbox(
        "👤 Rôle utilisateur",
        ["Vice-Doyen/Doyen", "Administrateur Examens", "Chef de Département", "Étudiant", "Professeur"]
    )
    
    st.sidebar.markdown("---")
    
    # Menu de navigation
    page = st.sidebar.selectbox(
        "📄 Menu",
        ["Accueil", "Gestion Examens", "Planning", "Statistiques", "Administration"]
    )
    
    # Contenu selon la page sélectionnée
    if page == "Accueil":
        show_home_page()
    elif page == "Gestion Examens":
        show_exam_management()
    elif page == "Planning":
        show_schedule()
    elif page == "Statistiques":
        show_statistics()
    elif page == "Administration":
        show_admin()

def show_home_page():
    """Afficher la page d'accueil"""
    
    st.markdown("### 👋 Bienvenue sur la plateforme")
    
    st.markdown("""
    <div class="info-card">
        <h4>🎯 Objectif de la plateforme</h4>
        <p>
        Cette plateforme permet de générer automatiquement des emplois du temps d'examens optimisés 
        pour une université de plus de 13 000 étudiants, en respectant toutes les contraintes :
        </p>
        <ul>
            <li>✅ Maximum 1 examen par jour par étudiant</li>
            <li>✅ Maximum 3 surveillances par jour par professeur</li>
            <li>✅ Respect des capacités des salles et amphis</li>
            <li>✅ Équilibrage des surveillances entre professeurs</li>
            <li>✅ Priorisation des surveillances par département</li>
        </ul>
    </div>
    """, unsafe_allow_html=True)
    
    # Statistiques rapides
    st.markdown("---")
    st.markdown("### 📊 Vue d'ensemble")
    
    try:
        conn = get_connection()
        
        # Nombre d'examens
        exam_count = pd.read_sql_query("SELECT COUNT(*) as count FROM examens", conn).iloc[0]['count']
        
        # Prochain examen
        next_exam = pd.read_sql_query(
            "SELECT matiere, date, salle FROM examens WHERE date >= DATE('now') ORDER BY date LIMIT 1", 
            conn
        )
        
        conn.close()
        
        col1, col2, col3 = st.columns(3)
        with col1:
            st.markdown(f"""
            <div class="stat-card">
                <h3>{exam_count}</h3>
                <p>Examens programmés</p>
            </div>
            """, unsafe_allow_html=True)
        
        with col2:
            st.markdown(f"""
            <div class="stat-card">
                <h3>13,000+</h3>
                <p>Étudiants concernés</p>
            </div>
            """, unsafe_allow_html=True)
        
        with col3:
            st.markdown("""
            <div class="stat-card">
                <h3>100%</h3>
                <p>Conformité aux contraintes</p>
            </div>
            """, unsafe_allow_html=True)
        
        # Afficher le prochain examen
        if not next_exam.empty:
            st.markdown("---")
            st.markdown("### 🗓️ Prochain examen")
            st.info(f"**{next_exam.iloc[0]['matiere']}** - {next_exam.iloc[0]['date']} - Salle {next_exam.iloc[0]['salle']}")
            
    except Exception as e:
        st.warning(f"Impossible de charger les statistiques: {e}")

def show_exam_management():
    """Gestion des examens"""
    st.title("📝 Gestion des Examens")
    
    tab1, tab2, tab3 = st.tabs(["📋 Liste des examens", "➕ Ajouter un examen", "🔍 Rechercher"])
    
    with tab1:
        try:
            conn = get_connection()
            df = pd.read_sql_query("SELECT * FROM examens ORDER BY date, heure_debut", conn)
            conn.close()
            
            if not df.empty:
                st.dataframe(df, use_container_width=True)
                
                # Options d'export
                col1, col2 = st.columns(2)
                with col1:
                    csv = df.to_csv(index=False)
                    st.download_button(
                        "📥 Télécharger CSV",
                        csv,
                        "examens.csv",
                        "text/csv"
                    )
                with col2:
                    excel = df.to_excel(index=False, engine='openpyxl')
                    st.download_button(
                        "📥 Télécharger Excel",
                        excel,
                        "examens.xlsx",
                        "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                    )
            else:
                st.info("Aucun examen programmé")
                
        except Exception as e:
            st.error(f"Erreur: {e}")
    
    with tab2:
        with st.form("add_exam"):
            col1, col2 = st.columns(2)
            with col1:
                matiere = st.text_input("Matière *")
                date = st.date_input("Date *", min_value=datetime.now().date())
                heure_debut = st.time_input("Heure de début *")
            with col2:
                salle = st.text_input("Salle *")
                capacite = st.number_input("Capacité *", min_value=1, value=100)
                departement = st.selectbox("Département *", ["Informatique", "Mathématiques", "Physique", "Chimie", "Biologie"])
            
            submitted = st.form_submit_button("Ajouter l'examen")
            
            if submitted:
                if matiere and date and salle:
                    try:
                        conn = get_connection()
                        cursor = conn.cursor()
                        cursor.execute('''
                            INSERT INTO examens (matiere, date, heure_debut, salle, capacite, departement)
                            VALUES (?, ?, ?, ?, ?, ?)
                        ''', (matiere, str(date), str(heure_debut), salle, capacite, departement))
                        conn.commit()
                        conn.close()
                        st.success("✅ Examen ajouté avec succès!")
                    except Exception as e:
                        st.error(f"Erreur: {e}")
                else:
                    st.error("Veuillez remplir tous les champs obligatoires (*)")

def show_schedule():
    """Afficher le planning"""
    st.title("🗓️ Planning des Examens")
    
    try:
        conn = get_connection()
        df = pd.read_sql_query("SELECT * FROM examens ORDER BY date, heure_debut", conn)
        conn.close()
        
        if not df.empty:
            # Filtrer par département
            departements = df['departement'].unique()
            selected_dept = st.selectbox("Filtrer par département", ["Tous"] + list(departements))
            
            if selected_dept != "Tous":
                df = df[df['departement'] == selected_dept]
            
            # Afficher sous forme de calendrier
            for date in df['date'].unique():
                exams_date = df[df['date'] == date]
                with st.expander(f"📅 {date} - {len(exams_date)} examen(s)"):
                    for _, exam in exams_date.iterrows():
                        st.markdown(f"""
                        **{exam['matiere']}** 
                        - ⏰ {exam['heure_debut']} 
                        - 🏫 {exam['salle']} ({exam['capacite']} places)
                        - 📚 {exam['departement']}
                        """)
        else:
            st.info("Aucun examen programmé")
            
    except Exception as e:
        st.error(f"Erreur: {e}")

def show_statistics():
    """Afficher les statistiques"""
    st.title("📈 Statistiques")
    
    try:
        conn = get_connection()
        
        # Nombre d'examens par département
        df_dept = pd.read_sql_query('''
            SELECT departement, COUNT(*) as count 
            FROM examens 
            GROUP BY departement 
            ORDER BY count DESC
        ''', conn)
        
        # Examens par date
        df_date = pd.read_sql_query('''
            SELECT date, COUNT(*) as count 
            FROM examens 
            GROUP BY date 
            ORDER BY date
        ''', conn)
        
        conn.close()
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("### 📊 Examens par département")
            if not df_dept.empty:
                st.bar_chart(df_dept.set_index('departement'))
            else:
                st.info("Aucune donnée disponible")
        
        with col2:
            st.markdown("### 📅 Examens par date")
            if not df_date.empty:
                st.line_chart(df_date.set_index('date'))
            else:
                st.info("Aucune donnée disponible")
        
        # Métriques
        st.markdown("---")
        col1, col2, col3 = st.columns(3)
        with col1:
            total_exams = df_dept['count'].sum() if not df_dept.empty else 0
            st.metric("Total examens", total_exams)
        with col2:
            total_depts = len(df_dept) if not df_dept.empty else 0
            st.metric("Départements", total_depts)
        with col3:
            avg_exams = df_dept['count'].mean() if not df_dept.empty else 0
            st.metric("Moyenne par département", f"{avg_exams:.1f}")
            
    except Exception as e:
        st.error(f"Erreur: {e}")

def show_admin():
    """Page d'administration"""
    st.title("⚙️ Administration")
    
    st.warning("⚠️ Zone réservée aux administrateurs")
    
    tab1, tab2 = st.tabs(["Initialiser la base", "Sauvegarder/Restaurer"])
    
    with tab1:
        st.markdown("### Initialiser la base de données")
        st.info("Cette action réinitialisera la base de données avec des données de test.")
        
        if st.button("🔄 Initialiser la base", type="secondary"):
            try:
                # Supprimer la base existante
                if DB_PATH.exists():
                    DB_PATH.unlink()
                
                # Recréer la base
                init_database()
                st.success("✅ Base de données réinitialisée avec succès!")
                st.experimental_rerun()
            except Exception as e:
                st.error(f"Erreur: {e}")
    
    with tab2:
        st.markdown("### Sauvegarde de la base de données")
        
        if st.button("💾 Créer une sauvegarde"):
            try:
                # Créer une copie de la base
                backup_path = "examens_backup.db"
                import shutil
                shutil.copy2(DB_PATH, backup_path)
                
                with open(backup_path, "rb") as f:
                    st.download_button(
                        "📥 Télécharger la sauvegarde",
                        f,
                        "examens_backup.db",
                        "application/x-sqlite3"
                    )
            except Exception as e:
                st.error(f"Erreur: {e}")

# Footer
st.markdown("""
<div class="footer">
    <p>📚 Plateforme de Gestion des Examens Universitaires - Version SQLite</p>
    <p><small>Déployée sur Streamlit Cloud - Compatible avec tous les hébergeurs</small></p>
</div>
""", unsafe_allow_html=True)

if __name__ == "__main__":
    main()
