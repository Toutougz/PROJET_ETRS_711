###
# Imports
###
import sqlite3
from typing import Optional
from datetime import date
#######
#Classes
#######
class DB:

    def __init__(self, db_name="cave_a_vin.db"):
        self.conn = sqlite3.connect(db_name, check_same_thread=False)
        self.conn.row_factory = sqlite3.Row
        self.creer_tables()

    def creer_tables(self):
        cur = self.conn.cursor()

        cur.execute("""
                    CREATE TABLE IF NOT EXISTS Utilisateur
                    (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    nom TEXT,
                    prenom TEXT,
                    login TEXT,
                    mot_de_passe TEXT
                    )""")

        cur.execute("""
                    CREATE TABLE IF NOT EXISTS Bouteille
                    (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    domaine TEXT,
                    nom TEXT,
                    type TEXT,
                    annee DATE,
                    region TEXT,
                    commentaire TEXT,
                    note FLOAT,
                    moyenne FLOAT,
                    etiquette TEXT,
                    prix INTEGER
                    )""")

        cur.execute("""
                    CREATE TABLE IF NOT EXISTS Etagere
                    (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    nom TEXT,
                    nbr_bouteilles INTEGER,
                    bouteille INTEGER,
                    FOREIGN KEY (bouteille) REFERENCES Bouteille(id)
                    )""")

        cur.execute("""
                    CREATE TABLE IF NOT EXISTS Cave
                    (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    nom TEXT,
                    etagere INTEGER,
                    FOREIGN KEY (etagere) REFERENCES Etagere(id)
                    )""")

        self.conn.commit()


class Utilisateur:
    def __init__(self, id_utilisateur:int, nom:str,prenom:str, login:str, mot_de_passe:str):
        self.id_utilisateur = id_utilisateur
        self.nom = nom
        self.prenom = prenom
        self.login = login
        self.mot_passe = mot_de_passe
        self.caves: list["Cave"] = []
        self.bouteilles : list["Bouteille"] = []


    def ajouter_cave(self, cave:"Cave"):
        self.caves.append(cave)

    def ajouter_bouteille(self, bouteille:"Bouteille", cave:"Cave"):
        self.bouteilles.append(bouteille) # il faut ajouter la bouteille dans la cave

    def consulter_cave(self):
        for cave in self.caves:
            for bouteille in self.bouteilles:

                print(f"Cave(s) de {self.prenom} :  {cave.nom_cave}, {bouteille.nom}")


    def supprimer_bouteille(self):
        pass

    def archiver_bouteille(self):
        pass



    def afficher_bouteille(self):
        pass

    def trier_bouteille(self):
        pass


class Cave:
    def __init__(self, id_cave:int, nom_cave:str,nombre_bouteille:Optional[int]=None):
        self.id_cave = id_cave
        self.nombre_bouteille = nombre_bouteille
        self.nom_cave = nom_cave

class etagere:
    def __init__(self,id_etagere,nom_etagere,emplacement_bouteille:int):
        self.id_etagere = id_etagere
        self.nom_etagere = nom_etagere
        self.emplacement_bouteille = emplacement_bouteille


class Bouteille:
    def __init__(self, domaine:str,nom:str,type:str,annee:date,region:str,commentaire:str,note:float,moyenne:float,
                 prix:float, etiquette: Optional[str] = None):
        self.domaine = domaine
        self.nom = nom
        self.type = type
        self.annee = annee
        self.region = region
        self.commentaire = commentaire
        self.note = note
        self.moyenne = moyenne
        self.etiquette = etiquette
        self.prix = prix


DB()

user1 = Utilisateur(1,"User1","PrenomUser1","puser1","azerty123")
cave1 = Cave(1,"cave1")
Utilisateur.ajouter_cave(user1,cave1)
user2=Utilisateur(2,"User2","PrenomUser2","puser2","azerty321")
cave2=Cave(2,"cave2")
bouteille1 = Bouteille("Chateau Bourgogne","Cabernet Sauvignon","Rouge",date.today(),"Bourgogne","Super BON",8,6.8,53)
Utilisateur.ajouter_bouteille(user1,bouteille1,cave1)

Utilisateur.ajouter_cave(user2,cave2)
Utilisateur.consulter_cave(user1)
Utilisateur.consulter_cave(user2)



