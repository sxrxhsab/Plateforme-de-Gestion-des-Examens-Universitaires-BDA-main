"""
Page Professeur - Mon Planning de Surveillance
🔥 AUTHENTIFICATION PAR EMAIL UNIQUEMENT
✅ Interface épurée
"""
import streamlit as st
import sys
from pathlib import Path
import pandas as pd
from datetime import datetime

sys.path.insert(0, str(Path(__file__).parent.parent))

from backend.db_connection import db

st.set_page_config(
    page_title="Espace Professeur",
    page_icon="👨‍🏫",
    layout="wide"
)

# ========== AUTHENTIFICATION ==========

def authenticate_professor(email):
    """Authentifier un professeur par son email"""
    query = """
    SELECT 
        p.id,
        p.nom,
        p.prenom,
        p.email,
        d.nom as departement,
        d.id as dept_id,
        d.code as dept_code,
        p.specialite
    FROM professeurs p
    JOIN departements d ON p.dept_id = d.id
    WHERE p.email = %s
    """
    result = db.execute_query(query, (email,))
    return result[0] if result else None

def login_page():
    """Page de connexion avec email uniquement"""
    st.title("👨‍🏫 Espace Professeur")
    st.markdown("### Connexion sécurisée")
    st.markdown("---")
    
    col1, col2, col3 = st.columns([1, 2, 1])
    
    with col2:
        st.markdown("#### 🔐 Authentification")
        st.info("💡 Connectez-vous avec votre email professionnel")
        
        email = st.text_input(
            "Email professionnel",
            placeholder="prenom.nom@univ-prof.dz"
        )
        
        if st.button("🔓 Se connecter", use_container_width=True, type="primary"):
            if not email or "@" not in email:
                st.error("❌ Email invalide")
            else:
                with st.spinner("🔍 Vérification..."):
                    prof = authenticate_professor(email)
                    if prof:
                        st.session_state['authenticated'] = True
                        st.session_state['professor'] = prof
                        st.success(f"✅ Bienvenue {prof['prenom']} {prof['nom']}")
                        st.rerun()
                    else:
                        st.error("❌ Email non trouvé dans le système")

# ========== FONCTIONS DE DONNÉES ==========

def get_professor_surveillances(prof_id, dept_filter=None, date_debut=None, date_fin=None):
    """Obtenir les surveillances d'un professeur avec filtres"""
    query = """
    SELECT 
        e.id as examen_id,
        e.date_heure,
        DATE_ADD(e.date_heure, INTERVAL e.duree_minutes MINUTE) as heure_fin,
        m.nom as module,
        m.code as code_module,
        f.nom as formation,
        f.niveau,
        d.nom as departement,
        d.code as code_dept,
        s.nom as salle,
        s.type as type_salle,
        s.capacite as capacite_salle,
        g.nom as groupe,
        e.nb_etudiants,
        e.duree_minutes
    FROM examens e
    JOIN modules m ON e.module_id = m.id
    JOIN formations f ON m.formation_id = f.id
    JOIN departements d ON f.dept_id = d.id
    JOIN salles s ON e.salle_id = s.id
    LEFT JOIN groupes g ON e.groupe_id = g.id
    WHERE e.prof_id = %s
    AND e.statut = 'planifie'
    """
    
    params = [prof_id]
    
    if dept_filter:
        query += " AND d.id = %s"
        params.append(dept_filter)
    
    if date_debut:
        query += " AND DATE(e.date_heure) >= %s"
        params.append(date_debut)
    
    if date_fin:
        query += " AND DATE(e.date_heure) <= %s"
        params.append(date_fin)
    
    query += " ORDER BY e.date_heure"
    
    return db.execute_query(query, tuple(params))

def get_professor_stats(prof_id):
    """Statistiques globales du professeur"""
    query = """
    SELECT 
        COUNT(DISTINCT e.id) as total_surveillances,
        COUNT(DISTINCT DATE(e.date_heure)) as nb_jours,
        COUNT(DISTINCT d.id) as nb_departements,
        MIN(e.date_heure) as premiere_surveillance,
        MAX(e.date_heure) as derniere_surveillance,
        SUM(e.nb_etudiants) as total_etudiants_surveilles
    FROM examens e
    JOIN modules m ON e.module_id = m.id
    JOIN formations f ON m.formation_id = f.id
    JOIN departements d ON f.dept_id = d.id
    WHERE e.prof_id = %s AND e.statut = 'planifie'
    """
    result = db.execute_query(query, (prof_id,))
    return result[0] if result else None

def get_surveillances_by_department(prof_id):
    """Répartition des surveillances par département"""
    query = """
    SELECT 
        d.nom as departement,
        d.id as dept_id,
        COUNT(DISTINCT e.id) as nb_surveillances,
        COUNT(DISTINCT DATE(e.date_heure)) as nb_jours
    FROM examens e
    JOIN modules m ON e.module_id = m.id
    JOIN formations f ON m.formation_id = f.id
    JOIN departements d ON f.dept_id = d.id
    WHERE e.prof_id = %s AND e.statut = 'planifie'
    GROUP BY d.id, d.nom
    ORDER BY nb_surveillances DESC
    """
    return db.execute_query(query, (prof_id,))

def check_overload_days(prof_id):
    """Vérifier les jours de surcharge (>3 surveillances)"""
    query = """
    SELECT 
        DATE(e.date_heure) as date,
        COUNT(DISTINCT e.id) as nb_surveillances,
        GROUP_CONCAT(DISTINCT m.nom ORDER BY e.date_heure SEPARATOR ' | ') as modules
    FROM examens e
    JOIN modules m ON e.module_id = m.id
    WHERE e.prof_id = %s AND e.statut = 'planifie'
    GROUP BY DATE(e.date_heure)
    HAVING COUNT(DISTINCT e.id) > 3
    ORDER BY date
    """
    return db.execute_query(query, (prof_id,))

# ========== PAGE PRINCIPALE ==========

def main_page():
    """Page principale après connexion"""
    prof = st.session_state['professor']
    prof_id = prof['id']
    
    # Header avec bouton déconnexion
    col1, col2 = st.columns([4, 1])
    
    with col1:
        st.title("👨‍🏫 Mon Espace Professeur")
        st.markdown(f"### Bienvenue, **{prof['prenom']} {prof['nom']}**")
    
    with col2:
        st.markdown("##")
        if st.button("🚪 Déconnexion", type="secondary"):
            st.session_state.clear()
            st.rerun()
    
    st.markdown(f"**Département:** {prof['departement']} ({prof['dept_code']})")
    st.markdown(f"**Email:** {prof['email']}")
    
    if prof['specialite']:
        st.markdown(f"**Spécialité:** {prof['specialite']}")
    
    st.markdown("---")
    
    # Vérifier les surcharges
    overload_days = check_overload_days(prof_id)
    if overload_days:
        st.error(f"⚠️ **ATTENTION:** Vous avez {len(overload_days)} jour(s) avec plus de 3 surveillances!")
        with st.expander("📋 Voir les détails"):
            for day in overload_days:
                st.warning(f"""
                **📅 {day['date'].strftime('%d/%m/%Y')}** : {day['nb_surveillances']} surveillances  
                **Modules:** {day['modules']}
                """)
    
    # Statistiques globales
    stats = get_professor_stats(prof_id)
    
    # Vérifier d'abord s'il y a des examens dans le système
    query_check = "SELECT COUNT(*) as total FROM examens WHERE statut = 'planifie'"
    total_examens = db.execute_query(query_check)
    nb_total_examens = total_examens[0]['total'] if total_examens else 0
    
    if stats and stats['total_surveillances'] > 0:
        st.markdown("#### 📊 Vue d'ensemble de mes surveillances")
        
        col1, col2, col3, col4, col5 = st.columns(5)
        
        with col1:
            st.metric("📝 Surveillances", stats['total_surveillances'])
        
        with col2:
            st.metric("📅 Jours", stats['nb_jours'])
        
        with col3:
            st.metric("🏢 Départements", stats['nb_departements'])
        
        with col4:
            avg_day = stats['total_surveillances'] / stats['nb_jours'] if stats['nb_jours'] > 0 else 0
            st.metric("📊 Moy/jour", f"{avg_day:.1f}")
        
        with col5:
            st.metric("👥 Total étudiants", stats['total_etudiants_surveilles'] or 0)
        
        st.markdown("---")
    else:
        if nb_total_examens == 0:
            st.warning("⚠️ Aucun examen n'a encore été planifié dans le système")
            st.info("""
            📋 **L'administration n'a pas encore généré le planning des examens.**
            
            Une fois que le planning sera généré par l'administrateur, vos surveillances apparaîtront automatiquement ici.
            """)
        else:
            st.info(f"ℹ️ Il y a {nb_total_examens} examen(s) planifié(s) dans le système, mais aucun ne vous est assigné pour le moment")
            st.markdown("""
            ### 💡 Que faire ?
            - L'administration est en train d'assigner les surveillances
            - Revenez consulter cette page régulièrement
            - Contactez le service de scolarité si vous avez des questions
            """)
        st.markdown("---")
        return
    
    # Charger départements où le prof surveille
    depts_prof = get_surveillances_by_department(prof_id)
    
    # Onglets
    tabs = st.tabs([
        "📅 Mon Planning",
        "📊 Par Département",
        "📈 Statistiques"
    ])
    
    with tabs[0]:
        # ========== PLANNING DÉTAILLÉ ==========
        st.subheader("📅 Mon planning de surveillance")
        
        # Filtres
        st.markdown("#### 🔎 Filtrer mon planning")
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            if depts_prof:
                dept_options = ["Tous les départements"] + [d['departement'] for d in depts_prof]
                selected_dept = st.selectbox("Département", dept_options)
                
                dept_filter = None
                if selected_dept != "Tous les départements":
                    dept_filter = next(d['dept_id'] for d in depts_prof if d['departement'] == selected_dept)
            else:
                st.selectbox("Département", ["Aucun"])
                dept_filter = None
        
        with col2:
            date_debut = st.date_input(
                "Date de début",
                value=None,
                help="Laisser vide pour voir toutes les dates"
            )
        
        with col3:
            date_fin = st.date_input(
                "Date de fin",
                value=None,
                help="Laisser vide pour voir toutes les dates"
            )
        
        st.markdown("---")
        
        surveillances = get_professor_surveillances(
            prof_id, 
            dept_filter,
            date_debut,
            date_fin
        )
        
        if surveillances:
            df = pd.DataFrame(surveillances)
            
            # Formater les dates
            df['date_heure'] = pd.to_datetime(df['date_heure'])
            df['Date'] = df['date_heure'].dt.strftime('%d/%m/%Y')
            df['Jour'] = df['date_heure'].dt.day_name()
            df['Heure début'] = df['date_heure'].dt.strftime('%H:%M')
            
            df['heure_fin'] = pd.to_datetime(df['heure_fin'])
            df['Heure fin'] = df['heure_fin'].dt.strftime('%H:%M')
            
            # Créer tableau d'affichage
            df_display = df[[
                'Date', 'Jour', 'Heure début', 'Heure fin',
                'module', 'formation', 'departement',
                'salle', 'nb_etudiants'
            ]].copy()
            
            df_display.columns = [
                'Date', 'Jour', 'Début', 'Fin',
                'Module', 'Formation', 'Département',
                'Salle', 'Étudiants'
            ]
            
            # Afficher le tableau
            st.dataframe(
                df_display,
                use_container_width=True,
                hide_index=True
            )
            
            st.caption(f"📋 {len(df)} surveillance(s) affichée(s)")
            
            # Bouton d'export
            st.markdown("---")
            st.markdown("#### 💾 Exporter mon planning")
            
            col1, col2 = st.columns([1, 3])
            
            with col1:
                csv = df_display.to_csv(index=False).encode('utf-8')
                st.download_button(
                    label="📥 Télécharger CSV",
                    data=csv,
                    file_name=f"planning_{prof['nom']}_{prof['prenom']}.csv",
                    mime="text/csv"
                )
            
            with col2:
                st.info("💡 Vous pouvez importer ce fichier dans Google Calendar, Outlook, etc.")
        
        else:
            st.warning("⚠️ Aucune surveillance trouvée avec ces filtres")
    
    with tabs[1]:
        # ========== PAR DÉPARTEMENT ==========
        st.subheader("📊 Mes surveillances par département")
        
        if depts_prof:
            df_dept = pd.DataFrame(depts_prof)
            df_dept_display = df_dept[['departement', 'nb_surveillances', 'nb_jours']].copy()
            df_dept_display.columns = ['Département', 'Nb surveillances', 'Nb jours']
            
            # Tableau
            st.dataframe(df_dept_display, use_container_width=True, hide_index=True)
            
            # Graphique
            st.markdown("---")
            st.markdown("#### 📊 Visualisation")
            
            chart_data = df_dept_display.set_index('Département')['Nb surveillances']
            st.bar_chart(chart_data)
            
            # Résumé
            st.markdown("---")
            col1, col2, col3 = st.columns(3)
            
            with col1:
                st.metric("🏢 Départements", len(df_dept))
            
            with col2:
                dept_principal = df_dept.iloc[0]['departement']
                st.metric("📌 Principal", dept_principal)
            
            with col3:
                total = df_dept['nb_surveillances'].sum()
                st.metric("📝 Total", total)
        
        else:
            st.info("Aucune surveillance planifiée")
    
    with tabs[2]:
        # ========== STATISTIQUES ==========
        st.subheader("📈 Mes statistiques détaillées")
        
        if stats and stats['total_surveillances'] > 0:
            col1, col2 = st.columns(2)
            
            with col1:
                st.markdown("#### 📊 Ma charge de travail")
                st.metric("Total surveillances", stats['total_surveillances'])
                st.metric("Jours mobilisés", stats['nb_jours'])
                st.metric("Départements impliqués", stats['nb_departements'])
                
                if stats['nb_jours'] > 0:
                    avg = stats['total_surveillances'] / stats['nb_jours']
                    st.metric("Moyenne par jour", f"{avg:.2f}")
            
            with col2:
                st.markdown("#### 📅 Période")
                
                if stats['premiere_surveillance']:
                    st.metric(
                        "Première surveillance",
                        stats['premiere_surveillance'].strftime('%d/%m/%Y à %H:%M')
                    )
                
                if stats['derniere_surveillance']:
                    st.metric(
                        "Dernière surveillance",
                        stats['derniere_surveillance'].strftime('%d/%m/%Y à %H:%M')
                    )
                
                if stats['premiere_surveillance'] and stats['derniere_surveillance']:
                    duree = (stats['derniere_surveillance'] - stats['premiere_surveillance']).days
                    st.metric("Durée totale", f"{duree} jours")
            
            st.markdown("---")
            
            # Répartition par département
            st.markdown("#### 🏢 Ma répartition par département")
            
            if depts_prof:
                df_dept = pd.DataFrame(depts_prof)
                
                total = df_dept['nb_surveillances'].sum()
                df_dept['Pourcentage'] = (df_dept['nb_surveillances'] / total * 100).round(1)
                
                for _, row in df_dept.iterrows():
                    col_dept1, col_dept2, col_dept3 = st.columns([3, 1, 1])
                    
                    with col_dept1:
                        st.write(f"**{row['departement']}**")
                    
                    with col_dept2:
                        st.write(f"{row['nb_surveillances']} surveillances")
                    
                    with col_dept3:
                        st.write(f"**{row['Pourcentage']:.1f}%**")
                    
                    st.progress(row['Pourcentage'] / 100)
            
            st.markdown("---")
            
            # Comparaison avec la moyenne
            st.markdown("#### ⚖️ Comparaison avec mes collègues")
            
            query_avg = """
            SELECT AVG(surv_count) as moyenne
            FROM (
                SELECT p.id, COUNT(DISTINCT e.id) as surv_count
                FROM professeurs p
                LEFT JOIN examens e ON p.id = e.prof_id AND e.statut = 'planifie'
                WHERE p.dept_id = %s
                GROUP BY p.id
            ) as sub
            """
            
            avg_result = db.execute_query(query_avg, (prof['dept_id'],))
            
            if avg_result:
                moyenne = avg_result[0]['moyenne']
                
                col1, col2, col3 = st.columns(3)
                
                with col1:
                    st.metric("Mes surveillances", stats['total_surveillances'])
                
                with col2:
                    st.metric("Moyenne du département", f"{moyenne:.1f}")
                
                with col3:
                    diff = stats['total_surveillances'] - moyenne
                    st.metric("Différence", f"{diff:+.1f}")
                
                if diff > 5:
                    st.warning("📈 Vous êtes au-dessus de la moyenne départementale")
                elif diff < -5:
                    st.success("📉 Vous êtes en-dessous de la moyenne départementale")
                else:
                    st.info("✅ Vous êtes proche de la moyenne départementale")
        
        else:
            st.info("Pas encore de statistiques disponibles")

# ========== MAIN ==========

def main():
    """Point d'entrée principal"""
    if 'authenticated' not in st.session_state:
        st.session_state['authenticated'] = False
    
    if st.session_state['authenticated']:
        main_page()
    else:
        login_page()

if __name__ == "__main__":
    main()