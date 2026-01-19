"""
Page Vice-Doyen - Vue Stratégique Globale
🔥 AVEC AUTHENTIFICATION PAR EMAIL + MOT DE PASSE
✅ AVEC VALIDATION PAR DÉPARTEMENT ET PAR SEMESTRE
"""
import streamlit as st
import sys
from pathlib import Path
import pandas as pd
import hashlib

sys.path.insert(0, str(Path(__file__).parent.parent))

from backend.db_connection import db

st.set_page_config(
    page_title="Espace Vice-Doyen",
    page_icon="🎓",
    layout="wide"
)

# ========== FONCTIONS UTILITAIRES ==========

def hash_password(password):
    """Hasher un mot de passe avec SHA-256"""
    return hashlib.sha256(password.encode()).hexdigest()

# ========== AUTHENTIFICATION ==========

def authenticate_vice_doyen(email, password):
    """Authentifier un vice-doyen avec email + mot de passe"""
    query = """
    SELECT 
        p.id, p.nom, p.prenom, p.email, p.password,
        d.nom as departement, d.id as dept_id, d.code as dept_code,
        p.specialite, p.est_vice_doyen, p.date_nomination_vd
    FROM professeurs p
    LEFT JOIN departements d ON p.dept_id = d.id
    WHERE p.email = %s AND p.est_vice_doyen = TRUE
    """
    result = db.execute_query(query, (email,))
    
    if not result:
        return None
    
    vice_doyen = result[0]
    
    # Vérifier le mot de passe
    password_hash = hash_password(password)
    
    # Si le mot de passe en BDD est NULL ou vide, accepter n'importe quel mot de passe
    # et mettre à jour avec le nouveau
    if not vice_doyen.get('password') or vice_doyen.get('password') == 'NULL':
        # Première connexion - définir le mot de passe
        update_query = "UPDATE professeurs SET password = %s WHERE id = %s"
        db.execute_query(update_query, (password_hash, vice_doyen['id']))
        return vice_doyen
    
    # Sinon, vérifier que le hash correspond
    if vice_doyen['password'] == password_hash:
        return vice_doyen
    
    return None

def login_page():
    """Page de connexion Vice-Doyen avec email + mot de passe"""
    st.title("🎓 Espace Vice-Doyen")
    st.markdown("### Authentification sécurisée")
    st.markdown("---")
    
    col1, col2, col3 = st.columns([1, 2, 1])
    
    with col2:
        st.markdown("#### 🔐 Connexion Vice-Doyen")
        st.info("💡 Connectez-vous avec votre email professionnel et mot de passe")
        
        email = st.text_input(
            "Email professionnel",
            placeholder="prenom.nom@univ-prof.dz",
            key="vd_email"
        )
        
        password = st.text_input(
            "Mot de passe",
            type="password",
            placeholder="Entrez votre mot de passe",
            key="vd_password"
        )
        
        col_btn1, col_btn2 = st.columns(2)
        
        with col_btn1:
            if st.button("🔓 Se connecter", use_container_width=True, type="primary"):
                if not email or "@" not in email:
                    st.error("❌ Email invalide")
                elif not password:
                    st.error("❌ Mot de passe requis")
                else:
                    with st.spinner("🔍 Vérification..."):
                        vice_doyen = authenticate_vice_doyen(email, password)
                        if vice_doyen:
                            st.session_state['authenticated_vice_doyen'] = True
                            st.session_state['vice_doyen'] = vice_doyen
                            st.success(f"✅ Bienvenue Vice-Doyen {vice_doyen['prenom']} {vice_doyen['nom']}")
                            st.rerun()
                        else:
                            st.error("❌ Email ou mot de passe incorrect")
        
        with col_btn2:
            if st.button("🔄 Réinitialiser", use_container_width=True):
                st.info("""
                📧 Pour réinitialiser votre mot de passe:
                - Contactez l'administrateur système
                - Email: admin@univ.dz
                """)

# ========== FONCTIONS DE DONNÉES ==========

def get_kpis_globaux():
    """KPIs académiques globaux"""
    query = """
    SELECT 
        (SELECT COUNT(*) FROM departements) as nb_departements,
        (SELECT COUNT(*) FROM formations) as nb_formations,
        (SELECT COUNT(*) FROM modules) as nb_modules,
        (SELECT COUNT(*) FROM etudiants) as nb_etudiants,
        (SELECT COUNT(*) FROM professeurs) as nb_professeurs,
        (SELECT COUNT(*) FROM salles) as nb_salles,
        (SELECT SUM(capacite) FROM salles) as capacite_totale,
        (SELECT COUNT(*) FROM examens WHERE statut = 'planifie') as examens_planifies
    """
    result = db.execute_query(query)
    return result[0] if result else None

def get_taux_occupation_global():
    """Taux d'occupation des amphis et salles"""
    query = """
    SELECT 
        type,
        COUNT(*) as total,
        SUM(capacite) as capacite_totale,
        COUNT(DISTINCT CASE WHEN id IN (
            SELECT DISTINCT salle_id FROM examens WHERE statut IN ('planifie', 'valide')
        ) THEN id END) as utilisees,
        ROUND(
            COUNT(DISTINCT CASE WHEN id IN (
                SELECT DISTINCT salle_id FROM examens WHERE statut IN ('planifie', 'valide')
            ) THEN id END) * 100.0 / COUNT(*), 
            1
        ) as taux_utilisation
    FROM salles
    GROUP BY type
    """
    return db.execute_query(query)

def get_heures_profs():
    """Heures de surveillance par professeur"""
    query = """
    SELECT 
        CONCAT(p.prenom, ' ', p.nom) as professeur,
        d.code as departement,
        COUNT(DISTINCT e.id) as nb_surveillances,
        SUM(e.duree_minutes) / 60.0 as heures_totales
    FROM professeurs p
    LEFT JOIN examens e ON p.id = e.prof_id AND e.statut IN ('planifie', 'valide')
    LEFT JOIN departements d ON p.dept_id = d.id
    GROUP BY p.id, p.prenom, p.nom, d.code
    HAVING COUNT(DISTINCT e.id) > 0
    ORDER BY heures_totales DESC
    LIMIT 20
    """
    return db.execute_query(query)

def get_conflits_par_departement():
    """Taux de conflits par département"""
    conflits_data = []
    
    query_depts = "SELECT id, nom, code FROM departements"
    departements = db.execute_query(query_depts)
    
    for dept in departements:
        dept_id = dept['id']
        
        # Conflits étudiants
        query_etu = """
        SELECT COUNT(*) as nb
        FROM (
            SELECT DATE(ex.date_heure) as jour, et.id
            FROM etudiants et
            JOIN formations f ON et.formation_id = f.id
            JOIN groupes g ON et.groupe_id = g.id
            JOIN inscriptions i ON et.id = i.etudiant_id
            JOIN modules m ON i.module_id = m.id
            JOIN examens ex ON m.id = ex.module_id 
                AND ex.groupe_id = et.groupe_id
            WHERE f.dept_id = %s AND ex.statut IN ('planifie', 'valide')
            GROUP BY DATE(ex.date_heure), et.id
            HAVING COUNT(DISTINCT ex.id) > 1
        ) as conflicts
        """
        result_etu = db.execute_query(query_etu, (dept_id,))
        nb_conflits_etu = result_etu[0]['nb'] if result_etu else 0
        
        # Conflits profs
        query_prof = """
        SELECT COUNT(*) as nb
        FROM (
            SELECT DATE(e.date_heure) as jour, p.id
            FROM examens e
            JOIN professeurs p ON e.prof_id = p.id
            WHERE p.dept_id = %s AND e.statut IN ('planifie', 'valide')
            GROUP BY DATE(e.date_heure), p.id
            HAVING COUNT(DISTINCT e.id) > 3
        ) as conflicts
        """
        result_prof = db.execute_query(query_prof, (dept_id,))
        nb_conflits_prof = result_prof[0]['nb'] if result_prof else 0
        
        # Total examens
        query_total = """
        SELECT COUNT(*) as total
        FROM examens e
        JOIN modules m ON e.module_id = m.id
        JOIN formations f ON m.formation_id = f.id
        WHERE f.dept_id = %s AND e.statut IN ('planifie', 'valide')
        """
        result_total = db.execute_query(query_total, (dept_id,))
        total_examens = result_total[0]['total'] if result_total else 0
        
        total_conflits = nb_conflits_etu + nb_conflits_prof
        taux = (total_conflits / total_examens * 100) if total_examens > 0 else 0
        
        conflits_data.append({
            'departement': dept['nom'],
            'code': dept['code'],
            'conflits': total_conflits,
            'examens': total_examens,
            'taux': round(taux, 1)
        })
    
    return conflits_data

def get_validation_status():
    """
    🔥 CORRIGÉ: Statut de validation par département ET par semestre
    """
    query = """
    SELECT 
        d.nom as departement,
        d.code,
        COALESCE(e.semestre, 0) as semestre,
        COUNT(CASE WHEN e.statut = 'planifie' THEN 1 END) as planifies,
        COUNT(CASE WHEN e.statut = 'valide' THEN 1 END) as valides,
        COUNT(e.id) as total
    FROM departements d
    JOIN formations f ON d.id = f.dept_id
    JOIN modules m ON f.id = m.formation_id
    JOIN examens e ON m.id = e.module_id
    WHERE e.statut IN ('planifie', 'valide')
    GROUP BY d.id, d.nom, d.code, e.semestre
    HAVING total > 0
    ORDER BY d.nom, e.semestre
    """
    return db.execute_query(query)

def get_validation_summary():
    """
    🔥 NOUVEAU: Résumé de validation par département (tous semestres confondus)
    """
    query = """
    SELECT 
        d.nom as departement,
        d.code,
        COUNT(CASE WHEN e.statut = 'planifie' THEN 1 END) as planifies,
        COUNT(CASE WHEN e.statut = 'valide' THEN 1 END) as valides,
        COUNT(e.id) as total,
        ROUND(
            COUNT(CASE WHEN e.statut = 'valide' THEN 1 END) * 100.0 / COUNT(e.id),
            1
        ) as taux_validation
    FROM departements d
    JOIN formations f ON d.id = f.dept_id
    JOIN modules m ON f.id = m.formation_id
    JOIN examens e ON m.id = e.module_id
    WHERE e.statut IN ('planifie', 'valide')
    GROUP BY d.id, d.nom, d.code
    HAVING total > 0
    ORDER BY taux_validation ASC, d.nom
    """
    return db.execute_query(query)

# ========== GESTION PROFIL ==========

def afficher_profil(vice_doyen):
    """Afficher et gérer le profil du vice-doyen"""
    st.subheader("👤 Mon Profil")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("### Informations personnelles")
        dept_info = f" - {vice_doyen['departement']} ({vice_doyen['dept_code']})" if vice_doyen.get('departement') else ""
        st.info(f"""
        **Nom:** {vice_doyen['nom']}  
        **Prénom:** {vice_doyen['prenom']}  
        **Email:** {vice_doyen['email']}  
        **Fonction:** Vice-Doyen{dept_info}  
        **Spécialité:** {vice_doyen.get('specialite', 'N/A')}  
        **Nommé le:** {vice_doyen.get('date_nomination_vd', 'N/A')}
        """)
    
    with col2:
        st.markdown("### Changer le mot de passe")
        
        with st.form("change_password_form_vd"):
            current_password = st.text_input("Mot de passe actuel", type="password")
            new_password = st.text_input("Nouveau mot de passe", type="password")
            confirm_password = st.text_input("Confirmer le nouveau mot de passe", type="password")
            
            if st.form_submit_button("🔒 Modifier le mot de passe", type="primary"):
                if not current_password or not new_password or not confirm_password:
                    st.error("❌ Tous les champs sont requis")
                elif new_password != confirm_password:
                    st.error("❌ Les nouveaux mots de passe ne correspondent pas")
                elif len(new_password) < 6:
                    st.error("❌ Le mot de passe doit contenir au moins 6 caractères")
                else:
                    verify_vd = authenticate_vice_doyen(vice_doyen['email'], current_password)
                    if not verify_vd:
                        st.error("❌ Mot de passe actuel incorrect")
                    else:
                        new_hash = hash_password(new_password)
                        update_query = "UPDATE professeurs SET password = %s WHERE id = %s"
                        db.execute_query(update_query, (new_hash, vice_doyen['id']))
                        st.success("✅ Mot de passe modifié avec succès!")
                        st.info("🔐 Veuillez vous reconnecter avec votre nouveau mot de passe")

# ========== INTERFACE PRINCIPALE ==========

def main_page():
    """Page principale après authentification"""
    vice_doyen = st.session_state['vice_doyen']
    
    # Header avec infos Vice-Doyen
    col1, col2 = st.columns([4, 1])
    with col1:
        st.title("🎓 Espace Vice-Doyen - Vue Stratégique Globale")
        st.markdown(f"**Vice-Doyen:** {vice_doyen['prenom']} {vice_doyen['nom']} | **Email:** {vice_doyen['email']}")
        if vice_doyen.get('date_nomination_vd'):
            st.caption(f"Nommé le: {vice_doyen['date_nomination_vd']}")
    with col2:
        st.markdown("##")
        if st.button("🚪 Déconnexion", type="secondary"):
            st.session_state.clear()
            st.rerun()
    
    st.markdown("Pilotage et validation de la planification des examens")
    st.markdown("---")
    
    # Onglets
    tabs = st.tabs([
        "📊 Tableau de Bord",
        "🏫 Occupation",
        "⚠️ Conflits",
        "👨‍🏫 Professeurs",
        "✅ Validation",
        "👤 Profil"
    ])
    
    with tabs[0]:
        # ========== KPIs GLOBAUX ==========
        st.subheader("📊 Indicateurs Clés de Performance")
        
        kpis = get_kpis_globaux()
        
        if kpis:
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                st.metric("🏢 Départements", kpis['nb_departements'])
                st.metric("👨‍🎓 Étudiants", f"{kpis['nb_etudiants']:,}")
            
            with col2:
                st.metric("🎓 Formations", kpis['nb_formations'])
                st.metric("📚 Modules", kpis['nb_modules'])
            
            with col3:
                st.metric("👨‍🏫 Professeurs", kpis['nb_professeurs'])
                st.metric("🏫 Salles totales", kpis['nb_salles'])
            
            with col4:
                st.metric("📝 Examens planifiés", kpis['examens_planifies'])
                taux_planif = (kpis['examens_planifies'] / kpis['nb_modules'] * 100) if kpis['nb_modules'] > 0 else 0
                st.metric("✅ Taux planification", f"{taux_planif:.1f}%")
        
        st.markdown("---")
        
        # Résumé Exécutif
        st.subheader("📈 Résumé Exécutif")
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.markdown("**🎯 Planification**")
            if kpis:
                taux = (kpis['examens_planifies'] / kpis['nb_modules'] * 100) if kpis['nb_modules'] > 0 else 0
                if taux >= 90:
                    st.success(f"✅ {taux:.0f}% planifié")
                elif taux >= 70:
                    st.warning(f"⚠️ {taux:.0f}% planifié")
                else:
                    st.error(f"❌ {taux:.0f}% planifié")
        
        with col2:
            st.markdown("**⚠️ Conflits**")
            conflits_dept = get_conflits_par_departement()
            if conflits_dept:
                total_conflits = sum(c['conflits'] for c in conflits_dept)
                if total_conflits == 0:
                    st.success("✅ Aucun conflit")
                elif total_conflits < 10:
                    st.warning(f"⚠️ {total_conflits} conflits mineurs")
                else:
                    st.error(f"❌ {total_conflits} conflits à résoudre")
        
        with col3:
            st.markdown("**🏫 Ressources**")
            occupation = get_taux_occupation_global()
            if occupation:
                df_occ = pd.DataFrame(occupation)
                taux_occ = (df_occ['utilisees'].sum() / df_occ['total'].sum() * 100)
                if 60 <= taux_occ <= 85:
                    st.success(f"✅ {taux_occ:.0f}% optimisé")
                elif taux_occ < 60:
                    st.info(f"ℹ️ {taux_occ:.0f}% sous-utilisé")
                else:
                    st.warning(f"⚠️ {taux_occ:.0f}% saturé")
    
    with tabs[1]:
        # ========== OCCUPATION GLOBALE ==========
        st.subheader("🏫 Occupation Globale des Amphis et Salles")
        
        occupation = get_taux_occupation_global()
        
        if occupation:
            df_occ = pd.DataFrame(occupation)
            
            col1, col2 = st.columns([1, 2])
            
            with col1:
                st.dataframe(
                    df_occ[['type', 'total', 'utilisees', 'taux_utilisation']].rename(columns={
                        'type': 'Type',
                        'total': 'Total',
                        'utilisees': 'Utilisées',
                        'taux_utilisation': 'Taux (%)'
                    }),
                    use_container_width=True,
                    hide_index=True
                )
                
                total_salles = df_occ['total'].sum()
                total_utilisees = df_occ['utilisees'].sum()
                taux_global = (total_utilisees / total_salles * 100) if total_salles > 0 else 0
                
                st.metric("📊 Taux global d'utilisation", f"{taux_global:.1f}%")
                
                if taux_global < 60:
                    st.info("💡 Optimisation possible - Certaines salles sont sous-utilisées")
                elif taux_global > 85:
                    st.warning("⚠️ Saturation élevée - Risque de contraintes")
            
            with col2:
                chart_data = df_occ.set_index('type')[['utilisees', 'total']]
                st.bar_chart(chart_data)
    
    with tabs[2]:
        # ========== CONFLITS PAR DÉPARTEMENT ==========
        st.subheader("⚠️ Taux de Conflits par Département")
        
        conflits_dept = get_conflits_par_departement()
        
        if conflits_dept:
            df_conflits = pd.DataFrame(conflits_dept)
            
            col1, col2 = st.columns([1, 1])
            
            with col1:
                st.dataframe(
                    df_conflits[['departement', 'conflits', 'examens', 'taux']].rename(columns={
                        'departement': 'Département',
                        'conflits': 'Conflits',
                        'examens': 'Examens',
                        'taux': 'Taux (%)'
                    }),
                    use_container_width=True,
                    hide_index=True
                )
                
                dept_problemes = df_conflits[df_conflits['taux'] > 5]
                if not dept_problemes.empty:
                    st.error(f"🔴 {len(dept_problemes)} département(s) avec taux > 5%")
            
            with col2:
                chart_data = df_conflits.set_index('code')['taux']
                st.bar_chart(chart_data)
        else:
            st.success("✅ Aucun conflit détecté dans toute l'université")
    
    with tabs[3]:
        # ========== HEURES PROFESSEURS ==========
        st.subheader("👨‍🏫 Heures de Surveillance des Professeurs")
        
        heures_profs = get_heures_profs()
        
        if heures_profs:
            df_heures = pd.DataFrame(heures_profs)
            
            col1, col2 = st.columns([1, 1])
            
            with col1:
                st.dataframe(
                    df_heures[['professeur', 'departement', 'nb_surveillances', 'heures_totales']].rename(columns={
                        'professeur': 'Professeur',
                        'departement': 'Dept',
                        'nb_surveillances': 'Surveillances',
                        'heures_totales': 'Heures'
                    }),
                    use_container_width=True,
                    hide_index=True
                )
                
                avg_heures = df_heures['heures_totales'].mean()
                max_heures = df_heures['heures_totales'].max()
                
                st.metric("📊 Moyenne heures/prof", f"{avg_heures:.1f}h")
                st.metric("📈 Maximum", f"{max_heures:.1f}h")
            
            with col2:
                df_top10 = df_heures.head(10)
                chart_data = df_top10.set_index('professeur')['heures_totales'].sort_values()
                st.bar_chart(chart_data)
    
    with tabs[4]:
        # ========== VALIDATION FINALE ==========
        st.subheader("✅ Validation Finale du Planning")
        
        st.info("""
        📋 **Information**: La validation se fait par département et par semestre.
        Chaque Chef de Département doit valider ses semestres 1 et 2 séparément.
        """)
        
        # 🔥 Résumé par département (tous semestres)
        st.markdown("### 📊 Résumé par Département")
        
        validation_summary = get_validation_summary()
        
        if validation_summary:
            df_summary = pd.DataFrame(validation_summary)
            
            col1, col2 = st.columns([2, 1])
            
            with col1:
                # Colorer les lignes selon le taux de validation
                def color_validation(row):
                    if row['taux_validation'] == 100:
                        return ['background-color: #d4edda'] * len(row)
                    elif row['taux_validation'] >= 50:
                        return ['background-color: #fff3cd'] * len(row)
                    else:
                        return ['background-color: #f8d7da'] * len(row)
                
                st.dataframe(
                    df_summary[['departement', 'planifies', 'valides', 'total', 'taux_validation']].rename(columns={
                        'departement': 'Département',
                        'planifies': 'Planifiés',
                        'valides': 'Validés',
                        'total': 'Total',
                        'taux_validation': 'Validation (%)'
                    }),
                    use_container_width=True,
                    hide_index=True
                )
            
            with col2:
                total_planifies = df_summary['planifies'].sum()
                total_valides = df_summary['valides'].sum()
                total_examens = df_summary['total'].sum()
                taux_global = (total_valides / total_examens * 100) if total_examens > 0 else 0
                
                st.metric("📝 Total examens", total_examens)
                st.metric("✅ Total validés", total_valides)
                st.metric("⏳ Non validés", total_planifies)
                st.metric("📊 Taux global", f"{taux_global:.1f}%")
        
        st.markdown("---")
        
        # 🔥 Détail par département ET par semestre
        st.markdown("### 📅 Détail par Département et Semestre")
        
        validation_status = get_validation_status()
        
        if validation_status:
            df_val = pd.DataFrame(validation_status)
            df_val['semestre'] = df_val['semestre'].apply(lambda x: f'S{x}' if x else 'N/A')
            df_val['taux_validation'] = (df_val['valides'] / df_val['total'] * 100).round(1)
            
            # Tableau détaillé
            st.dataframe(
                df_val[['departement', 'semestre', 'planifies', 'valides', 'total', 'taux_validation']].rename(columns={
                    'departement': 'Département',
                    'semestre': 'Semestre',
                    'planifies': 'Planifiés',
                    'valides': 'Validés',
                    'total': 'Total',
                    'taux_validation': 'Validation (%)'
                }),
                use_container_width=True,
                hide_index=True
            )
            
            # Analyse
            depts_non_valides = df_val[df_val['taux_validation'] < 100]
            
            if not depts_non_valides.empty:
                with st.expander("📋 Voir les détails des semestres"):
                    for _, row in depts_non_valides.iterrows():
                        st.text(f"• {row['departement']} - {row['semestre']}: {row['taux_validation']:.0f}% validé")
            else:
                st.success("🎉 Tous les semestres de tous les départements sont validés!")
                st.balloons()
                
                if st.button("🏆 APPROUVER LE PLANNING GLOBAL", type="primary", use_container_width=True):
                    # Mettre à jour tous les examens validés en "approuvé"
                    query = "UPDATE examens SET statut = 'approuve' WHERE statut = 'valide'"
                    db.execute_query(query)
                    st.success("✅ Planning global approuvé avec succès!")
                    st.balloons()
        else:
            st.info("ℹ️ Aucun examen planifié pour le moment")
    
    with tabs[5]:
        afficher_profil(vice_doyen)

# ========== MAIN ==========

def main():
    if 'authenticated_vice_doyen' not in st.session_state:
        st.session_state['authenticated_vice_doyen'] = False
    
    if st.session_state['authenticated_vice_doyen']:
        main_page()
    else:
        login_page()

if __name__ == "__main__":
    main()