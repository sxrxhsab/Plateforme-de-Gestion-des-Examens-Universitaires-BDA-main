"""
Script de vérification de l'installation - Version adaptée à votre structure
"""
import sys
from pathlib import Path

def check_python_version():
    """Vérifier la version de Python"""
    print("🐍 Vérification de Python...")
    version = sys.version_info
    if version.major >= 3 and version.minor >= 8:
        print(f"✅ Python {version.major}.{version.minor}.{version.micro} - OK")
        return True
    else:
        print(f"❌ Python {version.major}.{version.minor} - Version >= 3.8 requise")
        return False

def check_dependencies():
    """Vérifier les dépendances"""
    print("\n📦 Vérification des dépendances...")
    
    dependencies = {
        'streamlit': 'streamlit',
        'mysql.connector': 'mysql-connector-python',
        'pandas': 'pandas',
        'dotenv': 'python-dotenv'
    }
    
    all_ok = True
    for module, package in dependencies.items():
        try:
            if module == 'mysql.connector':
                __import__('mysql.connector')
            elif module == 'dotenv':
                __import__('dotenv')
            else:
                __import__(module)
            print(f"✅ {package} - Installé")
        except ImportError:
            print(f"❌ {package} - Non installé")
            all_ok = False
    
    return all_ok

def check_database_connection():
    """Vérifier la connexion à la base de données"""
    print("\n🗄️  Vérification de la connexion MySQL...")
    
    try:
        import mysql.connector
        import os
        from dotenv import load_dotenv
        
        # Charger le .env s'il existe
        env_path = Path(__file__).parent / '.env'
        if env_path.exists():
            load_dotenv()
        
        # Paramètres par défaut
        host = os.getenv('DB_HOST', 'localhost')
        port = int(os.getenv('DB_PORT', '3306'))
        database = os.getenv('DB_NAME', 'edt_examens')
        user = os.getenv('DB_USER', 'root')
        password = os.getenv('DB_PASSWORD', '')
        
        print(f"   Tentative de connexion à {user}@{host}:{port}/{database}...")
        
        # Tenter la connexion
        conn = mysql.connector.connect(
            host=host,
            port=port,
            database=database,
            user=user,
            password=password
        )
        
        if conn.is_connected():
            print("✅ Connexion à MySQL - OK")
            
            # Vérifier les tables
            cursor = conn.cursor(dictionary=True)
            cursor.execute("""
                SELECT COUNT(*) as nb_tables 
                FROM information_schema.tables 
                WHERE table_schema = %s
            """, (database,))
            result = cursor.fetchone()
            cursor.close()
            conn.close()
            
            if result and result['nb_tables'] > 0:
                print(f"✅ Base de données '{database}' - {result['nb_tables']} tables trouvées")
                return True
            else:
                print("⚠️  Base de données existe mais aucune table trouvée")
                print("\n   Pour importer les tables:")
                print("   mysql -u root -p edt_examens < database\\create_tables.sql")
                print("   mysql -u root -p edt_examens < database\\indexes.sql")
                return False
        else:
            print("❌ Impossible de se connecter à MySQL")
            return False
            
    except mysql.connector.Error as e:
        print(f"❌ Erreur MySQL: {e}")
        print("\n💡 Solutions possibles:")
        print("   1. Vérifiez que MySQL est démarré")
        print("   2. Créez la base de données:")
        print("      mysql -u root -p -e \"CREATE DATABASE edt_examens\"")
        print("   3. Vérifiez le mot de passe dans le fichier .env")
        return False
    except Exception as e:
        print(f"❌ Erreur: {e}")
        return False

def check_file_structure():
    """Vérifier la structure des fichiers"""
    print("\n📁 Vérification de la structure des fichiers...")
    
    base_path = Path(__file__).parent
    
    # Structure exacte de VOTRE projet
    required_files = {
        # Fichiers racine
        'app.py': base_path / 'app.py',
        'check_installation.py': base_path / 'check_installation.py',
        'generate_fake_data.py': base_path / 'generate_fake_data.py',
        
        # Backend
        'backend/__init__.py': base_path / 'backend' / '__init__.py',
        'backend/db_connection.py': base_path / 'backend' / 'db_connection.py',
        'backend/detect_conflicts.py': base_path / 'backend' / 'detect_conflicts.py',
        'backend/generate_edt.py': base_path / 'backend' / 'generate_edt.py',
        'backend/optimization.py': base_path / 'backend' / 'optimization.py',
        
        # Frontend pages
        'frontend/pages/1_Accueil.py': base_path / 'frontend' / 'pages' / '1_Accueil.py',
        'frontend/pages/2_Admin_Examens.py': base_path / 'frontend' / 'pages' / '2_Admin_Examens.py',
        'frontend/pages/3_Etudiant.py': base_path / 'frontend' / 'pages' / '3_Etudiant.py',
        'frontend/pages/4_Professeur.py': base_path / 'frontend' / 'pages' / '4_Professeur.py',
        'frontend/pages/5_Chef_Departement.py': base_path / 'frontend' / 'pages' / '5_Chef_Departement.py',
        'frontend/pages/6_Vice_Doyen.py': base_path / 'frontend' / 'pages' / '6_Vice_Doyen.py',
        
        # Database
        'database/create_tables.sql': base_path / 'database' / 'create_tables.sql',
        'database/indexes.sql': base_path / 'database' / 'indexes.sql',
        'database/edt_examens.sql': base_path / 'database' / 'edt_examens.sql',
        
        # Dataset
        'dataset/fake_data_generator.py': base_path / 'dataset' / 'fake_data_generator.py'
    }
    
    all_ok = True
    missing_files = []
    
    for name, path in required_files.items():
        if path.exists():
            print(f"✅ {name}")
        else:
            print(f"❌ {name} - Manquant")
            missing_files.append(name)
            all_ok = False
    
    if missing_files:
        print(f"\n⚠️  {len(missing_files)} fichier(s) manquant(s)")
    
    return all_ok

def check_env_file():
    """Vérifier le fichier .env"""
    print("\n⚙️  Vérification du fichier .env...")
    
    env_path = Path(__file__).parent / '.env'
    
    if not env_path.exists():
        print("⚠️  Fichier .env non trouvé")
        print("\n💡 Créez un fichier .env avec ce contenu:")
        print("=" * 50)
        print("DB_HOST=localhost")
        print("DB_PORT=3306")
        print("DB_NAME=edt_examens")
        print("DB_USER=root")
        print("DB_PASSWORD=votre_mot_de_passe_mysql")
        print("=" * 50)
        print("\n   Enregistrez ce fichier comme '.env' (pas .env.txt !)")
        return False
    
    print("✅ Fichier .env existe")
    
    # Vérifier les variables importantes
    try:
        import os
        from dotenv import load_dotenv
        
        load_dotenv()
        
        required_vars = {
            'DB_HOST': os.getenv('DB_HOST'),
            'DB_NAME': os.getenv('DB_NAME'),
            'DB_USER': os.getenv('DB_USER')
        }
        
        missing_vars = []
        for var, value in required_vars.items():
            if not value:
                missing_vars.append(var)
            else:
                print(f"   ✅ {var} = {value}")
        
        if missing_vars:
            print(f"\n⚠️  Variables manquantes: {', '.join(missing_vars)}")
            return False
        else:
            print("✅ Toutes les variables requises sont présentes")
            return True
            
    except Exception as e:
        print(f"⚠️  Impossible de lire .env: {e}")
        return False

def print_next_steps(checks):
    """Afficher les prochaines étapes"""
    print("\n📝 PROCHAINES ÉTAPES:")
    print("=" * 60)
    
    # Si .env manque
    if not checks[3][1]:
        print("\n1️⃣  CRÉER LE FICHIER .env")
        print("   - Ouvrez le Bloc-notes")
        print("   - Copiez:")
        print("     DB_HOST=localhost")
        print("     DB_PORT=3306")
        print("     DB_NAME=edt_examens")
        print("     DB_USER=root")
        print("     DB_PASSWORD=votre_mot_de_passe")
        print("   - Enregistrez comme: .env")
        print("   - IMPORTANT: Pas de .txt à la fin !")
    
    # Si BD a un problème
    if not checks[4][1]:
        print("\n2️⃣  CRÉER LA BASE DE DONNÉES")
        print("   cd C:\\Users\\sabrinalotfi\\Downloads\\exam_edt_optimization")
        print('   mysql -u root -p -e "CREATE DATABASE edt_examens"')
        print("   mysql -u root -p edt_examens < database\\create_tables.sql")
        print("   mysql -u root -p edt_examens < database\\indexes.sql")
    
    # Si tout est OK
    if all(check[1] for check in checks):
        print("\n3️⃣  GÉNÉRER LES DONNÉES DE TEST")
        print("   python generate_fake_data.py")
        print("\n4️⃣  LANCER L'APPLICATION")
        print("   streamlit run app.py")

def main():
    """Fonction principale"""
    print("=" * 60)
    print("🔍 VÉRIFICATION DE L'INSTALLATION")
    print("   Projet: Optimisation EDT Examens")
    print("=" * 60)
    
    checks = [
        ("Python", check_python_version()),
        ("Dépendances", check_dependencies()),
        ("Fichiers", check_file_structure()),
        ("Configuration (.env)", check_env_file()),
        ("Base de données", check_database_connection())
    ]
    
    print("\n" + "=" * 60)
    print("📋 RÉSUMÉ")
    print("=" * 60)
    
    all_ok = True
    for name, result in checks:
        status = "✅ OK" if result else "❌ ERREUR"
        print(f"{name:25} {status}")
        if not result:
            all_ok = False
    
    print("=" * 60)
    
    if all_ok:
        print("\n🎉 INSTALLATION COMPLÈTE ET PRÊTE À L'EMPLOI!")
        print("\n▶️  Pour démarrer l'application:")
        print("   streamlit run app.py")
        print("\n📊 Pour générer des données de test:")
        print("   python generate_fake_data.py")
    else:
        print("\n⚠️  Certains problèmes doivent être résolus")
        print_next_steps(checks)
    
    return all_ok

if __name__ == "__main__":
    try:
        success = main()
        input("\n\nAppuyez sur Entrée pour fermer...")
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n\n❌ Interrompu par l'utilisateur")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Erreur inattendue: {e}")
        import traceback
        traceback.print_exc()
        input("\n\nAppuyez sur Entrée pour fermer...")
        sys.exit(1)