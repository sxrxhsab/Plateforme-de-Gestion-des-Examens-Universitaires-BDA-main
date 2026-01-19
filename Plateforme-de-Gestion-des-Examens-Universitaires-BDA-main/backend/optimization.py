"""
Module d'optimisation des requêtes et des performances
"""
from backend.db_connection import db
from typing import Dict, Any, List

class QueryOptimizer:
    """Classe pour optimiser les performances des requêtes"""
    
    def __init__(self):
        """Initialiser l'optimiseur"""
        pass
    
    def create_indexes(self) -> Dict[str, bool]:
        """
        Créer les index nécessaires pour optimiser les performances
        Returns:
            Dictionnaire des index créés
        """
        indexes = {
            'idx_examens_date_statut': """
                CREATE INDEX IF NOT EXISTS idx_examens_date_statut 
                ON examens(date_heure, statut)
            """,
            'idx_examens_module_statut': """
                CREATE INDEX IF NOT EXISTS idx_examens_module_statut 
                ON examens(module_id, statut)
            """,
            'idx_inscriptions_composite': """
                CREATE INDEX IF NOT EXISTS idx_inscriptions_composite 
                ON inscriptions(etudiant_id, module_id)
            """,
            'idx_surveillances_prof_exam': """
                CREATE INDEX IF NOT EXISTS idx_surveillances_prof_exam 
                ON surveillances(prof_id, examen_id)
            """,
            'idx_modules_formation': """
                CREATE INDEX IF NOT EXISTS idx_modules_formation 
                ON modules(formation_id)
            """,
            'idx_formations_dept': """
                CREATE INDEX IF NOT EXISTS idx_formations_dept 
                ON formations(dept_id)
            """
        }
        
        results = {}
        for index_name, query in indexes.items():
            try:
                db.execute_query(query, fetch=False)
                results[index_name] = True
            except Exception as e:
                print(f"Erreur création index {index_name}: {e}")
                results[index_name] = False
        
        return results
    
    def analyze_query_performance(self, query: str) -> Dict[str, Any]:
        """
        Analyser les performances d'une requête avec EXPLAIN
        Args:
            query: Requête SQL à analyser
        Returns:
            Résultats de l'analyse
        """
        explain_query = f"EXPLAIN {query}"
        
        try:
            result = db.execute_query(explain_query)
            return {
                'success': True,
                'analysis': result
            }
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }
    
    def get_table_statistics(self) -> List[Dict[str, Any]]:
        """
        Obtenir des statistiques sur les tables
        Returns:
            Statistiques des tables
        """
        query = """
        SELECT 
            TABLE_NAME as table_name,
            TABLE_ROWS as row_count,
            ROUND(((DATA_LENGTH + INDEX_LENGTH) / 1024 / 1024), 2) as size_mb,
            ROUND((DATA_LENGTH / 1024 / 1024), 2) as data_mb,
            ROUND((INDEX_LENGTH / 1024 / 1024), 2) as index_mb
        FROM information_schema.TABLES
        WHERE TABLE_SCHEMA = 'edt_examens'
            AND TABLE_TYPE = 'BASE TABLE'
        ORDER BY (DATA_LENGTH + INDEX_LENGTH) DESC
        """
        
        return db.execute_query(query) or []
    
    def get_index_usage(self) -> List[Dict[str, Any]]:
        """
        Obtenir des statistiques sur l'utilisation des index
        Returns:
            Statistiques des index
        """
        query = """
        SELECT 
            TABLE_NAME as table_name,
            INDEX_NAME as index_name,
            NON_UNIQUE as non_unique,
            SEQ_IN_INDEX as sequence,
            COLUMN_NAME as column_name,
            CARDINALITY as cardinality
        FROM information_schema.STATISTICS
        WHERE TABLE_SCHEMA = 'edt_examens'
        ORDER BY TABLE_NAME, INDEX_NAME, SEQ_IN_INDEX
        """
        
        return db.execute_query(query) or []
    
    def optimize_tables(self) -> Dict[str, bool]:
        """
        Optimiser toutes les tables de la base de données
        Returns:
            Résultats de l'optimisation
        """
        tables = [
            'departements', 'formations', 'modules', 'etudiants',
            'professeurs', 'salles', 'inscriptions', 'examens',
            'surveillances', 'conflits_log', 'contraintes'
        ]
        
        results = {}
        for table in tables:
            try:
                query = f"OPTIMIZE TABLE {table}"
                db.execute_query(query, fetch=False)
                results[table] = True
            except Exception as e:
                print(f"Erreur optimisation {table}: {e}")
                results[table] = False
        
        return results
    
    def get_slow_queries_log(self) -> List[Dict[str, Any]]:
        """
        Simuler un log des requêtes lentes
        Returns:
            Log des requêtes potentiellement lentes
        """
        # Identifier les requêtes qui pourraient être lentes
        queries_to_check = [
            {
                'name': 'Conflits étudiants',
                'query': 'SELECT * FROM v_conflits_etudiants',
                'description': 'Détection des étudiants avec plusieurs examens/jour'
            },
            {
                'name': 'Conflits professeurs',
                'query': 'SELECT * FROM v_conflits_professeurs',
                'description': 'Détection des professeurs surchargés'
            },
            {
                'name': 'Planning étudiant',
                'query': 'CALL sp_planning_etudiant(1)',
                'description': 'Récupération du planning d\'un étudiant'
            }
        ]
        
        results = []
        for item in queries_to_check:
            analysis = self.analyze_query_performance(item['query'])
            results.append({
                'name': item['name'],
                'description': item['description'],
                'analysis': analysis
            })
        
        return results
    
    def benchmark_operations(self) -> Dict[str, Any]:
        """
        Benchmarker les opérations principales
        Returns:
            Résultats des benchmarks
        """
        import time
        
        benchmarks = {}
        
        # Test 1: Requête simple
        start = time.time()
        db.execute_query("SELECT COUNT(*) FROM etudiants")
        benchmarks['count_students'] = round((time.time() - start) * 1000, 2)
        
        # Test 2: Requête avec jointures
        start = time.time()
        db.execute_query("""
            SELECT e.*, f.nom, d.nom 
            FROM etudiants e
            JOIN formations f ON e.formation_id = f.id
            JOIN departements d ON f.dept_id = d.id
            LIMIT 100
        """)
        benchmarks['join_query'] = round((time.time() - start) * 1000, 2)
        
        # Test 3: Vue matérialisée
        start = time.time()
        db.execute_query("SELECT * FROM v_stats_departement")
        benchmarks['stats_view'] = round((time.time() - start) * 1000, 2)
        
        # Test 4: Détection de conflits
        start = time.time()
        db.execute_query("SELECT * FROM v_conflits_etudiants LIMIT 10")
        benchmarks['conflict_detection'] = round((time.time() - start) * 1000, 2)
        
        return {
            'benchmarks': benchmarks,
            'total_time': sum(benchmarks.values()),
            'unit': 'milliseconds'
        }
    
    def get_database_info(self) -> Dict[str, Any]:
        """
        Obtenir des informations générales sur la base de données
        Returns:
            Informations sur la BD
        """
        # Taille totale
        size_query = """
        SELECT 
            SUM(DATA_LENGTH + INDEX_LENGTH) / 1024 / 1024 as total_size_mb
        FROM information_schema.TABLES
        WHERE TABLE_SCHEMA = 'edt_examens'
        """
        
        size_result = db.execute_query(size_query)
        total_size = size_result[0]['total_size_mb'] if size_result else 0
        
        # Nombre de tables
        tables_query = """
        SELECT COUNT(*) as count
        FROM information_schema.TABLES
        WHERE TABLE_SCHEMA = 'edt_examens'
            AND TABLE_TYPE = 'BASE TABLE'
        """
        
        tables_result = db.execute_query(tables_query)
        nb_tables = tables_result[0]['count'] if tables_result else 0
        
        # Nombre de vues
        views_query = """
        SELECT COUNT(*) as count
        FROM information_schema.TABLES
        WHERE TABLE_SCHEMA = 'edt_examens'
            AND TABLE_TYPE = 'VIEW'
        """
        
        views_result = db.execute_query(views_query)
        nb_views = views_result[0]['count'] if views_result else 0
        
        # Nombre de procédures
        procs_query = """
        SELECT COUNT(*) as count
        FROM information_schema.ROUTINES
        WHERE ROUTINE_SCHEMA = 'edt_examens'
            AND ROUTINE_TYPE = 'PROCEDURE'
        """
        
        procs_result = db.execute_query(procs_query)
        nb_procs = procs_result[0]['count'] if procs_result else 0
        
        return {
            'total_size_mb': round(total_size, 2),
            'nb_tables': nb_tables,
            'nb_views': nb_views,
            'nb_procedures': nb_procs
        }

# Instance globale
optimizer = QueryOptimizer()