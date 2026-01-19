"""
Package Backend de la plateforme d'optimisation des emplois du temps

Ce package contient tous les modules nécessaires pour :
- La connexion à la base de données
- La détection de conflits
- La génération d'emplois du temps
- L'optimisation des performances

Modules:
    db_connection: Gestion de la connexion MySQL
    detect_conflicts: Détection automatique des conflits
    generate_edt: Génération optimale des emplois du temps
    optimization: Optimisation des requêtes et performances

Usage:
    from backend.db_connection import db
    from backend.detect_conflicts import conflict_detector
    from backend.generate_edt import scheduler
    from backend.optimization import optimizer
"""

__version__ = '1.0.0'
__author__ = 'Projet BDA - Université'
__all__ = [
    'db_connection',
    'detect_conflicts', 
    'generate_edt',
    'optimization'
]

# Import des modules principaux pour faciliter l'accès
try:
    from .db_connection import db, DatabaseConnection
    from .detect_conflicts import conflict_detector, ConflictDetector
    from .generate_edt import scheduler, ExamScheduler
    from .optimization import optimizer, QueryOptimizer
except ImportError as e:
    # Si les imports échouent, on continue sans erreur
    # (utile lors de l'installation initiale)
    pass
