-- phpMyAdmin SQL Dump
-- version 5.2.0
-- https://www.phpmyadmin.net/
--
-- Hôte : 127.0.0.1
-- Généré le : lun. 30 déc. 2024 à 19:38
-- Version du serveur : 10.4.27-MariaDB
-- Version de PHP : 7.4.33

SET SQL_MODE = "NO_AUTO_VALUE_ON_ZERO";
START TRANSACTION;
SET time_zone = "+00:00";


/*!40101 SET @OLD_CHARACTER_SET_CLIENT=@@CHARACTER_SET_CLIENT */;
/*!40101 SET @OLD_CHARACTER_SET_RESULTS=@@CHARACTER_SET_RESULTS */;
/*!40101 SET @OLD_COLLATION_CONNECTION=@@COLLATION_CONNECTION */;
/*!40101 SET NAMES utf8mb4 */;

--
-- Base de données : `urbangymtest`
--

-- --------------------------------------------------------

--
-- Structure de la table `break`
--

CREATE TABLE `break` (
  `Id` int(11) NOT NULL,
  `duration` varchar(255) NOT NULL,
  `VidPath` varchar(255) NOT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

--
-- Déchargement des données de la table `break`
--

INSERT INTO `break` (`Id`, `duration`, `VidPath`) VALUES
(1, '5 minute(s)', 'video1.mp4');

-- --------------------------------------------------------

--
-- Structure de la table `category`
--

CREATE TABLE `category` (
  `Id` int(11) NOT NULL,
  `name` varchar(255) NOT NULL,
  `numberOfInstances` int(11) NOT NULL,
  `icone_Path` varchar(255) NOT NULL,
  `icone_Path_female` varchar(255) NOT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

--
-- Déchargement des données de la table `category`
--

INSERT INTO `category` (`Id`, `name`, `numberOfInstances`, `icone_Path`, `icone_Path_female`) VALUES
(1, 'test', 2, 'R.jpg', 'girl.jpg'),
(3, 'poitrine', 2, 'Video2.png', 'female_poitrine.png');

-- --------------------------------------------------------

--
-- Structure de la table `exercices`
--

CREATE TABLE `exercices` (
  `code` varchar(255) NOT NULL,
  `name` text NOT NULL,
  `category_id` int(11) NOT NULL,
  `description` text NOT NULL,
  `videoPath` text NOT NULL,
  `videoPath_female` text NOT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

--
-- Déchargement des données de la table `exercices`
--

INSERT INTO `exercices` (`code`, `name`, `category_id`, `description`, `videoPath`, `videoPath_female`) VALUES
('PO_E_2', 'exercice2', 3, 'test 2 test', 'Video1.mp4', ''),
('TE_A_3', 'ccccc', 3, 'nuuh', 'Gender_reveal_party.mp4', 'Gender_reveal_party.mp4'),
('TE_N_2', 'Network', 1, 'Network cable shit', 'vid3.mp4', ''),
('TE_T_2', 'test_ex', 1, 'woow', 'Video2.mp4', '');

-- --------------------------------------------------------

--
-- Structure de la table `program`
--

CREATE TABLE `program` (
  `id` int(11) NOT NULL,
  `name` varchar(255) NOT NULL,
  `creator` varchar(255) NOT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

--
-- Déchargement des données de la table `program`
--

INSERT INTO `program` (`id`, `name`, `creator`) VALUES
(1, 'Default Program', 'admin'),
(2, 'test_Prog', 'admin'),
(6, 'rr', 'hatem');

-- --------------------------------------------------------

--
-- Structure de la table `program_details`
--

CREATE TABLE `program_details` (
  `id` int(11) NOT NULL,
  `program_id` int(11) NOT NULL,
  `exercice_code` varchar(255) DEFAULT NULL,
  `break_id` int(11) DEFAULT NULL,
  `sequence` int(11) NOT NULL,
  `day` int(11) NOT NULL,
  `type` enum('exercise','break') NOT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

--
-- Déchargement des données de la table `program_details`
--

INSERT INTO `program_details` (`id`, `program_id`, `exercice_code`, `break_id`, `sequence`, `day`, `type`) VALUES
(32, 2, 'TE_N_2', NULL, 1, 2, 'exercise'),
(44, 2, 'TE_N_2', NULL, 1, 4, 'exercise'),
(46, 2, 'PO_E_2', NULL, 1, 1, 'exercise'),
(47, 2, 'PO_E_2', NULL, 1, 3, 'exercise'),
(57, 2, 'TE_N_2', NULL, 2, 1, 'exercise'),
(60, 2, 'TE_N_2', NULL, 3, 2, 'exercise'),
(61, 2, 'PO_E_2', NULL, 4, 2, 'exercise'),
(62, 2, 'TE_T_2', NULL, 2, 2, 'exercise'),
(74, 6, 'TE_N_2', NULL, 1, 2, 'exercise'),
(76, 6, 'TE_N_2', NULL, 1, 1, 'exercise'),
(77, 6, 'TE_T_2', NULL, 2, 1, 'exercise'),
(78, 6, 'TE_N_2', NULL, 3, 1, 'exercise');

-- --------------------------------------------------------

--
-- Structure de la table `users`
--

CREATE TABLE `users` (
  `id` int(11) NOT NULL,
  `mac_address` varchar(20) DEFAULT NULL,
  `name` varchar(50) NOT NULL,
  `is_confirmed` tinyint(1) DEFAULT 0,
  `is_admin` tinyint(1) DEFAULT 0,
  `program_id` int(11) DEFAULT NULL,
  `gender` varchar(10) DEFAULT NULL,
  `remarks` text DEFAULT NULL,
  `dateOfBirth` date DEFAULT NULL,
  `expire_date` date DEFAULT NULL,
  `familyName` varchar(255) DEFAULT NULL,
  `Photo` varchar(255) DEFAULT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

--
-- Déchargement des données de la table `users`
--

INSERT INTO `users` (`id`, `mac_address`, `name`, `is_confirmed`, `is_admin`, `program_id`, `gender`, `remarks`, `dateOfBirth`, `expire_date`, `familyName`, `Photo`) VALUES
(7, 'e0:0a:f6:b0:e1:ba', 'admin', 1, 1, 1, 'Male', 'None', NULL, '2024-12-21', NULL, NULL),
(9, 'ba-f5-e5-9c-a1-a6', 'Seifeddine ', 1, 0, 6, 'Male', 'bo5li', '2000-06-05', '2024-12-20', 'Ben amor', 'R.jpg'),
(16, '92-33-73-63-95-5f', 'Farah ', 1, 0, 2, 'Female', 'Débutante', '2000-10-28', '2025-01-20', 'Omri', 'girl.jpg'),
(17, 'fe-c9-c8-89-af-9f', 'Seifoun', 1, 0, 6, 'Male', 'None', '2000-12-28', '2025-01-31', 'Ben a', 'R.jpg'),
(18, '62-6b-94-7f-60-8e', 'Feres', 0, 0, 1, 'male', NULL, '2007-01-20', '2025-01-26', 'Chda5lik', NULL);

--
-- Index pour les tables déchargées
--

--
-- Index pour la table `break`
--
ALTER TABLE `break`
  ADD PRIMARY KEY (`Id`);

--
-- Index pour la table `category`
--
ALTER TABLE `category`
  ADD PRIMARY KEY (`Id`);

--
-- Index pour la table `exercices`
--
ALTER TABLE `exercices`
  ADD PRIMARY KEY (`code`),
  ADD KEY `fk_category` (`category_id`);

--
-- Index pour la table `program`
--
ALTER TABLE `program`
  ADD PRIMARY KEY (`id`);

--
-- Index pour la table `program_details`
--
ALTER TABLE `program_details`
  ADD PRIMARY KEY (`id`),
  ADD KEY `program_id` (`program_id`),
  ADD KEY `exercice_code` (`exercice_code`),
  ADD KEY `break_id` (`break_id`);

--
-- Index pour la table `users`
--
ALTER TABLE `users`
  ADD PRIMARY KEY (`id`),
  ADD KEY `fk_user_program` (`program_id`);

--
-- AUTO_INCREMENT pour les tables déchargées
--

--
-- AUTO_INCREMENT pour la table `break`
--
ALTER TABLE `break`
  MODIFY `Id` int(11) NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=3;

--
-- AUTO_INCREMENT pour la table `category`
--
ALTER TABLE `category`
  MODIFY `Id` int(11) NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=9;

--
-- AUTO_INCREMENT pour la table `program`
--
ALTER TABLE `program`
  MODIFY `id` int(11) NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=7;

--
-- AUTO_INCREMENT pour la table `program_details`
--
ALTER TABLE `program_details`
  MODIFY `id` int(11) NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=79;

--
-- AUTO_INCREMENT pour la table `users`
--
ALTER TABLE `users`
  MODIFY `id` int(11) NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=19;

--
-- Contraintes pour les tables déchargées
--

--
-- Contraintes pour la table `exercices`
--
ALTER TABLE `exercices`
  ADD CONSTRAINT `fk_category` FOREIGN KEY (`category_id`) REFERENCES `category` (`Id`);

--
-- Contraintes pour la table `program_details`
--
ALTER TABLE `program_details`
  ADD CONSTRAINT `program_details_ibfk_1` FOREIGN KEY (`program_id`) REFERENCES `program` (`id`) ON DELETE CASCADE ON UPDATE CASCADE,
  ADD CONSTRAINT `program_details_ibfk_2` FOREIGN KEY (`exercice_code`) REFERENCES `exercices` (`code`) ON DELETE CASCADE ON UPDATE CASCADE,
  ADD CONSTRAINT `program_details_ibfk_3` FOREIGN KEY (`break_id`) REFERENCES `break` (`Id`) ON DELETE CASCADE ON UPDATE CASCADE;

--
-- Contraintes pour la table `users`
--
ALTER TABLE `users`
  ADD CONSTRAINT `fk_user_program` FOREIGN KEY (`program_id`) REFERENCES `program` (`id`) ON DELETE SET NULL ON UPDATE CASCADE;
COMMIT;

/*!40101 SET CHARACTER_SET_CLIENT=@OLD_CHARACTER_SET_CLIENT */;
/*!40101 SET CHARACTER_SET_RESULTS=@OLD_CHARACTER_SET_RESULTS */;
/*!40101 SET COLLATION_CONNECTION=@OLD_COLLATION_CONNECTION */;
