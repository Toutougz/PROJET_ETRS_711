#######
#Imports
#######
import sqlite3
from typing import Optional
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
#Creation des tables de la DB
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
#Modif du return de la class Utilisateur
    def __str__(self):
        return f"[{self.id_utilisateur}] {self.nom} {self.prenom} ({self.login})"


    def sauvegarder_user(self):
          """ Permet de sauvegarder l'utilisateur en DB"""
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
            return f"{self} ajouté à la BDD"


    def sauvegarder_cave(self,cave:"Cave"):
        """permet de creer la cave en DB"""
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
        """On récupère les caves dans la DB, pour les afficher"""
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


    def sauvegarder_bouteille(self, bouteille: "Bouteille"):
        """Permet de créer une bouteille en DB"""
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
            return True



    def afficher_bouteille(self):
        """Recupère une bouteille en DB pour l'afficher"""

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
        """Recupere les bouteilles avec le statut à 1 (archivée) pour le user connecté"""
        cur = self.conn.cursor()
        cur.execute("SELECT * FROM Bouteille WHERE proprietaire = ? and statut = 1", (self.login,))
        AllMyArchivedBottle = cur.fetchall()
        #print(AllMyBottle)
        return AllMyArchivedBottle

    def afficher_bouteille_archivees_global(self):
        """Recupere les bouteilles avec le statut à 1 (archivée) pour la communauté"""
        cur = self.conn.cursor()
        cur.execute("SELECT * FROM Bouteille WHERE statut = 1" )
        ArchivedBottle = cur.fetchall()
        print(ArchivedBottle)
        return ArchivedBottle

    def sauvegarder_etagere(self, etagere: "Etagere"):
        """Permet de créer une étagère dans la DB"""
        cur = self.conn.cursor()
        cur.execute("""
            INSERT INTO Etagere (nom, capacite, proprietaire)
            VALUES (?, ?, ?)
        """, (etagere.nom_etagere, etagere.capacite, self.login))
        LOGGER.debug(f"{etagere.nom_etagere} ajoutée à la BDD")
        self.conn.commit()

    def consulter_etagere(self):
            """Recupère l'étagère pour l'afficher"""
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
        """Pour supprimer l'étagère si elle est vide"""
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
        """Permet de trier les bouteilles selon un critère"""
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
        return f"{self.nom_etagere}, Il y a {self.capacite} emplacements"

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
        """On calcul une moyenne grace aux notes attribuées"""
        cur = self.conn.cursor()
        cur.execute("SELECT AVG(note) FROM Bouteille WHERE nom = ? AND type = ? AND note IS NOT NULL", (self.nom,self.type))
        resultat = cur.fetchone()
        self.moyenne = resultat[0] if resultat and resultat[0] is not None else 0

        # Mettre à jour la moyenne dans la BDD pour cette bouteille
        cur.execute("UPDATE Bouteille SET moyenne = ? WHERE nom = ? AND type = ?", (self.moyenne, self.nom,self.type))
        self.conn.commit()
        #on ne match que les bouteilles de 1 user, il faudrait faire comme pour le truc de communauté et matcher les statut = 1


    def __str__(self):
        return f" Bouteille : {self.domaine}, {self.nom}, {self.type}, {self.annee}, {self.region}"


#######
#MAIN
#######

def main():


    if __name__ == "__main__":
        logging.basicConfig(level=logging.DEBUG) # Pour voir les logs dans la console
        main()



