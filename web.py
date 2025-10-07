import cave
import flask
from flask import Flask, render_template,request,redirect,url_for,flash, session
import sqlite3, hashlib

from cave import Utilisateur

app = Flask(__name__)
app.secret_key = "MaCleTopSecreteDeLaMortQuiTue"

def get_db_connection():
    conn = sqlite3.connect("cave_a_vin.db")
    conn.row_factory = sqlite3.Row
    return conn

def get_user():
    login_user = session['user']['login']  # récupérer le login

    # Créer l'objet Utilisateur avec le login et la connexion DB
    db = cave.DB()
    cur = db.conn.cursor()
    cur.execute("SELECT * FROM Utilisateur WHERE login = ?", (login_user,))
    row = cur.fetchone()
    # Instancier l'utilisateur
    user = cave.Utilisateur(
        id_utilisateur=row['id'],
        nom=row['nom'],
        prenom=row['prenom'],
        login=row['login'],
        mot_de_passe=row['mot_de_passe'],
        conn=db.conn
    )
    return user





@app.route("/")
def index():
    if 'user' not in session:
        return redirect(url_for('login'))
    user = get_user()
    MesBouteilles = user.afficher_bouteille()
    MesBouteillesArchivees = user.afficher_bouteille_archivees()
    VoirMaCave = user.consulter_cave()
    return render_template('index.html', user=session['user'],bouteilles = MesBouteilles,cave = VoirMaCave, bouteillesArchivees= MesBouteillesArchivees)

@app.route("/bouteille")
def bouteille():
    if 'user' not in session:
        return redirect(url_for('login'))
    user = get_user()
    MesBouteilles = user.afficher_bouteille()
    return render_template('bouteille.html', bouteilles = MesBouteilles, user = session['user'])


@app.route("/communaute")
def communaute():
    user = get_user()
    ToutesBouteillesArchivees = user.afficher_bouteille_archivees_global()
    return render_template("communaute.html", bouteillesArchivees = ToutesBouteillesArchivees,  user = session['user'])


@app.route("/cave")
def MaCave():
    if 'user' not in session:
        return redirect(url_for('login'))
    user = get_user()
    VoirMaCave = user.consulter_cave()
    return render_template("cave.html",cave = VoirMaCave,user= session['user'])


@app.route("/archiver/<int:bouteille_id>", methods=['GET', 'POST'])
def archiver(bouteille_id):
    if 'user' not in session:
        return redirect(url_for('login'))
    user = get_user()
    if request.method == 'POST':
        # Récupérer la note depuis le formulaire
        note = request.form.get('note')
        commentaire = request.form.get("commentaire")
        try:
            note = float(note)
            if note < 0 or note > 10:
                return redirect(url_for('archiver', bouteille_id=bouteille_id))
        except ValueError:
            return redirect(url_for('archiver', bouteille_id=bouteille_id))

        # Mettre à jour la bouteille dans la DB
        cur = user.conn.cursor()
        cur.execute(
            "UPDATE Bouteille SET statut = 1, note = ?, commentaire = ? WHERE id = ? AND proprietaire = ?",
            (note, commentaire, bouteille_id, user.login)
        )
        user.conn.commit()
        return redirect(url_for('index'))
    # GET → afficher le formulaire
    return render_template("archiver.html", bouteille_id=bouteille_id)


@app.route("/cave/creer", methods=['GET', 'POST'])
def creer_cave():
    user = get_user()
    if 'user' not in session:
        return redirect(url_for('login'))
    if request.method == 'POST':
        nom_cave = request.form.get('nom_cave')
        MaCave = cave.Cave(nom_cave)
        Utilisateur.sauvegarder_cave(user, MaCave)

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        login = request.form['login']
        password = request.form['password']

        # Hash du mot de passe (comme dans ta classe Utilisateur)
        hashed = hashlib.sha256(password.encode()).hexdigest()

        conn = get_db_connection()
        user = conn.execute("SELECT * FROM Utilisateur WHERE login = ? AND mot_de_passe = ?", (login, hashed)).fetchone()
        conn.close()

        if user:
            session['user'] = dict(user)
            flash(f"Bienvenue {user['prenom']} !", "success")
            return redirect(url_for('index'))
        else:
            flash("Identifiant ou mot de passe incorrect.", "danger")

    return render_template('login.html')


@app.route('/logout')
def logout():
    session.pop('user', None)
    flash("Vous êtes déconnecté.", "info")
    return redirect(url_for('login'))



if __name__ == "__main__":
    app.run(debug=True)