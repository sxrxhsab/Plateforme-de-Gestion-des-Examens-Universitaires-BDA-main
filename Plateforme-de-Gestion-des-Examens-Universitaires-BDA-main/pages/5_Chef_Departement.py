"""
Page Chef de Département - Gestion et Validation des Examens
🔥 AVEC AUTHENTIFICATION PAR EMAIL + MOT DE PASSE
✅ AVEC STATISTIQUES PAR FORMATION ET SPÉCIALITÉ
✅ SYSTÈME DE VALIDATION DÉFINITIVE AVEC SUIVI
"""
import streamlit as st
import sys
from pathlib import Path
import pandas as pd
from datetime import datetime
import hashlib

sys.path.insert(0, str(Path(__file__).parent.parent))

from backend.db_connection import db

st.set_page_config(
    page_title="Espace Chef de Département",
    page_icon="👔",
    layout="wide"
)

# ========== FONCTIONS UTILITAIRES ==========

def hash_password(password):
    """Hasher un mot de passe avec SHA-256"""
    return hashlib.sha256(password.encode()).hexdigest()

# ========== AUTHENTIFICATION ==========

def authenticate_chef(email, password):
    """Authentifier un chef de département avec email + mot de passe"""
    query = """
    SELECT 
        p.id, p.nom, p.prenom, p.email, p.password,
        d.nom as departement, d.id as dept_id, d.code as dept_code,
        p.specialite, p.est_chef_dept, p.date_nomination
    FROM professeurs p
    JOIN departements d ON p.dept_id = d.id
    WHERE p.email = %s AND p.est_chef_dept = TRUE
    """
    result = db.execute_query(query, (email,))
    
    if not result:
        return None
    
    chef = result[0]
    password_hash = hash_password(password)
    
    if not chef.get('password') or chef.get('password') == 'NULL':
        update_query = "UPDATE professeurs SET password = %s WHERE id = %s"
        db.execute_query(update_query, (password_hash, chef['id']))
        return chef
    
    if chef['password'] == password_hash:
        return chef
    
    return None

def login_page():
    """Page de connexion avec email + mot de passe"""
    st.title("👔 Espace Chef de Département")
    st.markdown("### Authentification sécurisée")
    st.markdown("---")
    
    col1, col2, col3 = st.columns([1, 2, 1])
    
    with col2:
        st.markdown("#### 🔐 Connexion")
        
        email = st.text_input("Email professionnel", placeholder="prenom.nom@univ-prof.dz")
        password = st.text_input("Mot de passe", type="password", placeholder="Entrez votre mot de passe")
        
        col_btn1, col_btn2 = st.columns(2)
        
        with col_btn1:
            if st.button("🔓 Se connecter", use_container_width=True, type="primary"):
                if not email or "@" not in email:
                    st.error("❌ Email invalide")
                elif not password:
                    st.error("❌ Mot de passe requis")
                else:
                    with st.spinner("🔍 Vérification..."):
                        chef = authenticate_chef(email, password)
                        if chef:
                            st.session_state['authenticated_chef'] = True
                            st.session_state['chef'] = chef
                            st.success(f"✅ Bienvenue Chef {chef['prenom']} {chef['nom']}")
                            st.rerun()
                        else:
                            st.error("❌ Email ou mot de passe incorrect")
        
        with col_btn2:
            if st.button("🔄 Réinitialiser", use_container_width=True):
                st.info("📧 Pour réinitialiser votre mot de passe, contactez l'administrateur système")

# ========== STATISTIQUES ==========

def get_stats_departement(dept_id):
    """Récupérer les statistiques du département"""
    stats = {}
    
    query = "SELECT COUNT(*) as total FROM formations WHERE dept_id = %s"
    result = db.execute_query(query, (dept_id,))
    stats['formations'] = result[0]['total'] if result else 0
    
    query = """
    SELECT COUNT(DISTINCT e.id) as total
    FROM etudiants e
    JOIN formations f ON e.formation_id = f.id
    WHERE f.dept_id = %s
    """
    result = db.execute_query(query, (dept_id,))
    stats['etudiants'] = result[0]['total'] if result else 0
    
    query = "SELECT COUNT(*) as total FROM professeurs WHERE dept_id = %s"
    result = db.execute_query(query, (dept_id,))
    stats['professeurs'] = result[0]['total'] if result else 0
    
    query = """
    SELECT 
        SUM(CASE WHEN e.statut = 'planifie' THEN 1 ELSE 0 END) as planifies,
        SUM(CASE WHEN e.statut = 'valide' THEN 1 ELSE 0 END) as valides,
        COUNT(*) as total
    FROM examens e
    JOIN modules m ON e.module_id = m.id
    JOIN formations f ON m.formation_id = f.id
    WHERE f.dept_id = %s
    """
    result = db.execute_query(query, (dept_id,))
    if result and result[0]:
        stats['examens_planifies'] = result[0]['planifies'] or 0
        stats['examens_valides'] = result[0]['valides'] or 0
        stats['examens_total'] = result[0]['total'] or 0
    else:
        stats['examens_planifies'] = 0
        stats['examens_valides'] = 0
        stats['examens_total'] = 0
    
    return stats

def get_stats_par_specialite_etudiants(dept_id):
    """Récupérer les statistiques par spécialité des étudiants"""
    query = """
    SELECT 
        COALESCE(f.specialite, 'Tronc commun') as specialite,
        COUNT(DISTINCT e.id) as nb_etudiants,
        COUNT(DISTINCT f.id) as nb_formations,
        COUNT(DISTINCT ex.id) as nb_examens
    FROM formations f
    LEFT JOIN etudiants e ON f.id = e.formation_id
    LEFT JOIN modules m ON f.id = m.formation_id
    LEFT JOIN examens ex ON m.id = ex.module_id
    WHERE f.dept_id = %s
    GROUP BY COALESCE(f.specialite, 'Tronc commun')
    ORDER BY nb_etudiants DESC
    """
    return db.execute_query(query, (dept_id,))

def get_stats_par_specialite_profs(dept_id):
    """Récupérer les statistiques par spécialité des professeurs"""
    query = """
    SELECT 
        COALESCE(p.specialite, 'Non spécifié') as specialite,
        COUNT(DISTINCT p.id) as nb_professeurs,
        COUNT(DISTINCT sv.examen_id) as nb_surveillances
    FROM professeurs p
    LEFT JOIN surveillances sv ON p.id = sv.prof_id
    LEFT JOIN examens e ON sv.examen_id = e.id
    LEFT JOIN modules m ON e.module_id = m.id
    LEFT JOIN formations f ON m.formation_id = f.id
    WHERE p.dept_id = %s AND (f.dept_id = %s OR f.dept_id IS NULL)
    GROUP BY COALESCE(p.specialite, 'Non spécifié')
    ORDER BY nb_professeurs DESC
    """
    return db.execute_query(query, (dept_id, dept_id))

def afficher_statistiques(dept_id):
    """Afficher les statistiques du département"""
    st.subheader("📊 Statistiques Globales du Département")
    
    stats = get_stats_departement(dept_id)
    
    col1, col2, col3, col4, col5 = st.columns(5)
    
    with col1:
        st.metric("🎓 Formations", stats['formations'])
    with col2:
        st.metric("👨‍🎓 Étudiants", f"{stats['etudiants']:,}")
    with col3:
        st.metric("👨‍🏫 Professeurs", stats['professeurs'])
    with col4:
        taux_planif = (stats['examens_planifies'] / stats['examens_total'] * 100) if stats['examens_total'] > 0 else 0
        st.metric("📝 Planifiés", f"{stats['examens_planifies']}/{stats['examens_total']}", f"{taux_planif:.0f}%")
    with col5:
        taux_valid = (stats['examens_valides'] / stats['examens_total'] * 100) if stats['examens_total'] > 0 else 0
        st.metric("✅ Validés", f"{stats['examens_valides']}/{stats['examens_total']}", f"{taux_valid:.0f}%")
    
    st.markdown("---")
    
    st.subheader("🎓 Statistiques par Spécialité des Étudiants")
    stats_specialites_etudiants = get_stats_par_specialite_etudiants(dept_id)
    
    if stats_specialites_etudiants:
        df_spec_etudiants = pd.DataFrame(stats_specialites_etudiants)
        df_spec_etudiants.columns = ['Spécialité', 'Étudiants', 'Formations', 'Examens']
        st.dataframe(df_spec_etudiants, use_container_width=True, hide_index=True)
        
        col1, col2 = st.columns(2)
        with col1:
            st.markdown("**👨‍🎓 Étudiants par spécialité**")
            st.bar_chart(df_spec_etudiants.set_index('Spécialité')['Étudiants'])
        with col2:
            st.markdown("**📝 Examens par spécialité**")
            st.bar_chart(df_spec_etudiants.set_index('Spécialité')['Examens'])
    else:
        st.info("Aucune donnée disponible")
    
    st.markdown("---")
    st.subheader("🔬 Statistiques par Spécialité des Professeurs")
    stats_specialites_profs = get_stats_par_specialite_profs(dept_id)
    
    if stats_specialites_profs:
        df_specialites = pd.DataFrame(stats_specialites_profs)
        df_specialites.columns = ['Spécialité', 'Professeurs', 'Surveillances']
        st.dataframe(df_specialites, use_container_width=True, hide_index=True)
        
        col1, col2 = st.columns(2)
        with col1:
            st.markdown("**👨‍🏫 Professeurs par spécialité**")
            st.bar_chart(df_specialites.set_index('Spécialité')['Professeurs'])
        with col2:
            st.markdown("**👁️ Surveillances par spécialité**")
            st.bar_chart(df_specialites.set_index('Spécialité')['Surveillances'])
    else:
        st.info("Aucune donnée disponible")

# ========== CONFLITS ==========

def detecter_conflits(dept_id):
    """Détecter les conflits du planning"""
    conflits = []
    
    query = """
    SELECT 
        DATE(ex.date_heure) as jour, e.matricule,
        CONCAT(e.prenom, ' ', e.nom) as etudiant,
        f.nom as formation, g.nom as groupe,
        COUNT(DISTINCT ex.id) as nb_examens,
        GROUP_CONCAT(DISTINCT CONCAT(TIME(ex.date_heure), ' - ', m.nom) ORDER BY ex.date_heure SEPARATOR ' | ') as detail_examens
    FROM etudiants e
    JOIN formations f ON e.formation_id = f.id
    JOIN groupes g ON e.groupe_id = g.id
    JOIN inscriptions i ON e.id = i.etudiant_id
    JOIN modules m ON i.module_id = m.id
    JOIN examens ex ON m.id = ex.module_id AND ex.groupe_id = e.groupe_id
    WHERE f.dept_id = %s AND ex.statut = 'planifie'
    GROUP BY DATE(ex.date_heure), e.id, e.matricule, e.prenom, e.nom, f.nom, g.nom
    HAVING COUNT(DISTINCT ex.id) > 1
    ORDER BY jour, nb_examens DESC
    """
    result = db.execute_query(query, (dept_id,))
    if result:
        for r in result:
            conflits.append({
                'type': 'Étudiant',
                'detail': f"{r['etudiant']} ({r['matricule']}) - {r['groupe']} a {r['nb_examens']} examens le {r['jour']}",
                'detail_complet': r['detail_examens'],
                'gravite': 'Critique'
            })
    
    query = """
    SELECT 
        DATE(e.date_heure) as jour,
        CONCAT(p.prenom, ' ', p.nom) as professeur,
        COUNT(DISTINCT sv.examen_id) as nb_surveillances,
        GROUP_CONCAT(DISTINCT CONCAT(TIME(e.date_heure), ' - ', m.nom) ORDER BY e.date_heure SEPARATOR ' | ') as detail_surveillances
    FROM surveillances sv
    JOIN professeurs p ON sv.prof_id = p.id
    JOIN examens e ON sv.examen_id = e.id
    JOIN modules m ON e.module_id = m.id
    JOIN formations f ON m.formation_id = f.id
    WHERE p.dept_id = %s AND e.statut = 'planifie'
    GROUP BY DATE(e.date_heure), p.id, p.prenom, p.nom
    HAVING COUNT(DISTINCT sv.examen_id) > 3
    ORDER BY jour, nb_surveillances DESC
    """
    result = db.execute_query(query, (dept_id,))
    if result:
        for r in result:
            conflits.append({
                'type': 'Professeur',
                'detail': f"{r['professeur']} a {r['nb_surveillances']} surveillances le {r['jour']}",
                'detail_complet': r['detail_surveillances'],
                'gravite': 'Moyen'
            })
    
    query = """
    SELECT e.date_heure, s.nom as salle, s.capacite, e.nb_etudiants, m.nom as module, g.nom as groupe
    FROM examens e
    JOIN salles s ON e.salle_id = s.id
    JOIN modules m ON e.module_id = m.id
    JOIN formations f ON m.formation_id = f.id
    LEFT JOIN groupes g ON e.groupe_id = g.id
    WHERE f.dept_id = %s AND e.nb_etudiants > s.capacite AND e.statut = 'planifie'
    ORDER BY (e.nb_etudiants - s.capacite) DESC
    """
    result = db.execute_query(query, (dept_id,))
    if result:
        for r in result:
            depassement = r['nb_etudiants'] - r['capacite']
            groupe_info = f" - {r['groupe']}" if r.get('groupe') else ""
            conflits.append({
                'type': 'Salle',
                'detail': f"{r['salle']} (cap. {r['capacite']}) avec {r['nb_etudiants']} étudiants ({depassement} en trop) - {r['module']}{groupe_info}",
                'detail_complet': f"Date: {r['date_heure']}",
                'gravite': 'Critique'
            })
    
    return conflits

def afficher_conflits(dept_id):
    """Afficher les conflits détectés"""
    st.subheader("⚠️ Détection des Conflits")
    
    st.info("""
    📌 **Contraintes du projet**:
    - ✅ Chaque étudiant doit avoir **1 SEUL examen par jour**
    - ✅ Chaque professeur peut surveiller **maximum 3 examens par jour**
    - ✅ Les salles ne doivent **jamais dépasser leur capacité**
    """)
    
    conflits = detecter_conflits(dept_id)
    
    if not conflits:
        st.success("✅ Aucun conflit détecté dans le planning")
        st.balloons()
    else:
        st.error(f"❌ {len(conflits)} conflit(s) détecté(s)")
        
        conflits_etudiants = [c for c in conflits if c['type'] == 'Étudiant']
        conflits_profs = [c for c in conflits if c['type'] == 'Professeur']
        conflits_salles = [c for c in conflits if c['type'] == 'Salle']
        
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("👨‍🎓 Étudiants", len(conflits_etudiants))
        with col2:
            st.metric("👨‍🏫 Professeurs", len(conflits_profs))
        with col3:
            st.metric("🏫 Salles", len(conflits_salles))
        
        st.markdown("---")
        
        df_conflits = pd.DataFrame([
            {
                'Type': c['type'],
                'Gravité': c['gravite'],
                'Détail': c['detail'],
                'Info complémentaire': c.get('detail_complet', '')
            }
            for c in conflits
        ])
        
        st.dataframe(df_conflits, use_container_width=True, hide_index=True)

# ========== EXAMENS ==========

def afficher_examens_par_formation(dept_id):
    """Afficher les examens par formation"""
    st.subheader("📚 Examens par Formation")
    
    query = """
    SELECT 
        f.nom as formation, f.niveau, m.nom as module, m.semestre,
        COALESCE(g.nom, 'Tous groupes') as groupe, e.date_heure,
        s.nom as salle, e.nb_etudiants, e.statut, e.id as examen_id
    FROM examens e
    JOIN modules m ON e.module_id = m.id
    JOIN formations f ON m.formation_id = f.id
    JOIN salles s ON e.salle_id = s.id
    LEFT JOIN groupes g ON e.groupe_id = g.id
    WHERE f.dept_id = %s
    ORDER BY f.nom, m.semestre, e.date_heure
    """
    result = db.execute_query(query, (dept_id,))
    
    if not result:
        st.warning("⚠️ Aucun examen trouvé pour ce département")
        return
    
    df = pd.DataFrame(result)
    
    examen_ids = [r['examen_id'] for r in result]
    if examen_ids:
        placeholders = ','.join(['%s'] * len(examen_ids))
        query_profs = f"""
        SELECT e.id as examen_id,
            GROUP_CONCAT(CONCAT(p.prenom, ' ', p.nom) SEPARATOR ', ') as professeurs
        FROM examens e
        JOIN surveillances sv ON e.id = sv.examen_id
        JOIN professeurs p ON sv.prof_id = p.id
        WHERE e.id IN ({placeholders})
        GROUP BY e.id
        """
        profs_result = db.execute_query(query_profs, tuple(examen_ids))
        
        if profs_result:
            profs_dict = {r['examen_id']: r['professeurs'] for r in profs_result}
            df['Professeurs'] = df['examen_id'].map(profs_dict).fillna('Non assigné')
    
    col_f1, col_f2, col_f3 = st.columns(3)
    
    with col_f1:
        formations = sorted(df['formation'].unique())
        formation_selectionnee = st.selectbox("🎓 Formation", ["Toutes"] + formations)
    
    with col_f2:
        semestres = sorted(df['semestre'].unique())
        semestre_selectionne = st.selectbox("📅 Semestre", ["Tous"] + [f"S{s}" for s in semestres])
    
    with col_f3:
        statuts = sorted(df['statut'].unique())
        statut_selectionne = st.selectbox("📊 Statut", ["Tous"] + statuts)
    
    df_filtered = df.copy()
    
    if formation_selectionnee != "Toutes":
        df_filtered = df_filtered[df_filtered['formation'] == formation_selectionnee]
    
    if semestre_selectionne != "Tous":
        sem_num = int(semestre_selectionne[1])
        df_filtered = df_filtered[df_filtered['semestre'] == sem_num]
    
    if statut_selectionne != "Tous":
        df_filtered = df_filtered[df_filtered['statut'] == statut_selectionne]
    
    st.markdown("---")
    
    df_display = df_filtered[['formation', 'niveau', 'module', 'semestre', 'groupe', 
                               'date_heure', 'salle', 'nb_etudiants', 'statut']].copy()
    
    if 'Professeurs' in df_filtered.columns:
        df_display['Professeurs'] = df_filtered['Professeurs']
    
    df_display.columns = ['Formation', 'Niveau', 'Module', 'Sem', 'Groupe',
                          'Date et Heure', 'Salle', 'Nb Étudiants', 'Statut'] + \
                         (['Professeurs'] if 'Professeurs' in df_display.columns else [])
    
    st.dataframe(df_display, use_container_width=True, hide_index=True)
    
    st.markdown("---")
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("📝 Total examens", len(df_filtered))
    with col2:
        st.metric("👨‍🎓 Total étudiants", int(df_filtered['nb_etudiants'].sum()))
    with col3:
        dates_uniques = pd.to_datetime(df_filtered['date_heure']).dt.date.nunique()
        st.metric("📅 Jours utilisés", dates_uniques)
    with col4:
        salles_uniques = df_filtered['salle'].nunique()
        st.metric("🏫 Salles utilisées", salles_uniques)

# ========== VALIDATION ==========

def afficher_validation(dept_id, chef_info):
    """Afficher l'interface de validation"""
    st.subheader("✅ Validation du Planning d'Examens")
    
    stats = get_stats_departement(dept_id)
    conflits = detecter_conflits(dept_id)
    
    st.markdown("### 📊 État Actuel du Planning")
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("📝 Examens Planifiés", stats['examens_planifies'], help="Examens avec statut 'planifie'")
    with col2:
        st.metric("✅ Examens Validés", stats['examens_valides'], help="Examens avec statut 'valide'")
    with col3:
        if len(conflits) == 0:
            st.metric("⚠️ Conflits", "0", delta="Aucun conflit", delta_color="normal")
        else:
            st.metric("⚠️ Conflits", len(conflits), delta=f"{len(conflits)} détectés", delta_color="inverse")
    with col4:
        taux_complet = ((stats['examens_planifies'] + stats['examens_valides']) / stats['examens_total'] * 100) if stats['examens_total'] > 0 else 0
        st.metric("📊 Taux de Planification", f"{taux_complet:.1f}%")
    
    st.markdown("---")
    
    if len(conflits) > 0:
        st.error(f"""
        ❌ **Validation Impossible**
        
        Le planning contient **{len(conflits)} conflit(s)** qui doivent être résolus avant validation.
        
        Veuillez consulter l'onglet **"⚠️ Conflits"** pour plus de détails.
        """)
        
        with st.expander("📋 Résumé des conflits"):
            conflits_etudiants = [c for c in conflits if c['type'] == 'Étudiant']
            conflits_profs = [c for c in conflits if c['type'] == 'Professeur']
            conflits_salles = [c for c in conflits if c['type'] == 'Salle']
            
            if conflits_etudiants:
                st.warning(f"👨‍🎓 {len(conflits_etudiants)} conflits étudiants")
            if conflits_profs:
                st.warning(f"👨‍🏫 {len(conflits_profs)} conflits professeurs")
            if conflits_salles:
                st.warning(f"🏫 {len(conflits_salles)} conflits de salles")
    
    elif stats['examens_planifies'] == 0:
        st.success("""
        ✅ **Tous les examens sont déjà validés**
        
        Tous les examens de votre département ont été validés avec succès.
        """)
    
    else:
        st.success(f"""
        ✅ **Le planning est prêt à être validé**
        
        - Aucun conflit détecté
        - {stats['examens_planifies']} examens planifiés
        - Toutes les contraintes sont respectées
        """)
        
        st.markdown("### 🔐 Validation Définitive")
        
        st.warning("""
        ⚠️ **ATTENTION** : Cette action est **IRRÉVERSIBLE** !
        
        En validant ce planning:
        - Les {nb_examens} examens planifiés passeront au statut **'valide'**
        - Le Vice-Doyen pourra consulter votre validation
        - Vous ne pourrez plus modifier ces examens
        - Cette validation sera enregistrée avec votre identité et la date
        """.format(nb_examens=stats['examens_planifies']))
        
        confirmation = st.checkbox(
            "Je confirme avoir vérifié le planning et souhaite procéder à la validation définitive",
            key="confirm_validation"
        )
        
        col_btn1, col_btn2 = st.columns([1, 3])
        
        with col_btn1:
            if st.button("✅ VALIDER LE PLANNING", type="primary", disabled=not confirmation, use_container_width=True):
                with st.spinner("⏳ Validation en cours..."):
                    resultat = valider_planning_departement(dept_id, chef_info)
                    
                    if resultat['success']:
                        st.success(f"""
                        🎉 **Validation Réussie !**
                        
                        ✅ {resultat['nb_valides']} examens ont été validés
                        📅 Date de validation: {resultat['date_validation']}
                        👔 Validé par: {resultat['validateur']}
                        """)
                        st.balloons()
                        
                        st.markdown("### 📊 État Après Validation")
                        stats_apres = get_stats_departement(dept_id)
                        
                        col1, col2, col3 = st.columns(3)
                        with col1:
                            st.metric("📝 Examens Planifiés", stats_apres['examens_planifies'], 
                                      delta=-(stats['examens_planifies']), delta_color="off")
                        with col2:
                            st.metric("✅ Examens Validés", stats_apres['examens_valides'], 
                                      delta=resultat['nb_valides'], delta_color="normal")
                        with col3:
                            taux_valid = (stats_apres['examens_valides'] / stats_apres['examens_total'] * 100) if stats_apres['examens_total'] > 0 else 0
                            st.metric("📊 Taux de Validation", f"{taux_valid:.1f}%")
                        
                        import time
                        time.sleep(2)
                        st.rerun()
                    else:
                        st.error(f"❌ Erreur lors de la validation: {resultat['message']}")
        
        with col_btn2:
            if st.button("📋 Exporter le Planning", use_container_width=True):
                st.info("🚧 Fonctionnalité d'export en cours de développement")

def valider_planning_departement(dept_id, chef_info):
    """Valider le planning d'un département"""
    try:
        query_count = """
        SELECT COUNT(*) as nb_examens
        FROM examens e
        JOIN modules m ON e.module_id = m.id
        JOIN formations f ON m.formation_id = f.id
        WHERE f.dept_id = %s AND e.statut = 'planifie'
        """
        result_count = db.execute_query(query_count, (dept_id,))
        nb_examens = result_count[0]['nb_examens'] if result_count else 0
        
        if nb_examens == 0:
            return {'success': False, 'message': 'Aucun examen à valider', 'nb_valides': 0}
        
        query_update = """
        UPDATE examens e
        JOIN modules m ON e.module_id = m.id
        JOIN formations f ON m.formation_id = f.id
        SET e.statut = 'valide', e.date_validation = NOW(), e.validateur_id = %s
        WHERE f.dept_id = %s AND e.statut = 'planifie'
        """
        db.execute_query(query_update, (chef_info['id'], dept_id))
        
        query_create_table = """
        CREATE TABLE IF NOT EXISTS validations_planning (
            id INT PRIMARY KEY AUTO_INCREMENT,
            dept_id INT NOT NULL,
            chef_id INT NOT NULL,
            date_validation DATETIME NOT NULL,
            nb_examens_valides INT NOT NULL,
            commentaire TEXT,
            FOREIGN KEY (dept_id) REFERENCES departements(id),
            FOREIGN KEY (chef_id) REFERENCES professeurs(id),
            INDEX idx_dept_date (dept_id, date_validation)
        )
        """
        db.execute_query(query_create_table)
        
        query_insert_validation = """
        INSERT INTO validations_planning (dept_id, chef_id, date_validation, nb_examens_valides)
        VALUES (%s, %s, NOW(), %s)
        """
        db.execute_query(query_insert_validation, (dept_id, chef_info['id'], nb_examens))
        
        return {
            'success': True,
            'message': 'Validation effectuée avec succès',
            'nb_valides': nb_examens,
            'date_validation': datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            'validateur': f"{chef_info['prenom']} {chef_info['nom']}"
        }
        
    except Exception as e:
        print(f"Erreur lors de la validation: {e}")
        import traceback
        traceback.print_exc()
        return {'success': False, 'message': str(e), 'nb_valides': 0}

# ========== PAGE PRINCIPALE ==========

def main_page():
    """Page principale du chef de département"""
    chef = st.session_state['chef']
    dept_id = chef['dept_id']
    
    col1, col2 = st.columns([4, 1])
    with col1:
        st.title("👔 Espace Chef de Département")
        st.markdown(f"### {chef['departement']} ({chef['dept_code']})")
    with col2:
        st.markdown("##")
        if st.button("🚪 Déconnexion", type="secondary"):
            st.session_state.clear()
            st.rerun()
    
    st.markdown(f"**Chef:** {chef['prenom']} {chef['nom']} | **Email:** {chef['email']}")
    st.markdown("---")
    
    tabs = st.tabs(["📊 Statistiques", "⚠️ Conflits", "📚 Examens", "✅ Validation"])
    
    with tabs[0]:
        afficher_statistiques(dept_id)
    
    with tabs[1]:
        afficher_conflits(dept_id)
    
    with tabs[2]:
        afficher_examens_par_formation(dept_id)
    
    with tabs[3]:
        afficher_validation(dept_id, chef)

# ========== MAIN ==========

def main():
    if 'authenticated_chef' not in st.session_state:
        st.session_state['authenticated_chef'] = False
    
    if st.session_state['authenticated_chef']:
        main_page()
    else:
        login_page()

if __name__ == "__main__":
    main()