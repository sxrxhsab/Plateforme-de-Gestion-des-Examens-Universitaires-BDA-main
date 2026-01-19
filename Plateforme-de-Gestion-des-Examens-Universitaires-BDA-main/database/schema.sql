-- Base de données : `edt_examens`
--

DELIMITER $$
--
-- Procédures
--
DROP PROCEDURE IF EXISTS `sp_planning_etudiant`$$
CREATE DEFINER=`root`@`localhost` PROCEDURE `sp_planning_etudiant` (IN `p_etudiant_id` INT)   BEGIN
    SELECT 
        ex.date_heure,
        m.nom AS module,
        m.code AS code_module,
        CONCAT(p.nom, ' ', p.prenom) AS surveillant,
        s.nom AS salle,
        s.batiment,
        ex.duree_minutes,
        DATE_ADD(ex.date_heure, INTERVAL ex.duree_minutes MINUTE) AS heure_fin
    FROM examens ex
    JOIN modules m ON ex.module_id = m.id
    JOIN inscriptions i ON m.id = i.module_id
    JOIN professeurs p ON ex.prof_id = p.id
    JOIN salles s ON ex.salle_id = s.id
    WHERE i.etudiant_id = p_etudiant_id
        AND ex.statut = 'planifie'
    ORDER BY ex.date_heure;
END$$

DROP PROCEDURE IF EXISTS `sp_planning_professeur`$$
CREATE DEFINER=`root`@`localhost` PROCEDURE `sp_planning_professeur` (IN `p_prof_id` INT)   BEGIN
    SELECT 
        ex.date_heure,
        m.nom AS module,
        f.nom AS formation,
        s.nom AS salle,
        ex.nb_etudiants,
        surv.role,
        DATE_ADD(ex.date_heure, INTERVAL ex.duree_minutes MINUTE) AS heure_fin
    FROM surveillances surv
    JOIN examens ex ON surv.examen_id = ex.id
    JOIN modules m ON ex.module_id = m.id
    JOIN formations f ON m.formation_id = f.id
    JOIN salles s ON ex.salle_id = s.id
    WHERE surv.prof_id = p_prof_id
        AND ex.statut IN ('planifie', 'en_cours')
    ORDER BY ex.date_heure;
END$$

DROP PROCEDURE IF EXISTS `sp_salles_disponibles`$$
CREATE DEFINER=`root`@`localhost` PROCEDURE `sp_salles_disponibles` (IN `p_date_heure` DATETIME, IN `p_duree_minutes` INT, IN `p_nb_etudiants` INT)   BEGIN
    SELECT 
        s.id,
        s.nom,
        s.type,
        s.capacite,
        s.batiment,
        s.equipement
    FROM salles s
    WHERE s.capacite >= p_nb_etudiants
        AND s.disponible = TRUE
        AND s.id NOT IN (
            SELECT ex.salle_id
            FROM examens ex
            WHERE (
                (p_date_heure BETWEEN ex.date_heure 
                    AND DATE_ADD(ex.date_heure, INTERVAL ex.duree_minutes MINUTE))
                OR
                (ex.date_heure BETWEEN p_date_heure 
                    AND DATE_ADD(p_date_heure, INTERVAL p_duree_minutes MINUTE))
            )
            AND ex.statut IN ('planifie', 'en_cours')
        )
    ORDER BY 
        CASE 
            WHEN s.type = 'amphi' AND p_nb_etudiants > 50 THEN 1
            WHEN s.type = 'salle' AND p_nb_etudiants <= 30 THEN 1
            ELSE 2
        END,
        s.capacite;
END$$

DELIMITER ;

-- --------------------------------------------------------

--
-- Structure de la table `admin`
--

DROP TABLE IF EXISTS `admin`;
CREATE TABLE IF NOT EXISTS `admin` (
  `id` int NOT NULL AUTO_INCREMENT,
  `username` varchar(50) NOT NULL,
  `password` varchar(255) NOT NULL,
  `date_creation` timestamp NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  UNIQUE KEY `username` (`username`)
) ENGINE=MyISAM AUTO_INCREMENT=2 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

--
-- Déchargement des données de la table `admin`
--

INSERT INTO `admin` (`id`, `username`, `password`, `date_creation`) VALUES
(1, 'admin', '240be518fabd2724ddb6f04eeb1da5967448d7e831c08c8fa822809f74c720a9', '2026-01-10 14:58:16');

-- --------------------------------------------------------

--
-- Structure de la table `chefs_departement`
--

DROP TABLE IF EXISTS `chefs_departement`;
CREATE TABLE IF NOT EXISTS `chefs_departement` (
  `id` int NOT NULL AUTO_INCREMENT,
  `dept_id` int NOT NULL,
  `prof_id` int NOT NULL,
  `date_debut` date NOT NULL,
  `date_fin` date DEFAULT NULL,
  `statut` enum('actif','ancien') DEFAULT 'actif',
  PRIMARY KEY (`id`),
  KEY `prof_id` (`prof_id`),
  KEY `idx_dept_actif` (`dept_id`,`statut`)
) ENGINE=MyISAM AUTO_INCREMENT=8 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;



--
-- Structure de la table `conflits_log`
--

DROP TABLE IF EXISTS `conflits_log`;
CREATE TABLE IF NOT EXISTS `conflits_log` (
  `id` int NOT NULL AUTO_INCREMENT,
  `type_conflit` varchar(100) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL,
  `description` text CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL,
  `examen_id` int DEFAULT NULL,
  `entite_id` int DEFAULT NULL COMMENT 'ID étudiant/prof/salle concerné',
  `severite` enum('critique','important','mineur') CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci DEFAULT 'important',
  `resolu` tinyint(1) DEFAULT '0',
  `date_detection` timestamp NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  KEY `examen_id` (`examen_id`),
  KEY `idx_date` (`date_detection`),
  KEY `idx_resolu` (`resolu`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;



--
-- Structure de la table `contraintes`
--

DROP TABLE IF EXISTS `contraintes`;
CREATE TABLE IF NOT EXISTS `contraintes` (
  `id` int NOT NULL AUTO_INCREMENT,
  `type` enum('etudiant','professeur','salle','generale') CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL,
  `description` text CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL,
  `priorite` int DEFAULT '1' COMMENT '1=critique, 2=importante, 3=souhaitée',
  `active` tinyint(1) DEFAULT '1',
  `created_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=7 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

--


-- Structure de la table `departements`
--

DROP TABLE IF EXISTS `departements`;
CREATE TABLE IF NOT EXISTS `departements` (
  `id` int NOT NULL AUTO_INCREMENT,
  `nom` varchar(100) COLLATE utf8mb4_unicode_ci NOT NULL,
  `code` varchar(10) COLLATE utf8mb4_unicode_ci NOT NULL,
  `created_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  UNIQUE KEY `code` (`code`)
) ENGINE=InnoDB AUTO_INCREMENT=8 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;


--
-- Structure de la table `etudiants`
--

DROP TABLE IF EXISTS `etudiants`;
CREATE TABLE IF NOT EXISTS `etudiants` (
  `id` int NOT NULL AUTO_INCREMENT,
  `matricule` varchar(20) COLLATE utf8mb4_unicode_ci NOT NULL,
  `nom` varchar(100) COLLATE utf8mb4_unicode_ci NOT NULL,
  `prenom` varchar(100) COLLATE utf8mb4_unicode_ci NOT NULL,
  `formation_id` int NOT NULL,
  `promo` int NOT NULL,
  `email` varchar(200) COLLATE utf8mb4_unicode_ci NOT NULL,
  `created_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP,
  `groupe_id` int DEFAULT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `matricule` (`matricule`),
  KEY `idx_formation_id` (`formation_id`),
  KEY `idx_matricule` (`matricule`)
) ENGINE=InnoDB AUTO_INCREMENT=13001 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;


--
-- Structure de la table `formations`
--

DROP TABLE IF EXISTS `formations`;
CREATE TABLE IF NOT EXISTS `formations` (
  `id` int NOT NULL AUTO_INCREMENT,
  `nom` varchar(200) COLLATE utf8mb4_unicode_ci NOT NULL,
  `dept_id` int NOT NULL,
  `nb_modules` int NOT NULL,
  `niveau` varchar(50) COLLATE utf8mb4_unicode_ci NOT NULL,
  `created_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP,
  `specialite` varchar(100) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `nb_groupes` int DEFAULT '1',
  PRIMARY KEY (`id`),
  KEY `idx_dept_id` (`dept_id`)
) ENGINE=InnoDB AUTO_INCREMENT=201 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

--

--
-- Structure de la table `groupes`
--

DROP TABLE IF EXISTS `groupes`;
CREATE TABLE IF NOT EXISTS `groupes` (
  `id` int NOT NULL AUTO_INCREMENT,
  `formation_id` int NOT NULL,
  `nom` varchar(50) NOT NULL,
  `numero` int NOT NULL,
  `capacite` int DEFAULT '20',
  PRIMARY KEY (`id`),
  UNIQUE KEY `formation_id` (`formation_id`,`numero`)
) ENGINE=InnoDB AUTO_INCREMENT=1273 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;




--

DROP TABLE IF EXISTS `inscriptions`;
CREATE TABLE IF NOT EXISTS `inscriptions` (
  `etudiant_id` int NOT NULL,
  `module_id` int NOT NULL,
  `annee_academique` varchar(10) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL COMMENT '2024-2025',
  `note` decimal(5,2) DEFAULT NULL,
  `created_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`etudiant_id`,`module_id`),
  KEY `idx_module` (`module_id`),
  KEY `idx_annee` (`annee_academique`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;



--
-- Structure de la table `logs_systeme`
--

DROP TABLE IF EXISTS `logs_systeme`;
CREATE TABLE IF NOT EXISTS `logs_systeme` (
  `id` int NOT NULL AUTO_INCREMENT,
  `action` varchar(100) NOT NULL,
  `table_name` varchar(100) DEFAULT NULL,
  `record_id` int DEFAULT NULL,
  `details` text,
  `date_action` datetime NOT NULL,
  PRIMARY KEY (`id`),
  KEY `idx_action_date` (`action`,`date_action`),
  KEY `idx_table_record` (`table_name`,`record_id`)
) ENGINE=MyISAM DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- --

--
-- Structure de la table `modules`
--

DROP TABLE IF EXISTS `modules`;
CREATE TABLE IF NOT EXISTS `modules` (
  `id` int NOT NULL AUTO_INCREMENT,
  `nom` varchar(100) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL,
  `code` varchar(20) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL,
  `credits` int NOT NULL DEFAULT '3',
  `formation_id` int NOT NULL,
  `semestre` int DEFAULT NULL COMMENT '1 ou 2',
  `created_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  UNIQUE KEY `unique_module_code` (`formation_id`,`nom`),
  KEY `idx_formation` (`formation_id`)
) ENGINE=InnoDB AUTO_INCREMENT=1515 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;



- Structure de la table `professeurs`
--

DROP TABLE IF EXISTS `professeurs`;
CREATE TABLE IF NOT EXISTS `professeurs` (
  `id` int NOT NULL AUTO_INCREMENT,
  `nom` varchar(100) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL,
  `prenom` varchar(100) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL,
  `dept_id` int NOT NULL,
  `specialite` varchar(100) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `email` varchar(100) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `created_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP,
  `est_chef_dept` tinyint(1) DEFAULT '0',
  `date_nomination` date DEFAULT NULL,
  `est_vice_doyen` tinyint(1) DEFAULT '0',
  `date_nomination_vd` date DEFAULT NULL,
  `password` varchar(255) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  PRIMARY KEY (`id`),
  KEY `idx_dept` (`dept_id`),
  KEY `idx_professeurs_dept_nom` (`dept_id`,`nom`),
  KEY `idx_professeurs_vice_doyen` (`est_vice_doyen`)
) ENGINE=InnoDB AUTO_INCREMENT=106 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;



--
-- Structure de la table `salles`
--

DROP TABLE IF EXISTS `salles`;
CREATE TABLE IF NOT EXISTS `salles` (
  `id` int NOT NULL AUTO_INCREMENT,
  `nom` varchar(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL,
  `capacite` int NOT NULL,
  `type` enum('amphi','salle') CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL,
  `batiment` varchar(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL,
  `equipement` varchar(200) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci DEFAULT NULL COMMENT 'Projecteur, Ordinateurs, etc.',
  `disponible` tinyint(1) DEFAULT '1',
  `created_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  UNIQUE KEY `nom` (`nom`),
  KEY `idx_type` (`type`),
  KEY `idx_capacite` (`capacite`)
) ENGINE=InnoDB AUTO_INCREMENT=101 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;



--
-- Structure de la table `surveillances`
--

DROP TABLE IF EXISTS `surveillances`;
CREATE TABLE IF NOT EXISTS `surveillances` (
  `id` int NOT NULL AUTO_INCREMENT,
  `examen_id` int NOT NULL,
  `prof_id` int NOT NULL,
  `role` enum('principal','assistant') CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci DEFAULT 'assistant',
  `created_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  UNIQUE KEY `unique_surveillance` (`examen_id`,`prof_id`),
  KEY `idx_prof` (`prof_id`),
  KEY `idx_surveillances_prof_date` (`prof_id`,`examen_id`)
) ENGINE=InnoDB AUTO_INCREMENT=12940 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;


--
-- Structure de la table `validations_planning`
--

DROP TABLE IF EXISTS `validations_planning`;
CREATE TABLE IF NOT EXISTS `validations_planning` (
  `id` int NOT NULL AUTO_INCREMENT,
  `dept_id` int NOT NULL,
  `chef_id` int NOT NULL,
  `date_validation` datetime NOT NULL,
  `nb_examens_valides` int NOT NULL,
  `commentaire` text,
  PRIMARY KEY (`id`),
  KEY `idx_dept_date` (`dept_id`,`date_validation`),
  KEY `idx_chef` (`chef_id`)
) ENGINE=MyISAM AUTO_INCREMENT=7 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;


--
-- Structure de la table `vice_doyens`
--

DROP TABLE IF EXISTS `vice_doyens`;
CREATE TABLE IF NOT EXISTS `vice_doyens` (
  `id` int NOT NULL AUTO_INCREMENT,
  `prof_id` int NOT NULL,
  `date_debut` date NOT NULL,
  `date_fin` date DEFAULT NULL,
  `statut` enum('actif','ancien') DEFAULT 'actif',
  PRIMARY KEY (`id`),
  KEY `prof_id` (`prof_id`),
  KEY `idx_statut` (`statut`)
) ENGINE=MyISAM AUTO_INCREMENT=2 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;


-
-- Doublure de structure pour la vue `v_conflits_etudiants`
--
--
DROP VIEW IF EXISTS `v_conflits_etudiants`;
CREATE TABLE IF NOT EXISTS `v_conflits_etudiants` (
`etudiant_id` int
,`etudiant` varchar(201)
,`date_conflit` date
,`modules_conflit` text
,`nb_examens_jour` bigint
);


--
-- Doublure de structure pour la vue `v_conflits_professeurs`
-- (Voir ci-dessous la vue réelle)
--
DROP VIEW IF EXISTS `v_conflits_professeurs`;
CREATE TABLE IF NOT EXISTS `v_conflits_professeurs` (
`professeur_id` int
,`professeur` varchar(201)
,`departement` varchar(100)
,`date_conflit` date
,`nb_surveillances_jour` bigint
,`modules` text
);



-
-- Structure de la table `v_stats_departement`
--

DROP TABLE IF EXISTS `v_stats_departement`;
CREATE TABLE IF NOT EXISTS `v_stats_departement` (
  `dept_id` int DEFAULT NULL,
  `departement` varchar(100) DEFAULT NULL,
  `nb_formations` bigint DEFAULT NULL,
  `nb_modules` bigint DEFAULT NULL,
  `nb_etudiants` bigint DEFAULT NULL,
  `nb_professeurs` bigint DEFAULT NULL,
  `nb_examens_planifies` bigint DEFAULT NULL
) ENGINE=MyISAM DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

