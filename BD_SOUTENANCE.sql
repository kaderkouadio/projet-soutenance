
DROP DATABASE IF EXISTS BD_SOUTENANCE
CREATE DATABASE BD_SOUTENANCE

USE BD_SOUTENANCE;


DROP TABLE IF EXISTS Utilisateurs;
CREATE TABLE Utilisateurs (
    IdUtilisateurs INT NOT NULL PRIMARY KEY IDENTITY(1,1),
    Nom VARCHAR(255),
    Prenoms VARCHAR(255),
	Genre VARCHAR(255),
    Telephone VARCHAR(255),
    Adresse VARCHAR(255),
    Email VARCHAR(255) UNIQUE,
    Mot_de_pass VARCHAR(MAX),
    Roles VARCHAR(255),
	Date_Creation DATETIME 
);


DROP TABLE IF EXISTS Personnels;
CREATE TABLE Personnels (
    IdPersonnels INT NOT NULL PRIMARY KEY IDENTITY(1,1),
    Date_embauche DATE,	
    IdUtilisateurs INT NOT NULL,
    FOREIGN KEY (IdUtilisateurs) REFERENCES Utilisateurs(IdUtilisateurs)
);


DROP TABLE IF EXISTS Images;
CREATE TABLE Images (
    IdImages INT NOT NULL PRIMARY KEY IDENTITY(1,1),
    Image_Url VARCHAR(MAX),	
    IdUtilisateurs INT NOT NULL,
    FOREIGN KEY (IdUtilisateurs) REFERENCES Utilisateurs(IdUtilisateurs)
);



DROP TABLE IF EXISTS Categories;
CREATE TABLE Categories (
    IdCategories INT NOT NULL PRIMARY KEY IDENTITY(1,1),
    Images VARCHAR(MAX),
    Titre VARCHAR(255),
    DetailsCategories VARCHAR(255),
);

-----DROP TABLE IF EXISTS Cours;
-----CREATE TABLE Cours (
------    IdCours INT NOT NULL PRIMARY KEY IDENTITY(1,1),
 ------   Images VARCHAR(MAX),
 ------   Titre VARCHAR(255),
 ------   DetailsCours VARCHAR(255),
 ------   IdCategories INT NOT NULL,
 ------   FOREIGN KEY (IdCategories) REFERENCES Categories (IdCategories)
);

DROP TABLE IF EXISTS Programmes;
CREATE TABLE Programmes (
    IdProgrammes INT NOT NULL PRIMARY KEY IDENTITY(1,1),
    Images VARCHAR(MAX),
    Titre VARCHAR(255),
    Duree_programmes VARCHAR(255),
	Nombre_apprenants int,
    Date_debut DATE,
    Date_fin DATE,
	DetailsProgrammes VARCHAR(255),
    IdCategories INT NOT NULL,
    FOREIGN KEY (IdCategories) REFERENCES Categories (IdCategories)
);


DROP TABLE IF EXISTS Bailleurs;
CREATE TABLE Bailleurs (
    IdBailleurs INT NOT NULL PRIMARY KEY IDENTITY(1,1),
    NomEntreprise VARCHAR(255),
    Adresse VARCHAR(255),
    Telephone VARCHAR(255),
    Email VARCHAR(255),
    TypeFinancement VARCHAR(255),
    DetailsFinancement TEXT,
    MontantFinancement DECIMAL(18, 2),
    Nom_Contact VARCHAR(255),
    Poste_Contact VARCHAR(255),
    Telephone_Contact VARCHAR(255),
    Email_Contact VARCHAR(255),
    IdProgrammes INT NOT NULL,
    FOREIGN KEY (IdProgrammes) REFERENCES Programmes (IdProgrammes)
);

DROP TABLE IF EXISTS Formateurs;
CREATE TABLE Formateurs (
    IdFormateurs INT NOT NULL PRIMARY KEY IDENTITY(1,1),
    Diplomes VARCHAR(255),
    Annees_Experiences INT CHECK (Annees_Experiences >= 0),
    IdProgrammes INT NOT NULL,
    IdUtilisateurs INT NOT NULL,
    FOREIGN KEY (IdUtilisateurs) REFERENCES Utilisateurs (IdUtilisateurs),
    FOREIGN KEY (IdProgrammes) REFERENCES Programmes (IdProgrammes)
);


-- Table de liaison pour Formateurs et Programmes
---DROP TABLE IF EXISTS Enseigner;
---CREATE TABLE Enseigner (
  -- - IdFormateur INT NOT NULL,
   ---- IdProgramme INT NOT NULL,
    ----FOREIGN KEY (IdFormateur) REFERENCES Formateurs (IdFormateurs),
  ----  FOREIGN KEY (IdProgramme) REFERENCES Programmes (IdProgrammes),
   ---- PRIMARY KEY (IdFormateur, IdProgramme)
---);


DROP TABLE IF EXISTS Apprenants;
CREATE TABLE Apprenants (
    IdApprenants INT NOT NULL PRIMARY KEY IDENTITY(1,1),
    Niveau_Etudes VARCHAR(255),
    Diplomes VARCHAR(255),
    Age INT NOT NULL CHECK (Age >= 0),
    Nom_complet_parent VARCHAR(255),
    Telephone_parent VARCHAR(255),
    Adresse_parent VARCHAR(255),
    IdProgrammes INT NOT NULL,
	IdUtilisateurs INT NOT NULL,
    FOREIGN KEY (IdUtilisateurs) REFERENCES Utilisateurs (IdUtilisateurs),
    FOREIGN KEY (IdProgrammes) REFERENCES Programmes (IdProgrammes)
);



DROP TABLE IF EXISTS Documents;
CREATE TABLE Documents (
    IdDocuments INT NOT NULL PRIMARY KEY IDENTITY(1,1),
	NomFichier VARCHAR(255),
	CheminFichier VARCHAR(255),
    Dates DATETIME NOT NULL,
    IdProgrammes INT NOT NULL, 
    FOREIGN KEY (IdProgrammes) REFERENCES Programmes (IdProgrammes),
);



DROP TABLE IF EXISTS Commentaires;
CREATE TABLE Commentaires (
    IdCommentaires INT NOT NULL PRIMARY KEY IDENTITY(1,1),
    Communicataire VARCHAR(255),
    Emailing VARCHAR(255),
    Date_Communications DATE,
	avisformateur VARCHAR(255),
	Analyse VARCHAR(255),
	avisprogramme VARCHAR(255),
    Sentiment VARCHAR(255),
    IdApprenants INT NOT NULL,
	IdFormateurs INT NOT NULL,
    FOREIGN KEY (IdApprenants) REFERENCES Apprenants (IdApprenants),
	FOREIGN KEY (IdFormateurs) REFERENCES Formateurs (IdFormateurs),
);


SELECT * FROM Utilisateurs WHERE Email = 'kkaderkouadio@gmail.com'

SELECT * FROM Utilisateurs


select * from  Personnels

select * from  Images

select * from  Categories

select * from  Cours

select * from  Programmes

select * from  Formateurs

select * from  Apprenants


DELETE FROM Communications


select Images,Titre, Nombre_apprenants,Date_debut, Duree_programmes from Programmes;


SELECT U.Telephone
FROM Utilisateurs U
INNER JOIN Formateurs F ON U.IdUtilisateurs = F.IdUtilisateurs
WHERE F.IdProgrammes = 1;



SELECT U.Telephone
FROM Utilisateurs U
INNER JOIN Formateurs F ON U.IdUtilisateurs = F.IdUtilisateurs
WHERE F.IdProgrammes IN (
    SELECT P.IdProgrammes
    FROM Programmes P
    WHERE P.Titre LIKE '%Developpeur Data IA%'
);


DELETE FROM Utilisateurs WHERE IdUtilisateurs = 1;


DELETE FROM Utilisateurs;

DELETE FROM Personnels;

DELETE FROM Personnels;


 SELECT F.*, U.*, I.*
        FROM Formateurs F
        JOIN Utilisateurs U ON F.IdUtilisateurs = U.IdUtilisateurs
        JOIN Images I ON F.IdUtilisateurs = I.IdUtilisateurs;