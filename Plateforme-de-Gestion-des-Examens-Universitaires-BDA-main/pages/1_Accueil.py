"""
Page Accueil - Dashboard Principal
Vue d'ensemble de la plateforme EDT Examens
"""
import streamlit as st
import sys
from pathlib import Path
import pandas as pd

sys.path.insert(0, str(Path(__file__).parent.parent))

from backend.db_connection import db

# ========================================
# CONFIGURATION
# ========================================

st.set_page_config(
    page_title="Accueil - EDT Examens",
    page_icon="🏠",
    layout="wide"
)

# ========================================
# STYLES CSS
# ========================================

st.markdown("""
<style>
    .metric-card {
        text-align: center;
        padding: 25px;
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        border-radius: 15px;
        color: white;
        box-shadow: 0 4px 6px rgba(0,0,0,0.1);
    }
    .metric-card h1 {
        font-size: 3.5em;
        margin: 0;
        font-weight: bold;
    }
    .metric-card p {
        margin: 10px 0 0 0;
        font-size: 1.3em;
        opacity: 0.95;
    }
    .info-box {
        padding: 20px;
        border-radius: 10px;
        border-left: 5px solid #667eea;
        background: #f8f9fa;
        margin: 10px 0;
    }
    .section-title {
        font-size: 1.8em;
        font-weight: bold;
        margin-bottom: 20px;
        color: #333;
    }
</style>
""", unsafe_allow_html=True)

# ========================================
# FONCTIONS BASE DE DONNÉES
# ========================================

def get_global_stats():
    """Récupérer les statistiques globales de la plateforme"""
    query = """
    SELECT 
        (SELECT COUNT(*) FROM etudiants) as nb_etudiants,
        (SELECT COUNT(*) FROM professeurs) as nb_profs,
        (SELECT COUNT(*) FROM formations) as nb_formations,
        (SELECT COUNT(*) FROM modules) as nb_modules,
        (SELECT COUNT(*) FROM salles WHERE disponible=1) as nb_salles,
        (SELECT COUNT(*) FROM examens WHERE statut='planifie') as nb_examens,
        (SELECT COUNT(*) FROM departements) as nb_depts,
        (SELECT COUNT(*) FROM groupes) as nb_groupes
    """
    result = db.execute_query(query)
    return result[0] if result else None

def get_dept_summary():
    """Récupérer le résumé par département"""
    query = """
    SELECT 
        d.nom as departement,
        COUNT(DISTINCT f.id) as formations,
        COUNT(DISTINCT e.id) as etudiants,
        COUNT(DISTINCT ex.id) as examens
    FROM departements d
    LEFT JOIN formations f ON d.id = f.dept_id
    LEFT JOIN etudiants e ON f.id = e.formation_id
    LEFT JOIN modules m ON f.id = m.formation_id
    LEFT JOIN examens ex ON m.id = ex.module_id AND ex.statut = 'planifie'
    GROUP BY d.id, d.nom
    ORDER BY etudiants DESC
    """
    return db.execute_query(query)



def get_planning_period():
    """Récupérer la période du planning"""
    query = """
    SELECT 
        MIN(date_heure) as debut,
        MAX(date_heure) as fin
    FROM examens
    WHERE statut = 'planifie'
    """
    result = db.execute_query(query)
    return result[0] if result else None

# ========================================
# COMPOSANTS D'AFFICHAGE
# ========================================

def display_metric_card(value, label, icon):
    """Afficher une carte métrique stylisée"""
    st.markdown(f"""
    <div class="metric-card">
        <h1>{value:,}</h1>
        <p>{icon} {label}</p>
    </div>
    """, unsafe_allow_html=True)

def display_navigation_cards():
    """Afficher les cartes de navigation"""
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.markdown("""
        <div class="info-box">
            <h3>⚙️ Admin Examens</h3>
            <p>Génération automatique des emplois du temps et gestion des examens</p>
            <p><strong>👉 Voir page "Admin Examens"</strong></p>
        </div>
        """, unsafe_allow_html=True)
    
    with col2:
        st.markdown("""
        <div class="info-box">
            <h3>👨‍🎓 Espace Étudiant</h3>
            <p>Consultation des examens personnalisés par étudiant</p>
            <p><strong>👉 Voir page "Étudiant"</strong></p>
        </div>
        """, unsafe_allow_html=True)
    
    with col3:
        st.markdown("""
        <div class="info-box">
            <h3>👨‍🏫 Espace Professeur</h3>
            <p>Consultation des surveillances et emplois du temps</p>
            <p><strong>👉 Voir page "Professeur"</strong></p>
        </div>
        """, unsafe_allow_html=True)

# ========================================
# PAGE PRINCIPALE
# ========================================

def main():
    # En-tête
    st.title("🏠 Accueil - Plateforme EDT Examens")
    st.markdown("**Plateforme d'Optimisation des Emplois du Temps d'Examens Universitaires**")
    st.markdown("---")
    
    # Statistiques globales
    stats = get_global_stats()
    
    if stats:
        st.markdown('<p class="section-title">📊 Vue d\'Ensemble Globale</p>', unsafe_allow_html=True)
        
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            display_metric_card(stats['nb_etudiants'], "Étudiants", "👨‍🎓")
        
        with col2:
            display_metric_card(stats['nb_examens'], "Examens Planifiés", "📝")
        
        with col3:
            display_metric_card(stats['nb_profs'], "Professeurs", "👨‍🏫")
        
        with col4:
            display_metric_card(stats['nb_salles'], "Salles Disponibles", "🏫")
        
        st.markdown("")
        
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("🏢 Départements", stats['nb_depts'])
        with col2:
            st.metric("🎓 Formations", stats['nb_formations'])
        with col3:
            st.metric("📚 Modules", stats['nb_modules'])
        with col4:
            st.metric("👥 Groupes", stats['nb_groupes'])
    else:
        st.warning("⚠️ Impossible de charger les statistiques")
    
    st.markdown("---")
    
    # Période du planning
    period = get_planning_period()
    if period and period['debut'] and period['fin']:
        st.markdown('<p class="section-title">📅 Période des Examens</p>', unsafe_allow_html=True)
        
        col1, col2 = st.columns(2)
        with col1:
            st.info(f"**📅 Début:** {period['debut'].strftime('%d/%m/%Y')}")
        with col2:
            st.info(f"**📅 Fin:** {period['fin'].strftime('%d/%m/%Y')}")
        
        st.markdown("---")
    
    # Départements
    st.markdown('<p class="section-title">🏢 Statistiques par Département</p>', unsafe_allow_html=True)
    
    dept_data = get_dept_summary()
    
    if dept_data:
        df_dept = pd.DataFrame(dept_data)
        df_dept.columns = ['Département', 'Formations', 'Étudiants', 'Examens']
        
        st.dataframe(df_dept, use_container_width=True, hide_index=True)
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("**📊 Étudiants par département**")
            chart_etudiants = df_dept.set_index('Département')['Étudiants']
            st.bar_chart(chart_etudiants)
        
        with col2:
            st.markdown("**📝 Examens par département**")
            chart_examens = df_dept.set_index('Département')['Examens']
            st.bar_chart(chart_examens)
    else:
        st.info("Aucune donnée disponible pour les départements")
    
    st.markdown("---")
    
    # Navigation
    st.markdown('<p class="section-title">🧭 Navigation Rapide</p>', unsafe_allow_html=True)
    display_navigation_cards()
    
    # Footer
    st.markdown("---")
    st.caption("📊 Plateforme EDT Examens | Développée pour l'optimisation automatique des plannings universitaires")

if __name__ == "__main__":
    main()