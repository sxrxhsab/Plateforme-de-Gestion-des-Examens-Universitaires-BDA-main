"""
Page Étudiant - Consultation de l'emploi du temps
🎯 AVEC FILTRE PAR SEMESTRE
📅 Affichage des examens par semestre (S1 ou S2)
🚪 AVEC BOUTON DE DÉCONNEXION QUI EFFACE TOUT
"""
import streamlit as st
import sys
from pathlib import Path
from datetime import datetime
import pandas as pd

sys.path.insert(0, str(Path(__file__).parent.parent))

from backend.db_connection import db

st.set_page_config(
    page_title="Étudiant - EDT",
    page_icon="👨‍🎓",
    layout="wide"
)

# ========== FONCTIONS ==========
def load_student_schedule(matricule, semestre=None):
    """
    Charger l'emploi du temps d'un étudiant FILTRÉ PAR SEMESTRE
    
    Args:
        matricule: Matricule de l'étudiant
        semestre: 1, 2 ou None (tous)
    
    Returns:
        list: Liste des examens
    """
    query = """
    SELECT 
        e.id as examen_id,
        m.nom as module_nom,
        m.code as module_code,
        m.credits,
        m.semestre as module_semestre,
        e.date_heure,
        DATE(e.date_heure) as date_examen,
        e.duree_minutes,
        s.nom as salle_nom,
        s.type as salle_type,
        s.batiment,
        p.nom as prof_nom,
        p.prenom as prof_prenom,
        f.nom as formation_nom,
        g.nom as groupe_nom,
        e.statut,
        DAYNAME(e.date_heure) as jour_semaine
    FROM etudiants et
    JOIN formations f ON et.formation_id = f.id
    JOIN groupes g ON et.groupe_id = g.id
    JOIN inscriptions i ON et.id = i.etudiant_id
    JOIN modules m ON i.module_id = m.id
    LEFT JOIN examens e ON m.id = e.module_id 
        AND e.groupe_id = et.groupe_id
        AND e.statut = 'planifie'
    LEFT JOIN salles s ON e.salle_id = s.id
    LEFT JOIN professeurs p ON e.prof_id = p.id
    WHERE et.matricule = %s
    """
    
    # 🔥 FILTRE PAR SEMESTRE
    if semestre:
        query += f" AND m.semestre = {semestre}"
    
    query += " ORDER BY e.date_heure, m.nom"
    
    result = db.execute_query(query, (matricule,))
    return result if result else []

def get_student_info(matricule):
    """Obtenir les informations de l'étudiant"""
    query = """
    SELECT 
        e.id,
        e.matricule,
        e.nom,
        e.prenom,
        e.email,
        e.promo,
        f.nom as formation_nom,
        f.niveau as formation_niveau,
        g.nom as groupe_nom,
        d.nom as departement_nom
    FROM etudiants e
    JOIN formations f ON e.formation_id = f.id
    JOIN groupes g ON e.groupe_id = g.id
    JOIN departements d ON f.dept_id = d.id
    WHERE e.matricule = %s
    """
    
    result = db.execute_query(query, (matricule,))
    return result[0] if result else None

def get_exam_stats(matricule, semestre=None):
    """
    Obtenir les statistiques des examens FILTRÉES PAR SEMESTRE
    
    Args:
        matricule: Matricule de l'étudiant
        semestre: 1, 2 ou None (tous)
    
    Returns:
        dict: Statistiques
    """
    query = """
    SELECT 
        COUNT(DISTINCT e.id) as nb_examens,
        COUNT(DISTINCT m.id) as nb_modules,
        SUM(m.credits) as total_credits,
        MIN(e.date_heure) as premier_examen,
        MAX(e.date_heure) as dernier_examen,
        COUNT(DISTINCT DATE(e.date_heure)) as nb_jours_examens
    FROM etudiants et
    JOIN inscriptions i ON et.id = i.etudiant_id
    JOIN modules m ON i.module_id = m.id
    LEFT JOIN examens e ON m.id = e.module_id 
        AND e.groupe_id = et.groupe_id
        AND e.statut = 'planifie'
    WHERE et.matricule = %s
    """
    
    # 🔥 FILTRE PAR SEMESTRE
    if semestre:
        query += f" AND m.semestre = {semestre}"
    
    result = db.execute_query(query, (matricule,))
    return result[0] if result else None

def check_conflicts(matricule, semestre=None):
    """
    Vérifier s'il y a des conflits pour cet étudiant FILTRÉ PAR SEMESTRE
    
    Args:
        matricule: Matricule de l'étudiant
        semestre: 1, 2 ou None (tous)
    
    Returns:
        list: Liste des conflits
    """
    query = """
    SELECT 
        DATE(e.date_heure) as jour,
        COUNT(DISTINCT e.id) as nb_examens,
        GROUP_CONCAT(
            DISTINCT CONCAT(TIME(e.date_heure), ' - ', m.nom)
            ORDER BY e.date_heure
            SEPARATOR ' | '
        ) as examens_detail
    FROM etudiants et
    JOIN inscriptions i ON et.id = i.etudiant_id
    JOIN modules m ON i.module_id = m.id
    JOIN examens e ON m.id = e.module_id 
        AND e.groupe_id = et.groupe_id
        AND e.statut = 'planifie'
    WHERE et.matricule = %s
    """
    
    # 🔥 FILTRE PAR SEMESTRE
    if semestre:
        query += f" AND m.semestre = {semestre}"
    
    query += """
    GROUP BY DATE(e.date_heure)
    HAVING COUNT(DISTINCT e.id) > 1
    ORDER BY jour
    """
    
    result = db.execute_query(query, (matricule,))
    return result if result else []

def get_modules_by_semestre(matricule):
    """
    Obtenir le nombre de modules par semestre pour cet étudiant
    
    Args:
        matricule: Matricule de l'étudiant
    
    Returns:
        dict: {semestre: nombre_modules}
    """
    query = """
    SELECT 
        m.semestre,
        COUNT(DISTINCT m.id) as nb_modules,
        COUNT(DISTINCT e.id) as nb_examens_planifies
    FROM etudiants et
    JOIN inscriptions i ON et.id = i.etudiant_id
    JOIN modules m ON i.module_id = m.id
    LEFT JOIN examens e ON m.id = e.module_id 
        AND e.groupe_id = et.groupe_id
        AND e.statut = 'planifie'
    WHERE et.matricule = %s
    GROUP BY m.semestre
    ORDER BY m.semestre
    """
    
    result = db.execute_query(query, (matricule,))
    
    if result:
        return {
            row['semestre']: {
                'nb_modules': row['nb_modules'],
                'nb_examens': row['nb_examens_planifies'] or 0
            }
            for row in result
        }
    return {}

def logout():
    """Fonction de déconnexion complète"""
    # Effacer TOUTES les clés de session
    all_keys = list(st.session_state.keys())
    for key in all_keys:
        del st.session_state[key]

# ========== PAGE PRINCIPALE ==========
def main():
    # 🔥 Initialiser le compteur de session (pour forcer la réinitialisation)
    if "session_id" not in st.session_state:
        st.session_state["session_id"] = 0
    
    # 🔥 VÉRIFIER SI DÉCONNEXION DEMANDÉE
    if st.session_state.get("logout_requested", False):
        logout()
        # Incrémenter le session_id pour forcer la recréation des widgets
        st.session_state["session_id"] = st.session_state.get("session_id", 0) + 1
        if "logout_requested" in st.session_state:
            del st.session_state["logout_requested"]
        st.rerun()
    
    # 🔥 En-tête avec bouton déconnexion
    col_title, col_logout = st.columns([5, 1])
    
    with col_title:
        st.title("👨‍🎓 Emploi du Temps des Examens - Étudiant")
        st.markdown("Consultez votre emploi du temps d'examens par semestre")
    
    with col_logout:
        st.markdown("##")
        if st.button("🚪 Déconnexion", type="secondary", use_container_width=True, key="btn_logout"):
            # Marquer la déconnexion
            st.session_state["logout_requested"] = True
            st.rerun()
    
    st.markdown("---")
    
    # ========== SECTION: IDENTIFICATION ==========
    st.markdown("### 🔍 Identification")
    
    col1, col2 = st.columns([2, 1])
    
    with col1:
        # 🔥 Utiliser session_id dans la clé pour forcer la recréation du widget
        session_id = st.session_state.get("session_id", 0)
        
        matricule = st.text_input(
            "Entrez votre matricule",
            placeholder="Ex: 20241234",
            help="Votre matricule étudiant unique",
            key=f"input_matricule_{session_id}"
        )
    
    with col2:
        st.markdown("##")
        # Bouton de recherche
        search_button = st.button("🔍 Rechercher", type="primary", use_container_width=True, key="btn_search")
    
    # Si aucun matricule saisi
    if not matricule:
        st.info("👆 Entrez votre matricule pour voir votre emploi du temps")
        
        # Exemples de matricules
        st.markdown("---")
        st.markdown("#### 💡 Exemples de matricules")
        
        query = """
        SELECT matricule, CONCAT(prenom, ' ', nom) as nom_complet, f.nom as formation
        FROM etudiants e
        JOIN formations f ON e.formation_id = f.id
        LIMIT 5
        """
        exemples = db.execute_query(query)
        
        if exemples:
            for ex in exemples:
                st.code(f"{ex['matricule']} - {ex['nom_complet']} ({ex['formation']})")
        
        st.stop()
    
    # ========== SECTION: INFORMATIONS ÉTUDIANT ==========
    student = get_student_info(matricule)
    
    if not student:
        st.error(f"❌ Aucun étudiant trouvé avec le matricule: {matricule}")
        st.stop()
    
    # 🔥 Sauvegarder le matricule validé dans la session
    st.session_state["current_matricule"] = matricule
    st.session_state["student_authenticated"] = True
    
    st.success(f"✅ Étudiant trouvé: {student['prenom']} {student['nom']}")
    
    # Carte d'information
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("📋 Matricule", student['matricule'])
    
    with col2:
        st.metric("🎓 Formation", student['formation_niveau'])
    
    with col3:
        st.metric("👥 Groupe", student['groupe_nom'])
    
    with col4:
        st.metric("🏛️ Département", student['departement_nom'])
    
    st.markdown("---")
    
    # ========== SECTION: SÉLECTION DU SEMESTRE ==========
    st.markdown("### 📅 Sélection du Semestre")
    
    # Récupérer les modules par semestre
    modules_par_semestre = get_modules_by_semestre(matricule)
    
    col_sem_info, col_sem_select = st.columns([2, 1])
    
    with col_sem_info:
        if modules_par_semestre:
            st.info(f"""
            **📊 Vos modules:**
            - Semestre 1: {modules_par_semestre.get(1, {}).get('nb_modules', 0)} modules ({modules_par_semestre.get(1, {}).get('nb_examens', 0)} examens planifiés)
            - Semestre 2: {modules_par_semestre.get(2, {}).get('nb_modules', 0)} modules ({modules_par_semestre.get(2, {}).get('nb_examens', 0)} examens planifiés)
            """)
        else:
            st.warning("⚠️ Aucun module trouvé")
    
    with col_sem_select:
        semestre_options = {
            0: "📚 Tous les semestres",
            1: "📘 Semestre 1",
            2: "📗 Semestre 2"
        }
        
        selected_semestre = st.selectbox(
            "Afficher",
            options=list(semestre_options.keys()),
            format_func=lambda x: semestre_options[x],
            index=0,
            key=f"semestre_selector_{st.session_state.get('session_id', 0)}"
        )
    
    # Déterminer le filtre
    semestre_filter = None if selected_semestre == 0 else selected_semestre
    
    st.markdown("---")
    
    # ========== SECTION: STATISTIQUES ==========
    st.markdown(f"### 📊 Statistiques {semestre_options[selected_semestre]}")
    
    stats = get_exam_stats(matricule, semestre_filter)
    
    if stats:
        col1, col2, col3, col4, col5 = st.columns(5)
        
        with col1:
            st.metric("📝 Examens", stats['nb_examens'] or 0)
        
        with col2:
            st.metric("📚 Modules", stats['nb_modules'] or 0)
        
        with col3:
            st.metric("⭐ Crédits", stats['total_credits'] or 0)
        
        with col4:
            st.metric("📅 Jours", stats['nb_jours_examens'] or 0)
        
        with col5:
            if stats['premier_examen'] and stats['dernier_examen']:
                duree = (stats['dernier_examen'] - stats['premier_examen']).days + 1
                st.metric("⏱️ Durée", f"{duree}j")
            else:
                st.metric("⏱️ Durée", "N/A")
    
    st.markdown("---")
    
    # ========== SECTION: VÉRIFICATION CONFLITS ==========
    conflicts = check_conflicts(matricule, semestre_filter)
    
    if conflicts:
        st.error(f"⚠️ **ATTENTION: {len(conflicts)} conflit(s) détecté(s) !**")
        
        for conflict in conflicts:
            st.warning(f"""
            **{conflict['jour'].strftime('%d/%m/%Y')}** - {conflict['nb_examens']} examens:
            {conflict['examens_detail']}
            """)
        
        st.markdown("---")
    else:
        st.success("✅ Aucun conflit détecté - Vous avez maximum 1 examen par jour")
        st.markdown("---")
    
    # ========== SECTION: EMPLOI DU TEMPS ==========
    st.markdown(f"### 📅 Emploi du Temps {semestre_options[selected_semestre]}")
    
    schedule = load_student_schedule(matricule, semestre_filter)
    
    if not schedule:
        st.warning(f"⚠️ Aucun examen planifié pour {semestre_options[selected_semestre].lower()}")
        st.info("💡 Les examens seront bientôt disponibles. Revenez plus tard.")
        st.stop()
    
    # Filtrer seulement les examens planifiés
    schedule_with_exams = [s for s in schedule if s['examen_id'] is not None]
    
    if not schedule_with_exams:
        st.warning(f"⚠️ Aucun examen planifié pour {semestre_options[selected_semestre].lower()}")
        st.info("💡 Les examens seront bientôt disponibles. Revenez plus tard.")
        st.stop()
    
    # ========== AFFICHAGE: TABLEAU ==========
    tab1, tab2, tab3 = st.tabs(["📋 Liste des Examens", "📅 Calendrier", "📊 Par Date"])
    
    with tab1:
        st.markdown("#### 📋 Liste Complète des Examens")
        
        df_data = []
        for exam in schedule_with_exams:
            # Formater l'heure correctement
            if exam['date_heure']:
                heure_str = exam['date_heure'].strftime('%H:%M')
            else:
                heure_str = 'N/A'
            
            df_data.append({
                'Date': exam['date_examen'].strftime('%d/%m/%Y') if exam['date_examen'] else 'N/A',
                'Heure': heure_str,
                'Semestre': f"S{exam['module_semestre']}" if exam['module_semestre'] else 'N/A',
                'Module': exam['module_nom'],
                'Code': exam['module_code'],
                'Crédits': exam['credits'],
                'Durée': f"{exam['duree_minutes']}min" if exam['duree_minutes'] else 'N/A',
                'Salle': exam['salle_nom'] or 'N/A',
                'Bâtiment': exam['batiment'] or 'N/A',
                'Surveillant': f"{exam['prof_prenom']} {exam['prof_nom']}" if exam['prof_nom'] else 'N/A'
            })
        
        df = pd.DataFrame(df_data)
        st.dataframe(df, use_container_width=True, hide_index=True)
        
        # Export CSV
        csv = df.to_csv(index=False, encoding='utf-8-sig')
        st.download_button(
            label="📥 Télécharger en CSV",
            data=csv,
            file_name=f"emploi_temps_{matricule}_S{selected_semestre if selected_semestre else 'ALL'}.csv",
            mime="text/csv"
        )
    
    with tab2:
        st.markdown("#### 📅 Vue Calendrier")
        
        # Regrouper par date
        examens_par_date = {}
        for exam in schedule_with_exams:
            date_str = exam['date_examen'].strftime('%d/%m/%Y') if exam['date_examen'] else 'N/A'
            if date_str not in examens_par_date:
                examens_par_date[date_str] = []
            examens_par_date[date_str].append(exam)
        
        # Afficher par date
        for date_str in sorted(examens_par_date.keys()):
            with st.expander(f"📅 {date_str} ({len(examens_par_date[date_str])} examen(s))"):
                for exam in sorted(examens_par_date[date_str], key=lambda x: x['date_heure'] or datetime.min):
                    col1, col2, col3 = st.columns([1, 2, 1])
                    
                    # Formater l'heure
                    if exam['date_heure']:
                        heure_str = exam['date_heure'].strftime('%H:%M')
                    else:
                        heure_str = 'N/A'
                    
                    with col1:
                        st.markdown(f"**🕐 {heure_str}**")
                        st.caption(f"Durée: {exam['duree_minutes']}min")
                    
                    with col2:
                        st.markdown(f"**{exam['module_nom']}** (S{exam['module_semestre']})")
                        st.caption(f"Code: {exam['module_code']} | {exam['credits']} crédits")
                    
                    with col3:
                        st.markdown(f"📍 **{exam['salle_nom']}**")
                        st.caption(f"Bâtiment {exam['batiment']}")
                    
                    st.markdown("---")
    
    with tab3:
        st.markdown("#### 📊 Examens par Date")
        
        # Compter examens par jour
        dates_count = {}
        for exam in schedule_with_exams:
            date_str = exam['date_examen'].strftime('%d/%m/%Y') if exam['date_examen'] else 'N/A'
            dates_count[date_str] = dates_count.get(date_str, 0) + 1
        
        # Créer un DataFrame pour le graphique
        chart_data = pd.DataFrame({
            'Date': list(dates_count.keys()),
            'Nombre d\'examens': list(dates_count.values())
        })
        
        chart_data = chart_data.set_index('Date')
        st.bar_chart(chart_data)
        
        # Tableau récapitulatif
        st.markdown("##### Répartition des examens")
        recap_data = []
        for date_str, count in sorted(dates_count.items()):
            examens_jour = [e for e in schedule_with_exams if e['date_examen'].strftime('%d/%m/%Y') == date_str]
            modules_list = ', '.join([e['module_code'] for e in examens_jour])
            
            recap_data.append({
                'Date': date_str,
                'Nb Examens': count,
                'Modules': modules_list
            })
        
        df_recap = pd.DataFrame(recap_data)
        st.dataframe(df_recap, use_container_width=True, hide_index=True)
    
    st.markdown("---")
    
    # ========== SECTION: INFORMATIONS COMPLÉMENTAIRES ==========
    st.markdown("### 💡 Informations Importantes")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.info("""
        **📋 Conseils pour les examens:**
        - Arrivez 15 minutes avant l'heure
        - Apportez votre carte d'étudiant
        - Vérifiez le bâtiment et la salle
        - Préparez votre matériel autorisé
        """)
    
    with col2:
        st.warning("""
        **⚠️ En cas de conflit:**
        - Contactez immédiatement votre chef de département
        - Ne manquez aucun examen
        - Demandez une attestation si nécessaire
        """)

if __name__ == "__main__":
    main()