"""
Générateur de données réalistes pour la base EDT Examens
200 formations EXACTEMENT, 13,000 étudiants, 6-9 modules par formation
Structure spéciale pour département INFO
🔥 AVEC NOMINATION AUTOMATIQUE DE:
   - 7 CHEFS DE DÉPARTEMENT (1 PAR DÉPARTEMENT)
   - 1 VICE-DOYEN (parmi les professeurs)
"""

import mysql.connector
from faker import Faker
import random
from datetime import datetime, timedelta, date

fake = Faker('fr_FR')
Faker.seed(42)
random.seed(42)

# Configuration DB
DB_CONFIG = {
    'host': 'localhost',
    'user': 'root',
    'password': '',  # À MODIFIER
    'database': 'edt_examens'
}

# Constantes
NB_DEPARTEMENTS = 7
NB_FORMATIONS_TOTAL = 200
NB_ETUDIANTS = 13000
NB_PROFESSEURS_PAR_DEPT = 15
NB_SALLES_NORMALES = 80
NB_AMPHIS = 20

# Noms réalistes
DEPARTEMENTS = [
    ('Informatique', 'INFO'),
    ('Mathématiques', 'MATH'),
    ('Physique', 'PHYS'),
    ('Chimie', 'CHIM'),
    ('Biologie', 'BIO'),
    ('Sciences Économiques', 'ECO'),
    ('Lettres et Langues', 'LET')
]

# 🔥 STRUCTURE SPÉCIALE POUR INFO - 8 FORMATIONS
FORMATIONS_INFO = {
    'Licence 1': [('Licence 1 Informatique', None)],
    'Licence 2': [('Licence 2 Informatique', None)],
    'Licence 3': [('Licence 3 Informatique', 'SI')],
    'Master 1': [
        ('Master 1 Informatique', 'AI'),
        ('Master 1 Informatique', 'GL')
    ],
    'Master 2': [
        ('Master 2 Informatique', 'AI'),
        ('Master 2 Informatique', 'GL'),
        ('Master 2 Informatique', 'CS')
    ]
}

# Spécialités autres départements
SPECIALITES_AUTRES = {
    'MATH': ['Mathématiques Appliquées', 'Mathématiques Fondamentales', 'Statistiques', 'Analyse'],
    'PHYS': ['Physique Appliquée', 'Physique Théorique', 'Physique des Matériaux', 'Astrophysique'],
    'CHIM': ['Chimie Organique', 'Chimie Analytique', 'Chimie Industrielle', 'Biochimie'],
    'BIO': ['Biologie Cellulaire', 'Biologie Moléculaire', 'Biotechnologie', 'Écologie'],
    'ECO': ['Économie Appliquée', 'Finance', 'Management', 'Commerce International'],
    'LET': ['Littérature', 'Linguistique', 'Traduction', 'Didactique']
}

MODULES_NAMES = {
    'INFO': ['Algorithmique', 'Base de données', 'Réseaux', 'Intelligence Artificielle', 'Développement Web', 'Sécurité Informatique', 'Systèmes Distribués', 'Cloud Computing', 'DevOps', 'Cybersécurité'],
    'MATH': ['Algèbre Linéaire', 'Analyse Réelle', 'Probabilités', 'Statistiques', 'Géométrie', 'Topologie', 'Équations Différentielles', 'Optimisation', 'Analyse Numérique'],
    'PHYS': ['Mécanique', 'Thermodynamique', 'Électromagnétisme', 'Optique', 'Quantique', 'Physique Statistique', 'Physique Nucléaire', 'Astrophysique', 'Matériaux'],
    'CHIM': ['Chimie Organique', 'Chimie Inorganique', 'Chimie Analytique', 'Biochimie', 'Thermochimie', 'Catalyse', 'Chimie Industrielle', 'Spectroscopie', 'Cristallographie'],
    'BIO': ['Génétique', 'Biologie Cellulaire', 'Écologie', 'Microbiologie', 'Physiologie', 'Biologie Moléculaire', 'Immunologie', 'Biotechnologie', 'Bioinformatique'],
    'ECO': ['Microéconomie', 'Macroéconomie', 'Économétrie', 'Finance', 'Comptabilité', 'Marketing', 'Management', 'Commerce', 'Fiscalité'],
    'LET': ['Littérature', 'Linguistique', 'Phonétique', 'Grammaire', 'Civilisation', 'Traduction', 'Didactique', 'Stylistique', 'Sémantique']
}

BATIMENTS = ['A', 'B', 'C', 'D', 'E']

def get_connection():
    """Connexion à la base de données"""
    return mysql.connector.connect(**DB_CONFIG)

def setup_database_schema(cursor):
    """Vérifier et ajouter les colonnes manquantes + table chefs + colonnes Vice-Doyen"""
    print("🔧 Vérification du schéma de la base...")
    
    try:
        # Colonnes formations
        cursor.execute("""
            SELECT COUNT(*) 
            FROM information_schema.COLUMNS 
            WHERE TABLE_SCHEMA = 'edt_examens' 
            AND TABLE_NAME = 'formations' 
            AND COLUMN_NAME = 'nb_groupes'
        """)
        if cursor.fetchone()[0] == 0:
            cursor.execute("ALTER TABLE formations ADD COLUMN nb_groupes INT DEFAULT 1")
            print("  ✅ Colonne nb_groupes ajoutée")
        
        cursor.execute("""
            SELECT COUNT(*) 
            FROM information_schema.COLUMNS 
            WHERE TABLE_SCHEMA = 'edt_examens' 
            AND TABLE_NAME = 'formations' 
            AND COLUMN_NAME = 'specialite'
        """)
        if cursor.fetchone()[0] == 0:
            cursor.execute("ALTER TABLE formations ADD COLUMN specialite VARCHAR(100) DEFAULT NULL")
            print("  ✅ Colonne specialite ajoutée")
        
        # Colonnes étudiants
        cursor.execute("""
            SELECT COUNT(*) 
            FROM information_schema.COLUMNS 
            WHERE TABLE_SCHEMA = 'edt_examens' 
            AND TABLE_NAME = 'etudiants' 
            AND COLUMN_NAME = 'groupe_id'
        """)
        if cursor.fetchone()[0] == 0:
            cursor.execute("ALTER TABLE etudiants ADD COLUMN groupe_id INT DEFAULT NULL")
            print("  ✅ Colonne groupe_id ajoutée")
        
        # Colonnes pour chefs de département
        cursor.execute("""
            SELECT COUNT(*) 
            FROM information_schema.COLUMNS 
            WHERE TABLE_SCHEMA = 'edt_examens' 
            AND TABLE_NAME = 'professeurs' 
            AND COLUMN_NAME = 'est_chef_dept'
        """)
        if cursor.fetchone()[0] == 0:
            cursor.execute("ALTER TABLE professeurs ADD COLUMN est_chef_dept BOOLEAN DEFAULT FALSE")
            print("  ✅ Colonne est_chef_dept ajoutée")
        
        cursor.execute("""
            SELECT COUNT(*) 
            FROM information_schema.COLUMNS 
            WHERE TABLE_SCHEMA = 'edt_examens' 
            AND TABLE_NAME = 'professeurs' 
            AND COLUMN_NAME = 'date_nomination'
        """)
        if cursor.fetchone()[0] == 0:
            cursor.execute("ALTER TABLE professeurs ADD COLUMN date_nomination DATE DEFAULT NULL")
            print("  ✅ Colonne date_nomination ajoutée")
        
        # 🔥 NOUVEAU: Colonnes pour Vice-Doyen
        cursor.execute("""
            SELECT COUNT(*) 
            FROM information_schema.COLUMNS 
            WHERE TABLE_SCHEMA = 'edt_examens' 
            AND TABLE_NAME = 'professeurs' 
            AND COLUMN_NAME = 'est_vice_doyen'
        """)
        if cursor.fetchone()[0] == 0:
            cursor.execute("ALTER TABLE professeurs ADD COLUMN est_vice_doyen BOOLEAN DEFAULT FALSE")
            print("  ✅ Colonne est_vice_doyen ajoutée")
        
        cursor.execute("""
            SELECT COUNT(*) 
            FROM information_schema.COLUMNS 
            WHERE TABLE_SCHEMA = 'edt_examens' 
            AND TABLE_NAME = 'professeurs' 
            AND COLUMN_NAME = 'date_nomination_vd'
        """)
        if cursor.fetchone()[0] == 0:
            cursor.execute("ALTER TABLE professeurs ADD COLUMN date_nomination_vd DATE DEFAULT NULL")
            print("  ✅ Colonne date_nomination_vd ajoutée")
        
        # Table chefs_departement pour historique
        cursor.execute("SHOW TABLES LIKE 'chefs_departement'")
        if not cursor.fetchone():
            cursor.execute("""
                CREATE TABLE chefs_departement (
                    id INT PRIMARY KEY AUTO_INCREMENT,
                    dept_id INT NOT NULL,
                    prof_id INT NOT NULL,
                    date_debut DATE NOT NULL,
                    date_fin DATE DEFAULT NULL,
                    statut ENUM('actif', 'ancien') DEFAULT 'actif',
                    FOREIGN KEY (dept_id) REFERENCES departements(id) ON DELETE CASCADE,
                    FOREIGN KEY (prof_id) REFERENCES professeurs(id) ON DELETE CASCADE,
                    INDEX idx_dept_actif (dept_id, statut)
                )
            """)
            print("  ✅ Table chefs_departement créée")
        
        # 🔥 NOUVEAU: Table vice_doyens pour historique
        cursor.execute("SHOW TABLES LIKE 'vice_doyens'")
        if not cursor.fetchone():
            cursor.execute("""
                CREATE TABLE vice_doyens (
                    id INT PRIMARY KEY AUTO_INCREMENT,
                    prof_id INT NOT NULL,
                    date_debut DATE NOT NULL,
                    date_fin DATE DEFAULT NULL,
                    statut ENUM('actif', 'ancien') DEFAULT 'actif',
                    FOREIGN KEY (prof_id) REFERENCES professeurs(id) ON DELETE CASCADE,
                    INDEX idx_statut (statut)
                )
            """)
            print("  ✅ Table vice_doyens créée")
        
        print("✅ Schéma vérifié\n")
    except Exception as e:
        print(f"⚠️  Erreur schéma: {e}")

def clear_database(cursor):
    """Vider toutes les tables"""
    print("🧹 Nettoyage de la base de données...")
    tables = [
        'surveillances', 'inscriptions', 'examens', 
        'vice_doyens', 'chefs_departement', 'etudiants', 'groupes', 
        'modules', 'professeurs', 'salles', 
        'formations', 'departements'
    ]
    
    cursor.execute("SET FOREIGN_KEY_CHECKS = 0")
    for table in tables:
        try:
            cursor.execute(f"TRUNCATE TABLE {table}")
            print(f"  ✅ Table {table} vidée")
        except Exception as e:
            print(f"  ⚠️  {table}: {e}")
    cursor.execute("SET FOREIGN_KEY_CHECKS = 1")
    print("✅ Base nettoyée\n")

def generer_matricule():
    """Génère un matricule étudiant unique"""
    annee = random.randint(2020, 2024)
    num = random.randint(1000, 9999)
    return f"{annee}{num}"

def insert_departements(cursor):
    """Insérer les départements"""
    print("📚 Insertion des départements...")
    dept_ids = {}
    for nom, code in DEPARTEMENTS:
        cursor.execute("INSERT INTO departements (nom, code) VALUES (%s, %s)", (nom, code))
        dept_ids[code] = cursor.lastrowid
    print(f"✅ {len(DEPARTEMENTS)} départements créés")
    return dept_ids

def insert_formations(cursor, dept_ids):
    """Insérer 200 formations EXACTEMENT"""
    print("🎓 Insertion des formations...")
    
    formations_data = []
    total_formations = 0
    
    # 1. DÉPARTEMENT INFO
    dept_id_info = dept_ids.get('INFO')
    if dept_id_info:
        for niveau, formations_list in FORMATIONS_INFO.items():
            for nom, specialite in formations_list:
                nb_modules = random.randint(6, 9)
                
                if 'Licence 1' in niveau:
                    nb_groupes = random.randint(10, 15)
                elif 'Licence 2' in niveau:
                    nb_groupes = random.randint(8, 12)
                elif 'Licence 3' in niveau:
                    nb_groupes = random.randint(6, 10)
                elif 'Master 1' in niveau:
                    nb_groupes = random.randint(4, 7)
                else:
                    nb_groupes = random.randint(3, 6)
                
                cursor.execute(
                    "INSERT INTO formations (nom, dept_id, nb_modules, niveau, nb_groupes, specialite) VALUES (%s, %s, %s, %s, %s, %s)",
                    (nom, dept_id_info, nb_modules, niveau, nb_groupes, specialite)
                )
                formations_data.append((cursor.lastrowid, nb_groupes))
                total_formations += 1
        
        print(f"  ✅ INFO : {total_formations} formations créées")
    
    # 2. AUTRES DÉPARTEMENTS
    formations_restantes = NB_FORMATIONS_TOTAL - total_formations
    nb_formations_par_dept = formations_restantes // 6
    
    for code, dept_id in dept_ids.items():
        if code == 'INFO':
            continue
        
        specialites = SPECIALITES_AUTRES.get(code, ['Générale'])
        dept_formations = 0
        
        for _ in range(nb_formations_par_dept):
            niveau = random.choice(['Licence 1', 'Licence 2', 'Licence 3', 'Master 1', 'Master 2'])
            specialite = random.choice(specialites) if niveau in ['Licence 3', 'Master 1', 'Master 2'] else None
            
            if specialite:
                nom = f"{niveau} {code} - {specialite}"
            else:
                nom = f"{niveau} {code}"
            
            nb_modules = random.randint(6, 9)
            
            if 'Licence 1' in niveau:
                nb_groupes = random.randint(8, 12)
            elif 'Licence 2' in niveau:
                nb_groupes = random.randint(6, 10)
            elif 'Licence 3' in niveau:
                nb_groupes = random.randint(4, 8)
            elif 'Master 1' in niveau:
                nb_groupes = random.randint(3, 6)
            else:
                nb_groupes = random.randint(2, 5)
            
            cursor.execute(
                "INSERT INTO formations (nom, dept_id, nb_modules, niveau, nb_groupes, specialite) VALUES (%s, %s, %s, %s, %s, %s)",
                (nom, dept_id, nb_modules, niveau, nb_groupes, specialite)
            )
            formations_data.append((cursor.lastrowid, nb_groupes))
            total_formations += 1
            dept_formations += 1
        
        print(f"  ✅ {code}: {dept_formations} formations créées")
    
    print(f"✅ TOTAL: {total_formations} formations (objectif: {NB_FORMATIONS_TOTAL})\n")
    return formations_data

def insert_groupes(cursor, formations_data):
    """Insérer les groupes"""
    print("👥 Insertion des groupes...")
    groupe_count = 0
    
    for formation_id, nb_groupes in formations_data:
        for num_groupe in range(1, nb_groupes + 1):
            nom_groupe = f"Groupe {num_groupe}"
            capacite = random.randint(20, 30)
            
            cursor.execute(
                "INSERT INTO groupes (formation_id, nom, numero, capacite) VALUES (%s, %s, %s, %s)",
                (formation_id, nom_groupe, num_groupe, capacite)
            )
            groupe_count += 1
    
    print(f"✅ {groupe_count} groupes créés")

def insert_modules(cursor):
    """Insérer les modules"""
    print("📖 Insertion des modules...")
    cursor.execute("""
        SELECT f.id, f.dept_id, f.nb_modules, f.specialite
        FROM formations f 
        JOIN departements d ON f.dept_id = d.id
    """)
    formations = cursor.fetchall()
    
    module_count = 0
    for formation_id, dept_id, nb_modules, specialite in formations:
        cursor.execute("SELECT code FROM departements WHERE id = %s", (dept_id,))
        dept_code = cursor.fetchone()[0]
        
        base_names = MODULES_NAMES.get(dept_code, ['Module'])
        
        for i in range(nb_modules):
            nom = base_names[i % len(base_names)]
            
            if specialite:
                nom = f"{nom} - {specialite}"
            
            code = f"{dept_code}{formation_id:03d}M{i+1:02d}"
            credits = random.choice([4, 5, 6])
            semestre = random.choice([1, 2])
            
            try:
                cursor.execute(
                    "INSERT INTO modules (nom, code, credits, formation_id, semestre) VALUES (%s, %s, %s, %s, %s)",
                    (nom, code, credits, formation_id, semestre)
                )
                module_count += 1
            except:
                pass
    
    print(f"✅ {module_count} modules créés")

def insert_etudiants(cursor):
    """Insérer 13,000 étudiants"""
    print("👨‍🎓 Insertion des étudiants...")
    
    cursor.execute("""
        SELECT g.id, g.formation_id, g.capacite
        FROM groupes g
        ORDER BY RAND()
    """)
    groupes = cursor.fetchall()
    
    matricules_used = set()
    etudiant_count = 0
    
    for groupe_id, formation_id, capacite in groupes:
        if etudiant_count >= NB_ETUDIANTS:
            break
        
        for _ in range(capacite):
            if etudiant_count >= NB_ETUDIANTS:
                break
            
            matricule = generer_matricule()
            while matricule in matricules_used:
                matricule = generer_matricule()
            matricules_used.add(matricule)
            
            nom = fake.last_name()
            prenom = fake.first_name()
            promo = random.randint(2020, 2024)
            email = f"{prenom.lower()}.{nom.lower()}@univ.dz"
            
            cursor.execute(
                "INSERT INTO etudiants (matricule, nom, prenom, formation_id, groupe_id, promo, email) VALUES (%s, %s, %s, %s, %s, %s, %s)",
                (matricule, nom, prenom, formation_id, groupe_id, promo, email)
            )
            etudiant_count += 1
            
            if etudiant_count % 1000 == 0:
                print(f"  ⏳ {etudiant_count}/{NB_ETUDIANTS} étudiants...")
    
    print(f"✅ {etudiant_count} étudiants créés")

def insert_professeurs(cursor, dept_ids):
    """Insérer professeurs ET retourner IDs par département + tous les IDs"""
    print("👨‍🏫 Insertion des professeurs...")
    
    specialites = ['Théorie', 'Pratique', 'Recherche', 'Enseignement']
    prof_count = 0
    profs_by_dept = {}
    all_prof_ids = []
    
    for code, dept_id in dept_ids.items():
        profs_by_dept[dept_id] = []
        
        for _ in range(NB_PROFESSEURS_PAR_DEPT):
            nom = fake.last_name()
            prenom = fake.first_name()
            specialite = random.choice(specialites)
            email = f"{prenom.lower()}.{nom.lower()}@univ-prof.dz"
            
            cursor.execute(
                "INSERT INTO professeurs (nom, prenom, dept_id, specialite, email, est_chef_dept, est_vice_doyen) VALUES (%s, %s, %s, %s, %s, %s, %s)",
                (nom, prenom, dept_id, specialite, email, False, False)
            )
            prof_id = cursor.lastrowid
            profs_by_dept[dept_id].append(prof_id)
            all_prof_ids.append(prof_id)
            prof_count += 1
    
    print(f"✅ {prof_count} professeurs créés")
    return profs_by_dept, all_prof_ids

def nominate_chefs_departement(cursor, dept_ids, profs_by_dept):
    """NOMMER 1 CHEF PAR DÉPARTEMENT"""
    print("\n👔 Nomination des chefs de département...")
    
    today = date.today()
    chefs_nommes = []
    
    for code, dept_id in dept_ids.items():
        prof_ids = profs_by_dept.get(dept_id, [])
        
        if not prof_ids:
            print(f"  ⚠️  Aucun prof pour {code}")
            continue
        
        # Choisir le premier prof comme chef
        chef_prof_id = prof_ids[0]
        
        # Récupérer infos
        cursor.execute(
            "SELECT nom, prenom, email FROM professeurs WHERE id = %s",
            (chef_prof_id,)
        )
        prof_info = cursor.fetchone()
        
        if not prof_info:
            continue
        
        nom, prenom, email = prof_info
        
        # 1. Mettre à jour flag dans professeurs
        cursor.execute(
            "UPDATE professeurs SET est_chef_dept = TRUE, date_nomination = %s WHERE id = %s",
            (today, chef_prof_id)
        )
        
        # 2. Insérer dans chefs_departement
        cursor.execute(
            """INSERT INTO chefs_departement (dept_id, prof_id, date_debut, statut)
               VALUES (%s, %s, %s, 'actif')""",
            (dept_id, chef_prof_id, today)
        )
        
        chefs_nommes.append({
            'dept_code': code,
            'nom': nom,
            'prenom': prenom,
            'email': email
        })
        
        print(f"  ✅ {code:4} : {prenom} {nom} ({email})")
    
    print(f"\n✅ {len(chefs_nommes)} chefs nommés\n")
    return chefs_nommes

def nominate_vice_doyen(cursor, all_prof_ids):
    """🔥 NOMMER 1 VICE-DOYEN parmi TOUS les professeurs"""
    print("\n🎓 Nomination du Vice-Doyen...")
    
    today = date.today()
    
    if not all_prof_ids:
        print("  ⚠️  Aucun professeur disponible")
        return None
    
    # Choisir un professeur aléatoire (qui n'est PAS déjà chef)
    cursor.execute("""
        SELECT id, nom, prenom, email, dept_id
        FROM professeurs
        WHERE est_chef_dept = FALSE
        ORDER BY RAND()
        LIMIT 1
    """)
    
    vice_doyen_info = cursor.fetchone()
    
    if not vice_doyen_info:
        print("  ⚠️  Impossible de trouver un professeur non-chef")
        return None
    
    vd_id, nom, prenom, email, dept_id = vice_doyen_info
    
    # Récupérer le département
    cursor.execute("SELECT code FROM departements WHERE id = %s", (dept_id,))
    dept_code = cursor.fetchone()[0]
    
    # 1. Mettre à jour flag dans professeurs
    cursor.execute(
        "UPDATE professeurs SET est_vice_doyen = TRUE, date_nomination_vd = %s WHERE id = %s",
        (today, vd_id)
    )
    
    # 2. Insérer dans vice_doyens
    cursor.execute(
        """INSERT INTO vice_doyens (prof_id, date_debut, statut)
           VALUES (%s, %s, 'actif')""",
        (vd_id, today)
    )
    
    vice_doyen_data = {
        'id': vd_id,
        'nom': nom,
        'prenom': prenom,
        'email': email,
        'dept_code': dept_code
    }
    
    print(f"  ✅ Vice-Doyen: {prenom} {nom} ({dept_code}) - {email}")
    print(f"✅ 1 Vice-Doyen nommé\n")
    
    return vice_doyen_data

def insert_salles(cursor):
    """Insérer les salles"""
    print("🏫 Insertion des salles...")
    
    # Salles normales : 20 places
    for i in range(NB_SALLES_NORMALES):
        nom = f"Salle {i+1}"
        capacite = 20
        batiment = random.choice(BATIMENTS)
        equipement = random.choice(['Projecteur', 'Ordinateurs', 'Tableau Interactif', 'Basic'])
        
        cursor.execute(
            "INSERT INTO salles (nom, capacite, type, batiment, equipement, disponible) VALUES (%s, %s, %s, %s, %s, %s)",
            (nom, capacite, 'salle', batiment, equipement, 1)
        )
    
    # Amphithéâtres
    capacites_amphis = [50, 100, 150, 200, 250, 300]
    for i in range(NB_AMPHIS):
        nom = f"Amphi {chr(65 + i)}"
        capacite = random.choice(capacites_amphis)
        batiment = random.choice(BATIMENTS)
        equipement = 'Projecteur, Sonorisation, Vidéo'
        
        cursor.execute(
            "INSERT INTO salles (nom, capacite, type, batiment, equipement, disponible) VALUES (%s, %s, %s, %s, %s, %s)",
            (nom, capacite, 'amphi', batiment, equipement, 1)
        )
    
    print(f"✅ {NB_SALLES_NORMALES + NB_AMPHIS} salles créées")

def insert_inscriptions(cursor):
    """Insérer les inscriptions"""
    print("📝 Insertion des inscriptions...")
    
    cursor.execute("SELECT id, formation_id FROM etudiants")
    etudiants = cursor.fetchall()
    
    inscription_count = 0
    for etudiant_id, formation_id in etudiants:
        cursor.execute("SELECT id FROM modules WHERE formation_id = %s", (formation_id,))
        modules = [row[0] for row in cursor.fetchall()]
        
        for module_id in modules:
            try:
                cursor.execute(
                    "INSERT INTO inscriptions (etudiant_id, module_id, annee_academique) VALUES (%s, %s, %s)",
                    (etudiant_id, module_id, '2024-2025')
                )
                inscription_count += 1
            except:
                pass
        
        if inscription_count % 10000 == 0:
            print(f"  ⏳ {inscription_count} inscriptions...")
    
    print(f"✅ {inscription_count} inscriptions créées")

def display_statistics(cursor, chefs_nommes, vice_doyen_data):
    """Afficher statistiques finales"""
    print("\n" + "="*80)
    print("📊 STATISTIQUES FINALES")
    print("="*80)
    
    cursor.execute("SELECT COUNT(*) FROM etudiants")
    print(f"   👨‍🎓 Étudiants: {cursor.fetchone()[0]:,}")
    
    cursor.execute("SELECT COUNT(*) FROM groupes")
    print(f"   👥 Groupes: {cursor.fetchone()[0]}")
    
    cursor.execute("SELECT COUNT(*) FROM inscriptions")
    print(f"   📝 Inscriptions: {cursor.fetchone()[0]:,}")
    
    cursor.execute("SELECT COUNT(*) FROM formations")
    nb_formations = cursor.fetchone()[0]
    print(f"   🎓 Formations: {nb_formations} {'✅' if nb_formations == 200 else '❌'}")
    
    cursor.execute("SELECT COUNT(*) FROM modules")
    print(f"   📖 Modules: {cursor.fetchone()[0]}")
    
    cursor.execute("SELECT COUNT(*) FROM professeurs")
    print(f"   👨‍🏫 Professeurs: {cursor.fetchone()[0]}")
    
    cursor.execute("SELECT COUNT(*) FROM professeurs WHERE est_chef_dept = TRUE")
    print(f"   👔 Chefs de département: {cursor.fetchone()[0]}")
    
    cursor.execute("SELECT COUNT(*) FROM professeurs WHERE est_vice_doyen = TRUE")
    print(f"   🎓 Vice-Doyen: {cursor.fetchone()[0]}")
    
    cursor.execute("SELECT COUNT(*) FROM salles")
    print(f"   🏫 Salles: {cursor.fetchone()[0]}")
    
    print("\n" + "="*80)
    print("👔 LISTE DES CHEFS DE DÉPARTEMENT")
    print("="*80)
    
    for chef in chefs_nommes:
        print(f"   {chef['dept_code']:4} │ {chef['prenom']} {chef['nom']:15} │ {chef['email']}")
    
    print("\n" + "="*80)
    print("🎓 VICE-DOYEN")
    print("="*80)
    
    if vice_doyen_data:
        print(f"   {vice_doyen_data['dept_code']:4} │ {vice_doyen_data['prenom']} {vice_doyen_data['nom']:15} │ {vice_doyen_data['email']}")
    
    print("\n" + "="*80)
    print("💡 IMPORTANT: Utilisez ces emails pour vous connecter!")
    print("   - Chefs de département: accès à leur département")
    print("   - Vice-Doyen: accès à la vue globale de l'université")
    print("="*80 + "\n")

def main():
    """Fonction principale"""
    print("\n" + "="*80)
    print("🚀 GÉNÉRATION COMPLÈTE DE LA BASE DE DONNÉES")
    print("="*80)
    print(f"📊 Objectif : {NB_FORMATIONS_TOTAL} formations, {NB_ETUDIANTS} étudiants")
    print(f"👔 Objectif : {NB_DEPARTEMENTS} chefs de département + 1 Vice-Doyen")
    print("="*80 + "\n")
    
    conn = get_connection()
    cursor = conn.cursor()
    
    try:
        # 1. Setup schéma
        setup_database_schema(cursor)
        conn.commit()
        
        # 2. Nettoyage
        clear_database(cursor)
        conn.commit()
        
        # 3. Départements
        dept_ids = insert_departements(cursor)
        conn.commit()
        
        # 4. Formations
        formations_data = insert_formations(cursor, dept_ids)
        conn.commit()
        
        # 5. Groupes
        insert_groupes(cursor, formations_data)
        conn.commit()
        
        # 6. Modules
        insert_modules(cursor)
        conn.commit()
        
        # 7. Étudiants
        insert_etudiants(cursor)
        conn.commit()
        
        # 8. Professeurs
        profs_by_dept, all_prof_ids = insert_professeurs(cursor, dept_ids)
        conn.commit()
        
        # 9. NOMINATION DES 7 CHEFS
        chefs_nommes = nominate_chefs_departement(cursor, dept_ids, profs_by_dept)
        conn.commit()
        
        # 🔥 10. NOMINATION DU VICE-DOYEN
        vice_doyen_data = nominate_vice_doyen(cursor, all_prof_ids)
        conn.commit()
        
        # 11. Salles
        insert_salles(cursor)
        conn.commit()
        
        # 12. Inscriptions
        insert_inscriptions(cursor)
        conn.commit()
        
        # 13. Statistiques
        display_statistics(cursor, chefs_nommes, vice_doyen_data)
        
        print("✅ GÉNÉRATION TERMINÉE AVEC SUCCÈS!\n")
        print("🔑 Connexions disponibles:")
        print("   - Chefs de département avec leurs emails")
        print("   - Vice-Doyen avec son email\n")
        
    except Exception as e:
        print(f"\n❌ ERREUR: {e}")
        import traceback
        traceback.print_exc()
        conn.rollback()
    finally:
        cursor.close()
        conn.close()

if __name__ == "__main__":
    main()