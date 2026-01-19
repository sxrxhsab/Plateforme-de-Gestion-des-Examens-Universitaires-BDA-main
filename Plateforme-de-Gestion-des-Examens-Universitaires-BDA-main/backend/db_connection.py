"""
Module de connexion à la base de données MySQL
"""
import mysql.connector
from mysql.connector import Error
import os
from dotenv import load_dotenv

# Charger les variables d'environnement
load_dotenv()

class DatabaseConnection:
    """Classe pour gérer la connexion à la base de données"""
    
    def __init__(self):
        """Initialiser la connexion"""
        self.connection = None
        self.host = os.getenv('DB_HOST', 'localhost')
        self.port = int(os.getenv('DB_PORT', '3306'))
        self.database = os.getenv('DB_NAME', 'edt_examens')
        self.user = os.getenv('DB_USER', 'root')
        self.password = os.getenv('DB_PASSWORD', '')
    
    def connect(self):
        """Établir la connexion à la base de données"""
        try:
            if self.connection is None or not self.connection.is_connected():
                self.connection = mysql.connector.connect(
                    host=self.host,
                    port=self.port,
                    database=self.database,
                    user=self.user,
                    password=self.password,
                    autocommit=True,
                    consume_results=True  # Important pour éviter "Unread result found"
                )
                if self.connection.is_connected():
                    print(f"✅ Connecté à MySQL: {self.database}")
                    return self.connection
            return self.connection
        except Error as e:
            print(f"❌ Erreur de connexion MySQL: {e}")
            return None
    
    def disconnect(self):
        """Fermer la connexion"""
        if self.connection and self.connection.is_connected():
            self.connection.close()
            print("✅ Connexion MySQL fermée")
    
    def execute_query(self, query, params=None):
        """
        Exécuter une requête SELECT
        
        Args:
            query: Requête SQL
            params: Paramètres de la requête (tuple ou dict)
            
        Returns:
            Liste de dictionnaires avec les résultats
        """
        cursor = None
        try:
            conn = self.connect()
            if conn:
                cursor = conn.cursor(dictionary=True, buffered=True)  # buffered=True pour éviter les problèmes
                
                if params:
                    cursor.execute(query, params)
                else:
                    cursor.execute(query)
                
                # Pour les SELECT
                if query.strip().upper().startswith('SELECT') or query.strip().upper().startswith('DESCRIBE') or query.strip().upper().startswith('SHOW'):
                    result = cursor.fetchall()
                    return result
                else:
                    # Pour INSERT, UPDATE, DELETE
                    conn.commit()
                    return True
            return None
        except Error as e:
            print(f"❌ Erreur lors de l'exécution de la requête: {e}")
            print(f"   Requête: {query[:100]}...")
            return None
        finally:
            if cursor:
                cursor.close()
    
    def execute_many(self, query, data):
        """
        Exécuter une requête avec plusieurs enregistrements
        
        Args:
            query: Requête SQL (INSERT, UPDATE, etc.)
            data: Liste de tuples avec les données
            
        Returns:
            True si succès, False sinon
        """
        cursor = None
        try:
            conn = self.connect()
            if conn:
                cursor = conn.cursor(buffered=True)
                cursor.executemany(query, data)
                conn.commit()
                affected_rows = cursor.rowcount
                return True
            return False
        except Error as e:
            print(f"❌ Erreur lors de l'exécution multiple: {e}")
            print(f"   Requête: {query[:100]}...")
            return False
        finally:
            if cursor:
                cursor.close()
    
    def execute_procedure(self, procedure_name, params=None):
        """
        Exécuter une procédure stockée
        
        Args:
            procedure_name: Nom de la procédure
            params: Paramètres de la procédure (tuple)
            
        Returns:
            Liste de dictionnaires avec les résultats
        """
        cursor = None
        try:
            conn = self.connect()
            if conn:
                cursor = conn.cursor(dictionary=True, buffered=True)
                
                if params:
                    cursor.callproc(procedure_name, params)
                else:
                    cursor.callproc(procedure_name)
                
                # Récupérer les résultats
                results = []
                for result in cursor.stored_results():
                    results.extend(result.fetchall())
                
                return results
            return None
        except Error as e:
            print(f"❌ Erreur lors de l'exécution de la procédure: {e}")
            return None
        finally:
            if cursor:
                cursor.close()
    
    def get_last_insert_id(self):
        """Obtenir le dernier ID inséré"""
        cursor = None
        try:
            conn = self.connect()
            if conn:
                cursor = conn.cursor(buffered=True)
                cursor.execute("SELECT LAST_INSERT_ID() as id")
                result = cursor.fetchone()
                return result[0] if result else None
            return None
        except Error as e:
            print(f"❌ Erreur: {e}")
            return None
        finally:
            if cursor:
                cursor.close()


# Instance globale de la connexion
db = DatabaseConnection()


# Fonctions utilitaires pour simplifier l'utilisation
def get_connection():
    """Obtenir la connexion à la base de données"""
    return db.connect()

def execute_query(query, params=None):
    """Exécuter une requête"""
    return db.execute_query(query, params)

def execute_many(query, data):
    """Exécuter plusieurs insertions"""
    return db.execute_many(query, data)

def execute_procedure(procedure_name, params=None):
    """Exécuter une procédure stockée"""
    return db.execute_procedure(procedure_name, params)


# Test de connexion au chargement du module
if __name__ == "__main__":
    print("=" * 60)
    print("Test de connexion à la base de données")
    print("=" * 60)
    
    conn = db.connect()
    if conn:
        print("\n✅ Connexion réussie!")
        
        # Tester une requête simple
        result = db.execute_query("SELECT DATABASE() as current_db")
        if result:
            print(f"✅ Base de données actuelle: {result[0]['current_db']}")
        
        # Lister les tables
        result = db.execute_query("""
            SELECT table_name 
            FROM information_schema.tables 
            WHERE table_schema = DATABASE()
            ORDER BY table_name
        """)
        
        if result:
            print(f"\n✅ Tables trouvées: {len(result)}")
            for row in result:
                print(f"   - {row['table_name']}")
        
        db.disconnect()
    else:
        print("\n❌ Échec de la connexion!")
        print("\n💡 Vérifiez:")
        print("   1. MySQL est démarré")
        print("   2. Le fichier .env existe et contient les bons identifiants")
        print("   3. La base de données 'edt_examens' existe")
