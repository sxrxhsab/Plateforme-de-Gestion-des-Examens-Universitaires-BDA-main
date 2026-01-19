"""
Page Admin Examens - Génération et optimisation des emplois du temps
🔒 AVEC LOGIN INTÉGRÉ - VERSION PAR SEMESTRE
📅 GÉNÉRATION SÉPARÉE : SEMESTRE 1 et SEMESTRE 2
"""
import streamlit as st
import sys
from pathlib import Path
from datetime import datetime, timedelta
import pandas as pd
import hashlib

sys.path.insert(0, str(Path(__file__).parent.parent))

from backend.db_connection import db
from backend.detect_conflicts import conflict_detector
from backend.generate_edt import scheduler  # ✅ Utilise generate_edt.py

st.set_page_config(
    page_title="Admin Examens",
    page_icon="⚙️",
    layout="wide"
)

# ========== FONCTIONS LOGIN ==========
def hash_password(password):
    """Hasher le mot de passe avec SHA-256"""
    return hashlib.sha256(password.encode()).hexdigest()

def verify_admin_credentials(username, password):
    """Vérifier les identifiants administrateur"""
    try:
        password_hash = hash_password(password)
        query = "SELECT id, username FROM admin WHERE username = %s AND password = %s"
        result = db.execute_query(query, (username, password_hash))
        
        if result and len(result) > 0:
            return True, result[0]
        else:
            return False, None
    except Exception as e:
        st.error(f"❌ Erreur: {e}")
        return False, None

def show_login_page():
    """Afficher la page de connexion"""
    st.title("🔐 Authentification Administrateur")
    st.markdown("---")
    
    col1, col2, col3 = st.columns([1, 2, 1])
    
    with col2:
        st.markdown("### 🔑 Connexion requise")
        
        with st.form("login_form"):
            username = st.text_input("👤 Nom d'utilisateur", placeholder="admin")
            password = st.text_input("🔒 Mot de passe", type="password", placeholder="Entrez votre mot de passe")
            
            submitted = st.form_submit_button("🔓 Se connecter", use_container_width=True, type="primary")
            
            if submitted:
                if not username or not password:
                    st.error("⚠️ Veuillez remplir tous les champs")
                else:
                    is_valid, admin_data = verify_admin_credentials(username, password)
                    
                    if is_valid:
                        st.session_state.authenticated_admin = True
                        st.session_state.admin_id = admin_data['id']
                        st.session_state.admin_username = admin_data['username']
                        st.success(f"✅ Bienvenue {admin_data['username']} !")
                        st.rerun()
                    else:
                        st.error("❌ Identifiants incorrects")

# ========== VÉRIFICATION LOGIN ==========
if not st.session_state.get('authenticated_admin', False):
    show_login_page()
    st.stop()

# ========== SIDEBAR ==========
with st.sidebar:
    username = st.session_state.get('admin_username', 'Admin')
    st.success(f"✅ Connecté: **{username}**")
    st.markdown("---")
    
    if st.button("🚪 Déconnexion", use_container_width=True):
        st.session_state.clear()
        st.rerun()

# ========== FONCTIONS ==========
def load_departments():
    """Charger la liste des départements"""
    query = "SELECT id, nom FROM departements ORDER BY nom"
    return db.execute_query(query)

def get_schedule_stats(semestre=None):
    """Obtenir les statistiques du planning actuel par semestre"""
    query = """
    SELECT 
        e.semestre,
        COUNT(DISTINCT e.id) as total_examens,
        COUNT(DISTINCT e.module_id) as modules_planifies,
        COUNT(DISTINCT e.salle_id) as salles_utilisees,
        COUNT(DISTINCT s.prof_id) as profs_mobilises,
        MIN(e.date_heure) as premiere_date,
        MAX(e.date_heure) as derniere_date
    FROM examens e
    LEFT JOIN surveillances s ON e.id = s.examen_id
    WHERE e.statut = 'planifie'
    """
    
    if semestre:
        query += f" AND e.semestre = {semestre}"
    
    query += " GROUP BY e.semestre ORDER BY e.semestre"
    
    result = db.execute_query(query)
    return result if result else []

def get_modules_count_by_semestre():
    """Compter les modules par semestre"""
    query = """
    SELECT 
        semestre,
        COUNT(DISTINCT m.id) as nb_modules,
        COUNT(DISTINCT CONCAT(m.id, '-', g.id)) as nb_examens_prevus
    FROM modules m
    JOIN formations f ON m.formation_id = f.id
    JOIN groupes g ON g.formation_id = f.id
    WHERE EXISTS (
        SELECT 1 
        FROM etudiants e 
        JOIN inscriptions i ON e.id = i.etudiant_id 
        WHERE i.module_id = m.id AND e.groupe_id = g.id
    )
    GROUP BY semestre
    ORDER BY semestre
    """
    return db.execute_query(query)

# ========== PAGE PRINCIPALE ==========
def main():
    col_title, col_user = st.columns([3, 1])
    with col_title:
        st.title("⚙️ Génération d'Emploi du Temps - Par Semestre")
        st.markdown("Interface d'administration pour la planification automatique des examens")
    with col_user:
        st.markdown("##")
        st.info(f"👤 {st.session_state.get('admin_username', 'Admin')}")
    
    st.markdown("---")
    
    # 🎯 AFFICHER LES STATS ACTUELLES PAR SEMESTRE
    st.markdown("### 📊 État Actuel des Plannings")
    
    stats_by_semestre = get_schedule_stats()
    modules_count = get_modules_count_by_semestre()
    
    col_s1, col_s2 = st.columns(2)
    
    with col_s1:
        st.markdown("#### 📅 Semestre 1")
        s1_stats = next((s for s in stats_by_semestre if s['semestre'] == 1), None)
        s1_modules = next((m for m in modules_count if m['semestre'] == 1), None)
        
        if s1_stats and s1_stats['total_examens'] > 0:
            st.success(f"""
            **✅ Planifié:**
            - {s1_stats['total_examens']} examens
            - {s1_stats['modules_planifies']} modules
            - {s1_stats['salles_utilisees']} salles
            - {s1_stats['profs_mobilises'] or 0} professeurs
            - Du {s1_stats['premiere_date'].strftime('%d/%m/%Y') if s1_stats['premiere_date'] else 'N/A'} au {s1_stats['derniere_date'].strftime('%d/%m/%Y') if s1_stats['derniere_date'] else 'N/A'}
            """)
        else:
            if s1_modules:
                st.warning(f"""
                **⚠️ Non planifié**
                - {s1_modules['nb_examens_prevus']} examens à planifier
                - {s1_modules['nb_modules']} modules
                """)
            else:
                st.info("ℹ️ Aucun module pour ce semestre")
    
    with col_s2:
        st.markdown("#### 📅 Semestre 2")
        s2_stats = next((s for s in stats_by_semestre if s['semestre'] == 2), None)
        s2_modules = next((m for m in modules_count if m['semestre'] == 2), None)
        
        if s2_stats and s2_stats['total_examens'] > 0:
            st.success(f"""
            **✅ Planifié:**
            - {s2_stats['total_examens']} examens
            - {s2_stats['modules_planifies']} modules
            - {s2_stats['salles_utilisees']} salles
            - {s2_stats['profs_mobilises'] or 0} professeurs
            - Du {s2_stats['premiere_date'].strftime('%d/%m/%Y') if s2_stats['premiere_date'] else 'N/A'} au {s2_stats['derniere_date'].strftime('%d/%m/%Y') if s2_stats['derniere_date'] else 'N/A'}
            """)
        else:
            if s2_modules:
                st.warning(f"""
                **⚠️ Non planifié**
                - {s2_modules['nb_examens_prevus']} examens à planifier
                - {s2_modules['nb_modules']} modules
                """)
            else:
                st.info("ℹ️ Aucun module pour ce semestre")
    
    st.markdown("---")
    
    tab1, tab2, tab3 = st.tabs(["🎯 Génération EDT", "🔍 Détection Conflits", "📊 Statistiques"])
    
    # TAB 1: Génération EDT PAR SEMESTRE
    with tab1:
        st.markdown("### 🎯 Génération automatique par semestre")
        
        # 🔥 SÉLECTION DU SEMESTRE
        st.markdown("#### 📅 Sélection du semestre")
        
        col_sem1, col_sem2 = st.columns(2)
        
        with col_sem1:
            semestre_1_selected = st.checkbox(
                "📘 Semestre 1", 
                value=True,
                help="Générer l'emploi du temps pour les modules du semestre 1"
            )
        
        with col_sem2:
            semestre_2_selected = st.checkbox(
                "📗 Semestre 2", 
                value=False,
                help="Générer l'emploi du temps pour les modules du semestre 2"
            )
        
        if not semestre_1_selected and not semestre_2_selected:
            st.error("⚠️ Veuillez sélectionner au moins un semestre")
            st.stop()
        
        semestres_to_generate = []
        if semestre_1_selected:
            semestres_to_generate.append(1)
        if semestre_2_selected:
            semestres_to_generate.append(2)
        
        st.info(f"📋 Semestres sélectionnés : {', '.join([f'S{s}' for s in semestres_to_generate])}")
        
        st.markdown("---")
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("#### 🏢 Scope de génération")
            
            departments = load_departments()
            dept_id = None
            
            if departments:
                dept_options = ["Tous les départements"] + [d['nom'] for d in departments]
                selected_dept = st.selectbox("Département", dept_options)
                
                if selected_dept != "Tous les départements":
                    dept_id = next(d['id'] for d in departments if d['nom'] == selected_dept)
                    st.success(f"✅ Génération pour: {selected_dept}")
                else:
                    st.info("ℹ️ Génération globale (tous départements)")
            else:
                st.error("❌ Aucun département trouvé")
            
            annee_academique = st.text_input(
                "Année académique", 
                value="2024-2025",
                help="Format: YYYY-YYYY"
            )
        
        with col2:
            st.markdown("#### ⚙️ Options")
            
            clear_existing = st.checkbox(
                "Effacer le planning existant avant génération",
                value=True,
                help="Supprime tous les examens planifiés pour les semestres sélectionnés"
            )
            
            st.markdown("---")
            
            st.info(f"""
            **💡 Périodes d'examen:**
            
            Les périodes sont configurées dans la table `periodes_examens`.
            
            Par défaut:
            - S1: 15 jan → 15 fév
            - S2: 1 juin → 1 juil
            """)
        
        st.markdown("---")
        
        # 🚀 BOUTONS DE GÉNÉRATION
        col_gen1, col_gen2, col_gen3 = st.columns([1, 1, 1])
        
        with col_gen1:
            if st.button("🚀 Générer les semestres sélectionnés", type="primary", use_container_width=True):
                results = {}
                
                for semestre in semestres_to_generate:
                    st.markdown(f"### 📅 Génération Semestre {semestre}")
                    
                    # Effacer si demandé
                    if clear_existing:
                        with st.spinner(f"🗑️ Effacement planning S{semestre}..."):
                            scheduler.clear_schedule(dept_id=dept_id, semestre=semestre, annee_academique=annee_academique)
                            st.success(f"✅ Planning S{semestre} effacé")
                    
                    # Générer
                    with st.spinner(f"⏳ Génération S{semestre} en cours..."):
                        progress_bar = st.progress(0)
                        progress_bar.progress(25)
                        
                        result = scheduler.generate_schedule(
                            semestre=semestre,
                            dept_id=dept_id,
                            annee_academique=annee_academique
                        )
                        
                        progress_bar.progress(100)
                    
                    results[semestre] = result
                    
                    # Afficher résultats
                    if result['success']:
                        st.success(f"✅ {result['message']}")
                        
                        stats = result['stats']
                        col_a, col_b, col_c = st.columns(3)
                        
                        with col_a:
                            st.metric("📝 Examens planifiés", stats['examens_planifies'])
                            st.metric("⏱️ Temps d'exécution", f"{stats['temps_execution']}s")
                        
                        with col_b:
                            st.metric("📚 Total modules", stats['modules_total'])
                            st.metric("🏫 Salles utilisées", stats['salles_utilisees'])
                        
                        with col_c:
                            st.metric("❌ Échecs", stats['examens_non_planifies'])
                            st.metric("✅ Taux de réussite", f"{stats['taux_reussite']}%")
                        
                        # Vérifier conflits
                        total_conflits = (stats.get('conflits_groupes', 0) + 
                                        stats.get('conflits_professeurs', 0) + 
                                        stats.get('conflits_salles', 0))
                        
                        if total_conflits == 0:
                            st.success("🎉 ZÉRO CONFLIT - Planning optimal!")
                        else:
                            st.warning(f"⚠️ {total_conflits} conflits détectés")
                    else:
                        st.error(f"❌ {result['message']}")
                    
                    st.markdown("---")
                
                # Résumé global
                if len(results) > 1:
                    st.markdown("### 📊 Résumé Global")
                    
                    total_planifies = sum(r['stats']['examens_planifies'] for r in results.values() if r['success'])
                    total_examens = sum(r['stats']['examens_total'] for r in results.values() if r['success'])
                    total_temps = sum(r['stats']['temps_execution'] for r in results.values() if r['success'])
                    
                    col_res1, col_res2, col_res3 = st.columns(3)
                    
                    with col_res1:
                        st.metric("📝 Total examens", f"{total_planifies}/{total_examens}")
                    
                    with col_res2:
                        taux_global = (total_planifies / total_examens * 100) if total_examens > 0 else 0
                        st.metric("✅ Taux global", f"{taux_global:.1f}%")
                    
                    with col_res3:
                        st.metric("⏱️ Temps total", f"{total_temps:.1f}s")
                    
                    if taux_global == 100:
                        st.balloons()
                        st.success("🎉 TOUS LES EXAMENS PLANIFIÉS AVEC SUCCÈS!")
                
                st.info("🔄 Rechargez la page pour voir les statistiques mises à jour")
        
        with col_gen2:
            if st.button("🗑️ Effacer Semestre 1", use_container_width=True):
                if st.session_state.get('confirm_delete_s1'):
                    try:
                        scheduler.clear_schedule(semestre=1, annee_academique=annee_academique)
                        st.success("✅ Planning S1 effacé")
                        st.session_state.confirm_delete_s1 = False
                        st.rerun()
                    except Exception as e:
                        st.error(f"❌ Erreur: {e}")
                else:
                    st.session_state.confirm_delete_s1 = True
                    st.warning("⚠️ Cliquez à nouveau pour confirmer")
        
        with col_gen3:
            if st.button("🗑️ Effacer Semestre 2", use_container_width=True):
                if st.session_state.get('confirm_delete_s2'):
                    try:
                        scheduler.clear_schedule(semestre=2, annee_academique=annee_academique)
                        st.success("✅ Planning S2 effacé")
                        st.session_state.confirm_delete_s2 = False
                        st.rerun()
                    except Exception as e:
                        st.error(f"❌ Erreur: {e}")
                else:
                    st.session_state.confirm_delete_s2 = True
                    st.warning("⚠️ Cliquez à nouveau pour confirmer")
    
    # TAB 2: Détection de conflits
    with tab2:
        st.markdown("### 🔍 Détection et résolution de conflits")
        
        if st.button("🔍 Analyser les conflits", type="primary"):
            with st.spinner("Analyse en cours..."):
                conflicts = conflict_detector.detect_all_conflicts()
                summary = conflict_detector.get_conflicts_summary()
            
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                total = (summary['total_etudiants'] + summary['total_professeurs'] + 
                        summary['total_salles'] + summary['total_chevauchements'])
                st.metric("⚠️ Total conflits", total)
            
            with col2:
                st.metric("👨‍🎓 Étudiants", summary['total_etudiants'])
            
            with col3:
                st.metric("👨‍🏫 Professeurs", summary['total_professeurs'])
            
            with col4:
                st.metric("🏫 Salles", summary['total_salles'])
            
            st.markdown("---")
            
            if summary['has_conflicts']:
                if conflicts['etudiants']:
                    st.markdown("#### 👨‍🎓 Conflits étudiants")
                    df_etu = pd.DataFrame(conflicts['etudiants'])
                    if 'jour' in df_etu.columns:
                        df_etu['jour'] = pd.to_datetime(df_etu['jour']).dt.strftime('%d/%m/%Y')
                    st.dataframe(df_etu, use_container_width=True, hide_index=True)
                    st.markdown("---")
                
                if conflicts['professeurs']:
                    st.markdown("#### 👨‍🏫 Conflits professeurs")
                    df_prof = pd.DataFrame(conflicts['professeurs'])
                    if 'date_surveillance' in df_prof.columns:
                        df_prof['date_surveillance'] = pd.to_datetime(df_prof['date_surveillance']).dt.strftime('%d/%m/%Y')
                    st.dataframe(df_prof, use_container_width=True, hide_index=True)
                    st.markdown("---")
                
                if conflicts['salles']:
                    st.markdown("#### 🏫 Conflits salles")
                    df_salle = pd.DataFrame(conflicts['salles'])
                    if 'date_heure' in df_salle.columns:
                        df_salle['date_heure'] = pd.to_datetime(df_salle['date_heure']).dt.strftime('%d/%m/%Y %H:%M')
                    st.dataframe(df_salle, use_container_width=True, hide_index=True)
            else:
                st.success("✅ Aucun conflit détecté!")
    
    # TAB 3: Statistiques
    with tab3:
        st.markdown("### 📊 Statistiques par semestre")
        
        stats_query = """
        SELECT 
            e.semestre,
            COUNT(DISTINCT e.id) as total_examens,
            COUNT(DISTINCT e.module_id) as modules_planifies,
            COUNT(DISTINCT e.salle_id) as salles_utilisees,
            COUNT(DISTINCT sv.prof_id) as profs_mobilises
        FROM examens e
        LEFT JOIN surveillances sv ON e.id = sv.examen_id
        WHERE e.statut = 'planifie'
        GROUP BY e.semestre
        ORDER BY e.semestre
        """
        
        stats = db.execute_query(stats_query)
        
        if stats:
            for stat_row in stats:
                sem = stat_row['semestre']
                st.markdown(f"##### 📅 Semestre {sem if sem else 'N/A'}")
                
                col1, col2, col3, col4 = st.columns(4)
                
                with col1:
                    st.metric("📝 Examens", stat_row['total_examens'])
                
                with col2:
                    st.metric("📚 Modules", stat_row['modules_planifies'])
                
                with col3:
                    st.metric("🏫 Salles", stat_row['salles_utilisees'])
                
                with col4:
                    st.metric("👨‍🏫 Profs", stat_row['profs_mobilises'] or 0)
                
                st.markdown("---")
        else:
            st.info("Aucun examen planifié")

if __name__ == "__main__":
    main()