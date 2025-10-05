#######
#Imports
#######
import sqlite3
from typing import Optional
from datetime import date
import logging
import hashlib
LOGGER = logging.getLogger(__name__)

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
                    proprietaire TEXT,
                    FOREIGN KEY (etagere) REFERENCES Etagere(id),
                    FOREIGN KEY (proprietaire) REFERENCES Utilisateur(login)
                    )""")

        self.conn.commit()


class Utilisateur(DB):
    def __init__(self, id_utilisateur:int, nom:str,prenom:str, login:str, mot_de_passe:str, conn=None):
        self.id_utilisateur = id_utilisateur
        self.nom = nom
        self.prenom = prenom
        self.login = login
        self.mot_passe = mot_de_passe
        self.caves: list["Cave"] = []
        self.bouteilles : list["Bouteille"] = []
        self.conn=conn

    def __str__(self):
        return f"[{self.id_utilisateur}] {self.nom} {self.prenom} ({self.login})"


    def sauvegarder_user(self):
          cur = self.conn.cursor()
          # Vérification : l'utilisateur existe-t-il déjà ?
          cur.execute("SELECT * FROM Utilisateur WHERE login = ?", (self.login,))
          utilisateur_existant = cur.fetchone()

          if utilisateur_existant:
              LOGGER.debug(f"{self} deja dans la BDD")
              return f"{self} deja dans la BDD"
          else:
            mot_de_passe_hash = hashlib.sha256(self.mot_passe.encode()).hexdigest()
            cur.execute(
                "INSERT INTO Utilisateur (nom, prenom, login, mot_de_passe) VALUES (?, ?, ?, ?)",
                (self.nom, self.prenom, self.login, mot_de_passe_hash)
            )
            LOGGER.debug(f"{self} ajouté à la BDD")
            self.conn.commit()
            self.id_utilisateur = cur.lastrowid

    def ajouter_cave(self, cave:"Cave"):
        if len(self.caves) != 0:
            print("Vous ne pouvez pas créer de cave, vous avez déja une cave")
        else:
            self.caves.append(cave)

    def sauvegarder_cave(self,cave:"Cave"):
        cur = self.conn.cursor()
        # Vérification : le user a t-il deja une cave ?
        cur.execute("SELECT * FROM Cave WHERE proprietaire = ?", (self.login,))
        cave_existant = cur.fetchone()
        if cave_existant:
            LOGGER.debug(f"{self} à deja une cave")
            return f"{self} à deja une cave"
        else:
            LOGGER.debug(f"{cave.nom_cave} ")
            cur.execute(
                "INSERT INTO Cave (id, nom, proprietaire) VALUES (?, ?, ?)",
                (cave.id_cave, cave.nom_cave, self.login)
            )
            LOGGER.debug(f"{cave.nom_cave} ajoutée à la BDD")
            self.conn.commit()


    def ajouter_bouteille(self, bouteille:"Bouteille"):
        self.bouteilles.append(bouteille)
        LOGGER.debug(f"Bouteille : {bouteille.nom} ajoutée")
        #print(f"Bouteille : {bouteille.nom} ajoutée")

    def afficher_bouteille(self):
        for bouteille in self.bouteilles:
            print(f"{bouteille}")

    def consulter_cave(self):
        for cave in self.caves:
            print(f"{cave.nom_cave} de {self.login}, {len(self.bouteilles)} bouteille(s)")
        # pour la db, faire select * puis compter les lignes qui nous concernent. peut etre ajouter une reference
        # entre bouteille et cave, ou utiliser la etagere ?????????

            #for bouteille in self.bouteilles:
                #print(f"liste des bouteilles: {self.bouteilles}")
                # print(f"Cave(s) de {self.prenom} :  {cave.nom_cave}, {bouteille}")


    def supprimer_bouteille(self,bouteille:"Bouteille"):
        self.bouteilles.remove(bouteille)
        LOGGER.debug(f"Bouteille {bouteille.nom} supprimée")
        #print(f"Bouteille {bouteille.nom} supprimée")

    def archiver_bouteille(self):
        pass
    # Une fois que la bouteille est bue, on peut lui mettre une note, celle ci sera visible de tous les users.

    def consulter_etagere(self):
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

    def __str__(self):
        return f" Bouteille : {self.domaine}, {self.nom}, {self.type}, {self.annee}, {self.region}"


#######
#MAIN
#######

def main():
    db = DB()
    user1 = Utilisateur(1,"User1","PrenomUser1","puser1","azerty123",conn=db.conn)
    cave1 = Cave(1,"cave1")
    Utilisateur.ajouter_cave(user1,cave1)
    user2=Utilisateur(2,"User2","PrenomUser2","puser2","azerty321", conn=db.conn)
    cave2=Cave(2,"cave2")
    bouteille1 = Bouteille("Chateau Bourgogne","Cabernet Sauvignon","Rouge",date.today(),"Bourgogne","Super BON",8,6.8,53)
    bouteille2 = Bouteille("Chateau Coca","Cocacola","Blanc",date.today(),"Bourgogne","Super Degueu",4,8.6,65)
    bouteille3 = Bouteille("Chateau Tencin","Le tencinois","Rosée",date.today(),"Isere","Super DELICIEUX",10,10,12)

    Utilisateur.ajouter_bouteille(user1,bouteille1)
    Utilisateur.ajouter_bouteille(user1,bouteille2)
    Utilisateur.ajouter_bouteille(user1,bouteille3)

    Utilisateur.ajouter_cave(user2,cave2)
    Utilisateur.supprimer_bouteille(user1, bouteille1)
    Utilisateur.consulter_cave(user1)
    Utilisateur.consulter_cave(user2)


    Utilisateur.sauvegarder_user(user1)
    Utilisateur.sauvegarder_user(user2)
    Utilisateur.sauvegarder_cave(user2,cave2)
    # Utilisateur.sauvegarder_user(user2)

    # Utilisateur.afficher_bouteille(user1)

if __name__ == "__main__":  # Configuration de la journalisation
    logging.basicConfig(level=logging.DEBUG)
    main()



