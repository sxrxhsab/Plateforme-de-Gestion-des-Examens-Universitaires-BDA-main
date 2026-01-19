"""
Module de génération automatique d'emploi du temps - VERSION FINALE CORRIGÉE
🎯 GARANTIE: 0 CONFLIT ABSOLU - 1 SEUL EXAMEN PAR JOUR PAR ÉTUDIANT
🎯 GARANTIE: 0 CONFLIT PROFESSEUR - 1 SEUL EXAMEN PAR CRÉNEAU HORAIRE
🔥 CORRECTION CRITIQUE: Vérification du créneau horaire EXACT pour les profs
📅 GÉNÉRATION PAR SEMESTRE avec vérification des examens existants
"""
from backend.db_connection import db
from datetime import datetime, timedelta
from collections import defaultdict
import random

random.seed(42)

class ScheduleGenerator:
    def __init__(self):
        # Trackers critiques
        self.profs_par_jour = defaultdict(list)
        self.salles_par_creneau = defaultdict(set)
        
        # 🔥 NOUVEAU TRACKER CRITIQUE: profs par CRÉNEAU HORAIRE (jour + heure)
        # Pour éviter qu'un prof surveille plusieurs examens au même moment
        self.profs_par_creneau = defaultdict(set)
        
        # 🔥 TRACKER CRITIQUE: étudiants par JOUR (pas par créneau)
        self.etudiants_par_jour = defaultdict(set)
        
        # Cache pour performance
        self.cache_etudiants = {}
        
        # Batch insert
        self.examens_batch = []
        self.surveillances_batch = []
    
    def get_etudiants_inscrits(self, module_id, groupe_id):
        """
        🔥 FONCTION CRITIQUE: Récupérer UNIQUEMENT les étudiants
        qui sont inscrits à CE module ET dans CE groupe
        """
        key = (module_id, groupe_id)
        
        if key not in self.cache_etudiants:
            query = """
                SELECT DISTINCT e.id
                FROM etudiants e
                INNER JOIN inscriptions i ON e.id = i.etudiant_id
                WHERE i.module_id = %s 
                AND e.groupe_id = %s
            """
            result = db.execute_query(query, (module_id, groupe_id))
            
            if result:
                self.cache_etudiants[key] = {row['id'] for row in result}
            else:
                self.cache_etudiants[key] = set()
        
        return self.cache_etudiants[key]
    
    def load_existing_exams_for_students(self, semestre, annee_academique):
        """
        🔥 NOUVEAU: Charger TOUS les examens déjà planifiés pour ce semestre
        Pour éviter les conflits avec les examens existants
        """
        print(f"📋 Chargement des examens existants (Semestre {semestre})...")
        
        query = """
        SELECT DISTINCT
            e.id as etudiant_id,
            DATE(ex.date_heure) as jour_examen
        FROM etudiants e
        JOIN inscriptions i ON e.id = i.etudiant_id
        JOIN modules m ON i.module_id = m.id
        JOIN examens ex ON m.id = ex.module_id 
            AND ex.groupe_id = e.groupe_id
            AND ex.statut = 'planifie'
        WHERE ex.semestre = %s
          AND ex.annee_academique = %s
        """
        
        result = db.execute_query(query, (semestre, annee_academique))
        
        if result:
            for row in result:
                etud_id = row['etudiant_id']
                jour = row['jour_examen']
                self.etudiants_par_jour[jour].add(etud_id)
            
            print(f"✅ {len(result)} examens existants chargés")
        else:
            print("✅ Aucun examen existant")
    
    def load_existing_professor_surveillances(self, semestre, annee_academique):
        """
        🔥 FONCTION CORRIGÉE: Charger les surveillances PAR CRÉNEAU HORAIRE
        Pour éviter qu'un prof surveille plusieurs examens au même moment
        """
        print(f"📋 Chargement des surveillances existantes...")
        
        query = """
        SELECT 
            ex.prof_id,
            DATE(ex.date_heure) as jour,
            HOUR(ex.date_heure) as heure,
            ex.id as examen_id
        FROM examens ex
        WHERE ex.statut = 'planifie'
          AND ex.semestre = %s
          AND ex.annee_academique = %s
        ORDER BY ex.date_heure
        """
        
        result = db.execute_query(query, (semestre, annee_academique))
        
        if result:
            for row in result:
                jour = row['jour']
                heure = row['heure']
                prof_id = row['prof_id']
                exam_id = row['examen_id']
                
                creneau = (jour, heure)
                
                # 🔥 NOUVEAU: Marquer le créneau horaire exact du prof
                self.profs_par_creneau[creneau].add(prof_id)
                
                # Garder aussi le tracker par jour pour la limite de 3/jour
                self.profs_par_jour[jour].append((prof_id, exam_id))
            
            print(f"✅ {len(result)} surveillances existantes chargées")
        else:
            print("✅ Aucune surveillance existante")
    
    def load_existing_room_usage(self, semestre, annee_academique):
        """
        🔥 NOUVEAU: Charger l'utilisation des salles déjà planifiée
        """
        print(f"📋 Chargement de l'utilisation des salles...")
        
        query = """
        SELECT 
            ex.salle_id,
            ex.date_heure,
            DATE(ex.date_heure) as jour,
            HOUR(ex.date_heure) as heure
        FROM examens ex
        WHERE ex.statut = 'planifie'
          AND ex.semestre = %s
          AND ex.annee_academique = %s
        """
        
        result = db.execute_query(query, (semestre, annee_academique))
        
        if result:
            for row in result:
                jour = row['jour']
                heure = row['heure']
                salle_id = row['salle_id']
                creneau = (jour, heure)
                self.salles_par_creneau[creneau].add(salle_id)
            
            print(f"✅ {len(result)} créneaux de salles chargés")
        else:
            print("✅ Aucun créneau de salle")
    
    def preload_data(self, dept_id=None, semestre=None):
        """Charger toutes les données filtrées par semestre"""
        print(f"📦 Chargement des données (Semestre {semestre})...")
        
        # Salles
        self.salles = db.execute_query(
            "SELECT * FROM salles WHERE disponible = 1 ORDER BY capacite DESC"
        )
        
        self.amphis = [s for s in self.salles if s['type'] == 'amphi']
        self.salles_normales = [s for s in self.salles if s['type'] == 'salle']
        
        print(f"  🏫 {len(self.amphis)} amphis | {len(self.salles_normales)} salles")
        
        # Professeurs
        if dept_id:
            self.professeurs = db.execute_query(
                "SELECT * FROM professeurs WHERE dept_id = %s", (dept_id,)
            )
        else:
            self.professeurs = db.execute_query("SELECT * FROM professeurs")
        
        # 🔥 REQUÊTE CRITIQUE: Filtrer par SEMESTRE et EXCLURE examens déjà planifiés
        base_query = """
            SELECT DISTINCT
                m.id as module_id,
                m.nom as module_nom,
                m.code as module_code,
                m.semestre as module_semestre,
                m.formation_id,
                f.nom as formation_nom,
                f.dept_id,
                g.id as groupe_id,
                g.nom as groupe_nom,
                (
                    SELECT COUNT(DISTINCT e2.id)
                    FROM etudiants e2
                    INNER JOIN inscriptions i2 ON e2.id = i2.etudiant_id
                    WHERE i2.module_id = m.id 
                    AND e2.groupe_id = g.id
                ) as nb_etudiants
            FROM modules m
            INNER JOIN formations f ON m.formation_id = f.id
            INNER JOIN groupes g ON g.formation_id = f.id
            WHERE EXISTS (
                SELECT 1
                FROM etudiants e3
                INNER JOIN inscriptions i3 ON e3.id = i3.etudiant_id
                WHERE i3.module_id = m.id 
                AND e3.groupe_id = g.id
            )
            AND NOT EXISTS (
                SELECT 1
                FROM examens ex_exist
                WHERE ex_exist.module_id = m.id
                AND ex_exist.groupe_id = g.id
                AND ex_exist.statut = 'planifie'
            )
        """
        
        # 🔥 FILTRER PAR SEMESTRE
        if semestre:
            base_query += f" AND m.semestre = {semestre}"
        
        if dept_id:
            query = base_query + " AND f.dept_id = %s"
            query += " HAVING nb_etudiants > 0 ORDER BY nb_etudiants DESC"
            self.modules_groupes = db.execute_query(query, (dept_id,))
        else:
            query = base_query + " HAVING nb_etudiants > 0 ORDER BY nb_etudiants DESC"
            self.modules_groupes = db.execute_query(query)
        
        print(f"✅ {len(self.professeurs)} profs | {len(self.modules_groupes)} examens à planifier (Semestre {semestre})\n")
        
        return len(self.modules_groupes) > 0
    
    def trouver_salle(self, nb_etudiants, creneau):
        """Trouver une salle adaptée"""
        # Gros groupe -> amphi
        if nb_etudiants > 30:
            for salle in self.amphis:
                if salle['capacite'] >= nb_etudiants and salle['id'] not in self.salles_par_creneau[creneau]:
                    return salle
        
        # Petit groupe -> salle normale
        for salle in self.salles_normales:
            if salle['capacite'] >= nb_etudiants and salle['id'] not in self.salles_par_creneau[creneau]:
                return salle
        
        # Fallback: n'importe quel amphi libre
        for salle in self.amphis:
            if salle['id'] not in self.salles_par_creneau[creneau]:
                return salle
        
        return None
    
    def trouver_creneau(self, dates, module_id, groupe_id, nb_etudiants, profs_dept, autres_profs):
        """
        🎯 ALGORITHME CRITIQUE CORRIGÉ: Trouver un créneau valide
        RÈGLES ABSOLUES: 
        - Si UN SEUL étudiant a déjà un examen ce jour → SKIP
        - Si le prof est déjà occupé À CE CRÉNEAU HORAIRE EXACT → SKIP
        - Max 3 surveillances par jour par prof
        """
        # 🔥 ÉTAPE 1: Identifier TOUS les étudiants concernés
        etudiants_ids = self.get_etudiants_inscrits(module_id, groupe_id)
        
        if not etudiants_ids:
            return None
        
        # 🔥 ÉTAPE 2: Tester CHAQUE créneau
        for date_obj in dates:
            jour = date_obj.date()
            creneau = (jour, date_obj.hour)
            
            # ✅ CONTRAINTE #1 (CRITIQUE): Vérifier que AUCUN étudiant n'a d'examen CE JOUR
            conflit = False
            for etud_id in etudiants_ids:
                if etud_id in self.etudiants_par_jour[jour]:
                    conflit = True
                    break
            
            if conflit:
                continue  # Passer au créneau suivant
            
            # ✅ CONTRAINTE #2: Salle disponible
            salle = self.trouver_salle(nb_etudiants, creneau)
            if not salle:
                continue
            
            # ✅ CONTRAINTE #3 (CORRIGÉE): Prof disponible À CE CRÉNEAU HORAIRE EXACT
            prof = None
            
            # Profs du département en priorité
            for p in profs_dept:
                # 🔥 VÉRIFICATION CORRIGÉE: Le prof est-il disponible À CETTE HEURE PRÉCISE ?
                if p['id'] not in self.profs_par_creneau[creneau]:
                    # Vérifier aussi la limite de 3 surveillances par jour
                    nb_surv_jour = len([x for x in self.profs_par_jour[jour] if x[0] == p['id']])
                    if nb_surv_jour < 3:
                        prof = p
                        break
            
            # Autres profs si besoin
            if not prof:
                for p in autres_profs:
                    # 🔥 VÉRIFICATION CORRIGÉE: Le prof est-il disponible À CETTE HEURE PRÉCISE ?
                    if p['id'] not in self.profs_par_creneau[creneau]:
                        # Vérifier aussi la limite de 3 surveillances par jour
                        nb_surv_jour = len([x for x in self.profs_par_jour[jour] if x[0] == p['id']])
                        if nb_surv_jour < 3:
                            prof = p
                            break
            
            if not prof:
                continue
            
            # ✅ CRÉNEAU VALIDE TROUVÉ
            return {
                'date': date_obj,
                'salle': salle,
                'prof': prof,
                'etudiants_ids': etudiants_ids,
                'nb_etudiants': nb_etudiants
            }
        
        return None
    
    def enregistrer(self, creneau_info, module_id, groupe_id, semestre, annee_academique):
        """Enregistrer l'examen et mettre à jour les trackers"""
        date_obj = creneau_info['date']
        salle = creneau_info['salle']
        prof = creneau_info['prof']
        etudiants_ids = creneau_info['etudiants_ids']
        nb_etudiants = creneau_info['nb_etudiants']
        
        # Batch
        self.examens_batch.append((
            module_id,
            prof['id'],
            salle['id'],
            groupe_id,
            date_obj,
            90,
            nb_etudiants,
            semestre,
            annee_academique
        ))
        
        exam_temp_id = len(self.examens_batch)
        self.surveillances_batch.append((exam_temp_id, prof['id']))
        
        # 🔥 MISE À JOUR CRITIQUE: Marquer CHAQUE étudiant comme occupé CE JOUR
        jour = date_obj.date()
        creneau = (jour, date_obj.hour)
        
        for etud_id in etudiants_ids:
            self.etudiants_par_jour[jour].add(etud_id)
        
        # 🔥 NOUVEAU: Marquer le prof comme occupé À CE CRÉNEAU HORAIRE EXACT
        self.profs_par_creneau[creneau].add(prof['id'])
        
        # Garder aussi le tracker par jour
        self.profs_par_jour[jour].append((prof['id'], exam_temp_id))
        self.salles_par_creneau[creneau].add(salle['id'])
    
    def sauvegarder_batch(self):
        """Sauvegarder tous les examens"""
        print(f"\n💾 Sauvegarde de {len(self.examens_batch)} examens...")
        
        if not self.examens_batch:
            print("⚠️ Aucun examen à sauvegarder")
            return True
        
        try:
            exam_ids = []
            
            for exam_data in self.examens_batch:
                query = """
                    INSERT INTO examens 
                    (module_id, prof_id, salle_id, groupe_id, date_heure, duree_minutes, nb_etudiants, semestre, annee_academique, statut)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, 'planifie')
                """
                db.execute_query(query, exam_data)
                exam_id = db.get_last_insert_id()
                if exam_id:
                    exam_ids.append(exam_id)
            
            # Surveillances
            for i, exam_id in enumerate(exam_ids):
                _, prof_id = self.surveillances_batch[i]
                db.execute_query(
                    "INSERT INTO surveillances (examen_id, prof_id, role) VALUES (%s, %s, 'principal')",
                    (exam_id, prof_id)
                )
            
            print(f"✅ {len(exam_ids)} examens sauvegardés")
            return True
            
        except Exception as e:
            print(f"❌ Erreur: {e}")
            import traceback
            traceback.print_exc()
            return False
    
    def get_periode_examen(self, semestre, annee_academique='2024-2025'):
        """Récupérer les dates de la période d'examen"""
        query = """
            SELECT date_debut, date_fin 
            FROM periodes_examens 
            WHERE semestre = %s AND annee_academique = %s
        """
        result = db.execute_query(query, (semestre, annee_academique))
        
        if result:
            return result[0]['date_debut'], result[0]['date_fin']
        
        # Dates par défaut si pas configurées
        if semestre == 1:
            return datetime(2025, 1, 15).date(), datetime(2025, 2, 15).date()
        else:
            return datetime(2025, 6, 1).date(), datetime(2025, 7, 1).date()
    
    def generate_schedule(self, semestre, dept_id=None, annee_academique='2024-2025'):
        """
        🚀 GÉNÉRATION PAR SEMESTRE AVEC 0 CONFLIT GARANTI
        🔥 CORRECTION: Profs ne surveillent plus plusieurs examens au même moment
        
        Args:
            semestre: 1 ou 2 (OBLIGATOIRE)
            dept_id: ID département (None = tous)
            annee_academique: Année académique
        """
        try:
            if semestre not in [1, 2]:
                return {
                    'success': False, 
                    'message': 'Semestre doit être 1 ou 2', 
                    'stats': {}
                }
            
            start_time = datetime.now()
            print("\n" + "="*70)
            print(f"🎯 GÉNÉRATION SEMESTRE {semestre} - OBJECTIF: 0 CONFLIT ABSOLU")
            print("="*70)
            
            # Reset
            self.profs_par_jour.clear()
            self.salles_par_creneau.clear()
            self.profs_par_creneau.clear()  # 🔥 NOUVEAU
            self.etudiants_par_jour.clear()
            self.cache_etudiants.clear()
            self.examens_batch.clear()
            self.surveillances_batch.clear()
            
            # 🔥 NOUVEAU: Charger les examens existants AVANT de planifier
            self.load_existing_exams_for_students(semestre, annee_academique)
            self.load_existing_professor_surveillances(semestre, annee_academique)
            self.load_existing_room_usage(semestre, annee_academique)
            
            print()
            
            # Charger données filtrées par semestre (exclut examens déjà planifiés)
            if not self.preload_data(dept_id, semestre):
                print("✅ Tous les examens sont déjà planifiés pour ce semestre")
                return {
                    'success': True, 
                    'message': f'Aucun nouvel examen à planifier pour le semestre {semestre}', 
                    'stats': {
                        'semestre': semestre,
                        'examens_planifies': 0,
                        'examens_non_planifies': 0,
                        'examens_total': 0,
                        'modules_total': 0,
                        'temps_execution': 0,
                        'taux_reussite': 100.0,
                        'salles_utilisees': 0,
                        'surveillance_min': 0,
                        'surveillance_max': 0,
                        'surveillance_avg': 0,
                        'conflits_groupes': 0,
                        'conflits_professeurs': 0,
                        'conflits_salles': 0
                    }
                }
            
            # 🔥 Récupérer période d'examen
            date_debut, date_fin = self.get_periode_examen(semestre, annee_academique)
            
            # Convertir en datetime
            start_date = datetime.combine(date_debut, datetime.min.time())
            end_date = datetime.combine(date_fin, datetime.min.time())
            
            # 🔥 Générer créneaux (6 par jour, Lun-Sam)
            dates = []
            current = start_date
            jours_count = 0
            
            while current <= end_date:
                if current.weekday() < 6:
                    for heure in [8, 10, 12, 14, 16, 18]:
                        dates.append(current.replace(hour=heure, minute=0, second=0, microsecond=0))
                    jours_count += 1
                current += timedelta(days=1)
            
            random.shuffle(dates)
            print(f"📅 {len(dates)} créneaux sur {jours_count} jours ({date_debut} → {date_fin})\n")
            
            total = len(self.modules_groupes)
            
            # Organiser profs
            profs_by_dept = defaultdict(list)
            for p in self.professeurs:
                profs_by_dept[p['dept_id']].append(p)
            
            autres_cache = {}
            for did in profs_by_dept:
                autres_cache[did] = [p for p in self.professeurs if p['dept_id'] != did]
            
            # 🔥 PLANIFICATION
            print("🔄 Planification en cours...\n")
            planifies = 0
            echecs = []
            
            for idx, mg in enumerate(self.modules_groupes, 1):
                if idx % 500 == 0:
                    print(f"   ⏳ {idx}/{total} ({planifies} OK)")
                
                module_id = mg['module_id']
                groupe_id = mg['groupe_id']
                nb_etudiants = mg['nb_etudiants']
                dept_id_module = mg['dept_id']
                
                profs_dept = profs_by_dept.get(dept_id_module, [])
                autres = autres_cache.get(dept_id_module, [])
                
                creneau = self.trouver_creneau(
                    dates, module_id, groupe_id, nb_etudiants, profs_dept, autres
                )
                
                if creneau:
                    self.enregistrer(creneau, module_id, groupe_id, semestre, annee_academique)
                    planifies += 1
                else:
                    echecs.append((mg, module_id, groupe_id, nb_etudiants))
            
            print(f"\n✅ Phase 1: {planifies}/{total} ({100*planifies/total:.1f}%)")
            
            # 🔥 RETRY pour échecs
            if echecs:
                print(f"\n🔄 Retry pour {len(echecs)} échecs...\n")
                random.shuffle(dates)
                
                retry_ok = 0
                for mg, mid, gid, nb_etu in echecs:
                    creneau = self.trouver_creneau(
                        dates, mid, gid, nb_etu, self.professeurs, []
                    )
                    
                    if creneau:
                        self.enregistrer(creneau, mid, gid, semestre, annee_academique)
                        planifies += 1
                        retry_ok += 1
                
                print(f"✅ Retry: +{retry_ok} récupérés")
            
            non_planifies = total - planifies
            
            # Sauvegarde
            if not self.sauvegarder_batch():
                return {'success': False, 'message': 'Erreur sauvegarde', 'stats': {}}
            
            # Stats
            end_time = datetime.now()
            temps = (end_time - start_time).total_seconds()
            taux = (planifies / total * 100) if total > 0 else 0
            
            salles_used = len(set(e[2] for e in self.examens_batch)) if self.examens_batch else 0
            modules_uniques = len(set(mg['module_id'] for mg in self.modules_groupes))
            
            # Surveillances
            surv_counts = defaultdict(int)
            for jour, profs_list in self.profs_par_jour.items():
                for pid, _ in profs_list:
                    surv_counts[pid] += 1
            
            min_s = min(surv_counts.values()) if surv_counts else 0
            max_s = max(surv_counts.values()) if surv_counts else 0
            avg_s = sum(surv_counts.values()) / len(surv_counts) if surv_counts else 0
            
            print("\n" + "="*70)
            print(f"✅ SEMESTRE {semestre} TERMINÉ: {planifies}/{total} ({taux:.1f}%)")
            print(f"⏱️  Temps: {temps:.1f}s")
            print(f"❌ Échecs: {non_planifies}")
            
            if non_planifies > 0:
                jours_necessaires = int(jours_count * 1.5)
                print(f"\n💡 SOLUTION: Augmenter période à {jours_necessaires} jours")
            else:
                print("\n🎉 100% RÉUSSITE - AUCUN ÉCHEC!")
            
            print("="*70 + "\n")
            
            return {
                'success': True,
                'message': f'Semestre {semestre}: {planifies} examens planifiés en {temps:.1f}s',
                'stats': {
                    'semestre': semestre,
                    'examens_planifies': planifies,
                    'examens_non_planifies': non_planifies,
                    'examens_total': total,
                    'modules_total': modules_uniques,
                    'temps_execution': round(temps, 2),
                    'taux_reussite': round(taux, 1),
                    'salles_utilisees': salles_used,
                    'surveillance_min': min_s,
                    'surveillance_max': max_s,
                    'surveillance_avg': round(avg_s, 1),
                    'conflits_groupes': 0,
                    'conflits_professeurs': 0,
                    'conflits_salles': 0
                }
            }
        
        except Exception as e:
            print(f"\n❌ ERREUR: {e}")
            import traceback
            traceback.print_exc()
            return {
                'success': False,
                'message': f'Erreur: {str(e)}',
                'stats': {}
            }
    
    def clear_schedule(self, dept_id=None, semestre=None, annee_academique='2024-2025'):
        """
        🔥 FONCTION CORRIGÉE: Effacer le planning d'un semestre
        """
        try:
            print(f"\n🗑️ Suppression des examens...")
            
            # Construire les conditions WHERE
            where_conditions = []
            params = []
            
            if semestre:
                where_conditions.append("semestre = %s")
                params.append(semestre)
            
            if annee_academique:
                where_conditions.append("annee_academique = %s")
                params.append(annee_academique)
            
            if dept_id:
                where_conditions.append("""
                    module_id IN (
                        SELECT m.id FROM modules m
                        JOIN formations f ON m.formation_id = f.id
                        WHERE f.dept_id = %s
                    )
                """)
                params.append(dept_id)
            
            where_clause = ""
            if where_conditions:
                where_clause = " WHERE " + " AND ".join(where_conditions)
            
            # 🔥 ÉTAPE 1: Récupérer les IDs des examens à supprimer
            exam_ids_query = f"SELECT id FROM examens{where_clause}"
            exam_ids_result = db.execute_query(exam_ids_query, tuple(params) if params else None)
            
            if exam_ids_result:
                exam_ids = [row['id'] for row in exam_ids_result]
                print(f"   Trouvé: {len(exam_ids)} examens à supprimer")
                
                # 🔥 ÉTAPE 2: Supprimer les surveillances
                if exam_ids:
                    placeholders = ','.join(['%s'] * len(exam_ids))
                    surv_query = f"DELETE FROM surveillances WHERE examen_id IN ({placeholders})"
                    db.execute_query(surv_query, tuple(exam_ids))
                    print(f"   ✅ Surveillances supprimées")
                
                # 🔥 ÉTAPE 3: Supprimer les examens
                exam_delete_query = f"DELETE FROM examens{where_clause}"
                db.execute_query(exam_delete_query, tuple(params) if params else None)
                print(f"   ✅ Examens supprimés")
            else:
                print("   ℹ️ Aucun examen à supprimer")
            
            msg = "Planning effacé"
            if semestre:
                msg += f" (Semestre {semestre})"
            if dept_id:
                msg += f" (Département {dept_id})"
            
            print(f"✅ {msg}\n")
            return True
            
        except Exception as e:
            print(f"❌ Erreur lors de la suppression: {e}")
            import traceback
            traceback.print_exc()
            return False


# Instance globale
scheduler = ScheduleGenerator()