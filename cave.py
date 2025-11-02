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
                    note INTEGER ,
                    moyenne INTEGER,
                    etiquette TEXT,
                    prix INTEGER,
                    proprietaire TEXT,
                    statut  INTEGER,
                    etagere_id INTEGER,
                    FOREIGN KEY (proprietaire) REFERENCES Utilisateur(login),
                    FOREIGN KEY (etagere_id) REFERENCES Etagere(id)
                    )""")

        cur.execute("""
                    CREATE TABLE IF NOT EXISTS Etagere
                    (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    nom TEXT,
                    capacite INTEGER,
                    proprietaire TEXT,
                    FOREIGN KEY (proprietaire) REFERENCES Utilisateur(login)
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
            return False
        else:
            LOGGER.debug(f"{cave.nom_cave} ")
            cur.execute(
                "INSERT INTO Cave (nom, proprietaire) VALUES (?, ?)",
                (cave.nom_cave, self.login)
            )
            LOGGER.debug(f"{cave.nom_cave} ajoutée à la BDD")
            self.conn.commit()
            return True


    def consulter_cave(self):
        #for cave in self.caves:
        #    print(f"{cave.nom_cave} de {self.login}, {len(self.bouteilles)} bouteille(s)")

        cur = self.conn.cursor()
        cur.execute("SELECT * FROM Cave WHERE proprietaire = ?", (self.login,))
        MesCaves = cur.fetchall()
        return MesCaves
        # pour la db, faire select * puis compter les lignes qui nous concernent. peut etre ajouter une reference
        # entre bouteille et cave, ou utiliser la etagere ?????????

            #for bouteille in self.bouteilles:
                #print(f"liste des bouteilles: {self.bouteilles}")
                # print(f"Cave(s) de {self.prenom} :  {cave.nom_cave}, {bouteille}")


    def ajouter_bouteille(self, bouteille:"Bouteille"):
        self.bouteilles.append(bouteille)
        LOGGER.debug(f"Bouteille : {bouteille.nom} ajoutée")
        #print(f"Bouteille : {bouteille.nom} ajoutée")

    """   def sauvegarder_bouteille(self, bouteille:"Bouteille"):
        cur = self.conn.cursor()
        # Vérification : le user a t-il deja une cave ?
        if self.consulter_cave():
            LOGGER.debug(f"{bouteille.nom} ")
            cur.execute(
                    "INSERT INTO Bouteille (domaine, nom, type, annee, region, commentaire, etiquette, prix, proprietaire, statut) VALUES (?,?,?,?,?,?,?,?,?,?)",
                    (
                        bouteille.domaine,  # domaine
                        bouteille.nom,  # nom
                        bouteille.type,  # type
                        bouteille.annee,  # annee
                        bouteille.region,  # region
                        bouteille.commentaire or "",  # commentaire
                        bouteille.etiquette or "",  # etiquette (chemin image)
                        bouteille.prix or 0,  # prix
                        self.login,  # proprietaire
                        0  # statut
                    )
                    )
            LOGGER.debug(f"{bouteille.nom} ajoutée à la BDD")
            self.conn.commit()
        else:
            print("impossible d'ajouter une bouteille vous n'avez pas de cave")"""


    def sauvegarder_bouteille(self, bouteille: "Bouteille"):
        cur = self.conn.cursor()
        if self.consulter_cave():
            # Vérifie si l'étagère a encore de la place
            cur.execute("""
                SELECT COUNT(*) FROM Bouteille WHERE etagere_id = ?
            """, (bouteille.etagere_id,))
            nb_bouteilles = cur.fetchone()[0]

            cur.execute("""
                SELECT capacite FROM Etagere WHERE id = ?
            """, (bouteille.etagere_id,))
            capacite = cur.fetchone()[0]

            if nb_bouteilles < capacite:
                cur.execute("""
                    INSERT INTO Bouteille (domaine, nom, type, annee, region, commentaire,
                                           etiquette, prix, proprietaire, statut, etagere_id)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    bouteille.domaine,
                    bouteille.nom,
                    bouteille.type,
                    bouteille.annee,
                    bouteille.region,
                    bouteille.commentaire or "",
                    bouteille.etiquette or "",
                    bouteille.prix or 0,
                    self.login,
                    0,
                    bouteille.etagere_id
                ))
                LOGGER.debug(f"{bouteille.nom} ajoutée à la BDD sur l'étagère {bouteille.etagere_id}")
                self.conn.commit()
                return True
            else:
                print("Impossible d'ajouter la bouteille : étagère pleine.")
                return False
        else:
            print("Impossible d'ajouter une bouteille : vous n'avez pas de cave.")



    def afficher_bouteille(self):
        #for bouteille in self.bouteilles:
        #    print(f"{bouteille}")

        cur = self.conn.cursor()
        cur.execute("SELECT * FROM Bouteille WHERE proprietaire = ? and statut = 0", (self.login,))
        AllMyBottle = cur.fetchall()
        #print(AllMyBottle)
        return AllMyBottle

    def archiver_bouteille(self, bouteille_id: int):
        """Met à jour le statut d'une bouteille à 1 (archivée)"""
        cur = self.conn.cursor()
        cur.execute("UPDATE Bouteille SET statut = 1 WHERE id = ? AND proprietaire = ?", (bouteille_id, self.login))
        self.conn.commit()

    def afficher_bouteille_archivees(self):
        cur = self.conn.cursor()
        cur.execute("SELECT * FROM Bouteille WHERE proprietaire = ? and statut = 1", (self.login,))
        AllMyArchivedBottle = cur.fetchall()
        #print(AllMyBottle)
        return AllMyArchivedBottle

    def afficher_bouteille_archivees_global(self):
        cur = self.conn.cursor()
        cur.execute("SELECT * FROM Bouteille WHERE statut = 1" )
        ArchivedBottle = cur.fetchall()
        print(ArchivedBottle)
        return ArchivedBottle


    def supprimer_bouteille(self,bouteille:"Bouteille"):
        self.bouteilles.remove(bouteille)
        LOGGER.debug(f"Bouteille {bouteille.nom} supprimée")
        #print(f"Bouteille {bouteille.nom} supprimée")


    def sauvegarder_etagere(self, etagere: "Etagere"):
        cur = self.conn.cursor()
        cur.execute("""
            INSERT INTO Etagere (nom, capacite, proprietaire)
            VALUES (?, ?, ?)
        """, (etagere.nom_etagere, etagere.capacite, self.login))
        LOGGER.debug(f"{etagere.nom_etagere} ajoutée à la BDD")
        self.conn.commit()

    def consulter_etagere(self):
            cur = self.conn.cursor()
            cur.execute("""
                SELECT E.id, E.nom, E.capacite, B.nom, B.annee, B.type, B.region
                FROM Etagere E
                LEFT JOIN Bouteille B ON E.id = B.etagere_id
                WHERE E.proprietaire = ?
                ORDER BY E.id
            """, (self.login,))
            return cur.fetchall()

    def supprimer_etagere(self, etagere_id: int):
        cur = self.conn.cursor()

        # Vérifier si l'étagère contient des bouteilles
        cur.execute("""
            SELECT COUNT(*) FROM Bouteille
            WHERE etagere_id = ? AND proprietaire = ?
        """, (etagere_id, self.login))

        nb_bouteilles = cur.fetchone()[0]

        if nb_bouteilles > 0:
            # Impossible de supprimer : il y a encore des bouteilles
            return False
        else:
            # On supprime l'étagère
            cur.execute("DELETE FROM Etagere WHERE id = ? AND proprietaire = ?", (etagere_id, self.login))
            self.conn.commit()
            return True

    def trier_bouteille(self):
        pass


class Cave:
    def __init__(self, nom_cave:str,nombre_bouteille:Optional[int]=None):
        self.nombre_bouteille = nombre_bouteille
        self.nom_cave = nom_cave

class Etagere:
    def __init__(self,id_etagere,nom_etagere, proprietaire, capacite):
        self.id_etagere = id_etagere
        self.nom_etagere = nom_etagere
        self.proprietaire = proprietaire
        self.capacite = capacite

    def __str__(self):
        return f"{self.nom_etagere}, Il y a {self.emplacement_bouteille} emplacements"

class Bouteille:
    def __init__(self, domaine:str,nom:str,type:str,annee:str,region:str, prix:float, conn=None, commentaire:Optional[str] = None ,note:Optional[float] = None,moyenne:Optional[float] = None, etiquette: Optional[str] = None, etagere_id: Optional[int] = None,):
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
        self.conn=conn
        self.etagere_id = etagere_id

    def calculerMoyenne(self):
        cur = self.conn.cursor()
        cur.execute("SELECT AVG(note) FROM Bouteille WHERE nom = ? AND note IS NOT NULL", (self.nom,))
        resultat = cur.fetchone()
        self.moyenne = resultat[0] if resultat and resultat[0] is not None else 0

        # Mettre à jour la moyenne dans la BDD pour cette bouteille
        cur.execute("UPDATE Bouteille SET moyenne = ? WHERE nom = ?", (self.moyenne, self.nom))
        self.conn.commit()
        #on ne match que les bouteilles de 1 user, il faudrait faire comme pour le truc de communauté et matcher les statut = 1



    def __str__(self):
        return f" Bouteille : {self.domaine}, {self.nom}, {self.type}, {self.annee}, {self.region}"


#######
#MAIN
#######

def main():
    db = DB()
    user1 = Utilisateur(1,"User1","PrenomUser1","puser1","azerty123",conn=db.conn)
    cave1 = Cave("cave1")
    Utilisateur.ajouter_cave(user1,cave1)
    user2=Utilisateur(2,"User2","PrenomUser2","puser2","azerty321", conn=db.conn)
    cave2=Cave("cave2")

    bouteille1 = Bouteille("Chateau Bourgogne","Cabernet Sauvignon","Rouge",2018,"Bourgogne",25)
    bouteille2 = Bouteille("Chateau Coca","Cocacola","Blanc",2014,"Bourgogne",98)
    bouteille3 = Bouteille("Chateau Tencin","Le tencinois","Rosée",2003,"Isere",42)



    Utilisateur.ajouter_bouteille(user1,bouteille1)
    Utilisateur.ajouter_bouteille(user1,bouteille2)
    Utilisateur.ajouter_bouteille(user1,bouteille3)


    Utilisateur.sauvegarder_bouteille(user1,bouteille1)
    Utilisateur.sauvegarder_bouteille(user2,bouteille3)
    Utilisateur.sauvegarder_bouteille(user2,bouteille2)


    Utilisateur.ajouter_cave(user2,cave2)
    Utilisateur.ajouter_cave(user1,cave1)

    Utilisateur.supprimer_bouteille(user1, bouteille1)

    Utilisateur.consulter_cave(user1)
    Utilisateur.consulter_cave(user2)

    Utilisateur.consulter_etagere(user1)

    Utilisateur.sauvegarder_user(user1)
    Utilisateur.sauvegarder_user(user2)

    Utilisateur.sauvegarder_cave(user2,cave2)
    Utilisateur.sauvegarder_cave(user1, cave1)


    Utilisateur.afficher_bouteille(user1)


    Utilisateur.afficher_bouteille_archivees_global(user1)

if __name__ == "__main__":  # Configuration de la journalisation
    logging.basicConfig(level=logging.DEBUG)
    main()



