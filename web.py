import cave
import flask
from flask import Flask, render_template, request, redirect, url_for, flash, session
import sqlite3, hashlib
from werkzeug.security import generate_password_hash
from werkzeug.utils import secure_filename
from cave import Utilisateur
import os

app = Flask(__name__)
app.secret_key = "MaCleTopSecreteDeLaMortQuiTue"
db_init= cave.DB()

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

UPLOAD_FOLDER = "./static/images"
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS



@app.route("/")
def index():
    if 'user' not in session:
        return redirect(url_for('login'))

    user = get_user()
    MesBouteillesArchivees = user.afficher_bouteille_archivees()

    # Récupérer les caves
    VoirMaCave = user.consulter_cave()

    # Construire une structure caves → étagères → bouteilles
    cur = user.conn.cursor()
    caves_data = []
    for cave_row in VoirMaCave:
        cave_id = cave_row['id']

        # Récupérer les étagères de cette cave
        cur.execute("""
            SELECT * FROM Etagere WHERE proprietaire = ? ORDER BY id
        """, (user.login,))
        etageres = cur.fetchall()

        etageres_data = []
        for etagere in etageres:
            etagere_id = etagere['id']

            # Récupérer les bouteilles de cette étagère
            cur.execute("""
                SELECT * FROM Bouteille WHERE etagere_id = ? AND proprietaire = ? AND statut = 0""", (etagere_id, user.login))
            bouteilles = cur.fetchall()

            etageres_data.append({
                'etagere': etagere,
                'bouteilles': bouteilles
            })

        caves_data.append({
            'cave': cave_row,
            'etageres': etageres_data
        })

    return render_template('index.html',user=session['user'],caves_data=caves_data,bouteillesArchivees=MesBouteillesArchivees)


@app.route("/bouteille")
def bouteille():
    if 'user' not in session:
        return redirect(url_for('login'))
    user = get_user()
    MesBouteilles = user.afficher_bouteille()
    return render_template('bouteille.html', bouteilles=MesBouteilles, user=session['user'])


@app.route("/communaute")
def communaute():
    user = get_user()
    ToutesBouteillesArchivees = user.afficher_bouteille_archivees_global()
    return render_template("communaute.html", bouteillesArchivees=ToutesBouteillesArchivees, user=session['user'])


@app.route("/cave")
def MaCave():
    if 'user' not in session:
        return redirect(url_for('login'))
    user = get_user()
    VoirMaCave = user.consulter_cave()
    return render_template("cave.html", cave=VoirMaCave, user=session['user'])


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
            "UPDATE Bouteille SET etagere_id = NULL, statut = 1, note = ?, commentaire = ? WHERE id = ? AND proprietaire = ?",
            (note, commentaire, bouteille_id, user.login)
        )
        user.conn.commit()
        # Calculer et mettre à jour la moyenne du vin
        cur.execute("SELECT nom, type FROM Bouteille WHERE id = ?", (bouteille_id,))
        row = cur.fetchone()
        if row:
            bouteille = cave.Bouteille(
                domaine=None,
                nom=row["nom"],
                type=row["type"],
                annee=None,
                region=None,
                prix=0,
                conn=user.conn
            )
            bouteille.calculerMoyenne()
        return redirect(url_for('index'))
    # GET: afficher le formulaire
    return render_template("archiver.html", bouteille_id=bouteille_id)


@app.route("/cave/creer", methods=['GET', 'POST'])
def creer_cave():
    user = get_user()
    if 'user' not in session:
        return redirect(url_for('login'))
    if request.method == 'POST':
        nom_cave = request.form.get('nom_cave')
        MaCave = cave.Cave(nom_cave)

        success = Utilisateur.sauvegarder_cave(user, MaCave)
        if success:
            flash(f"Cave '{nom_cave}' créée avec succès !", "success")
        else:
            flash("Vous avez déjà une cave, impossible d'en créer une nouvelle.", "error")

        return redirect(url_for('index'))
    return render_template("creatCave.html")


@app.route("/bouteille/creer", methods=['GET', 'POST'])
def creer_bouteille():
    user = get_user()
    if 'user' not in session:
        return redirect(url_for('login'))

    # Récupérer les étagères de l'utilisateur pour le formulaire
    cur = user.conn.cursor()
    cur.execute("SELECT * FROM Etagere WHERE proprietaire = ?", (user.login,))
    etageres = cur.fetchall()

    if request.method == 'POST':
        domaine = request.form.get('domaine')
        nom = request.form.get('nom')
        type = request.form.get('type')
        annee = request.form.get('annee')
        region = request.form.get('region')
        prix = request.form.get('prix')
        etagere_id = request.form.get('etagere_id')
        # Vérifier que l'étagère sélectionnée appartient bien à l'utilisateur
        cur.execute("SELECT * FROM Etagere WHERE id = ? AND proprietaire = ?", (etagere_id, user.login))
        if cur.fetchone() is None:
            flash("Étagère invalide")
            return redirect(url_for('creer_bouteille'))

        # Gestion de l'image
        file = request.files.get('image')
        image_path = None
        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            image_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
            file.save(image_path)

        MaBouteille = cave.Bouteille(
            domaine=domaine,
            nom=nom,
            type=type,
            annee=annee,
            region=region,
            prix=float(prix) if prix else 0.0,
            etiquette=image_path,
            etagere_id = int(etagere_id)
        )


        success = Utilisateur.sauvegarder_bouteille(user, MaBouteille)
        if success:
            flash(f"Bouteille créée avec succès !", "success")
        else:
            flash("Impossible d'ajouter la bouteille : étagère pleine.", "error")



        return redirect(url_for('index'))
    return render_template("creatBouteille.html", etageres=etageres)




@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        login = request.form['login']
        password = request.form['password']

        # Hash du mot de passe (comme dans ta classe Utilisateur)
        hashed = hashlib.sha256(password.encode()).hexdigest()

        conn = get_db_connection()
        user = conn.execute("SELECT * FROM Utilisateur WHERE login = ? AND mot_de_passe = ?",
                            (login, hashed)).fetchone()
        conn.close()

        if user:
            session['user'] = dict(user)
            flash(f"Bienvenue {user['prenom']} !", "success")
            return redirect(url_for('index'))
        else:
            flash("Identifiant ou mot de passe incorrect.", "danger")

    return render_template('login.html')


@app.route('/creer_etagere', methods=['GET', 'POST'])
def creer_etagere():
    user = get_user()
    if 'user' not in session:
        return redirect(url_for('login'))

    if request.method == 'POST':
        nom_etagere = request.form.get('nom_etagere')
        capacite = request.form.get('capacite')

        if not nom_etagere or not capacite:
            flash("Veuillez remplir tous les champs.")
            return redirect(url_for('creer_etagere'))

        try:
            capacite = int(capacite)
        except ValueError:
            flash("La capacité doit être un nombre.")
            return redirect(url_for('creer_etagere'))

        # Créer l'objet Etagere
        nouvelle_etagere = cave.Etagere(id_etagere=None, nom_etagere=nom_etagere, capacite=capacite, proprietaire=user.login)
        user.sauvegarder_etagere(nouvelle_etagere)

        flash(f"Étagère '{nom_etagere}' créée avec succès !")
        return redirect(url_for('index'))  # redirection vers page principale

    # GET : afficher le formulaire de création
    return render_template('creer_etagere.html')


@app.route("/etagere/supprimer/<int:etagere_id>")
def supprimer_etagere(etagere_id):
    user = get_user()

    success = user.supprimer_etagere(etagere_id)

    if success:
        flash("Étagère supprimée avec succès !", "success")
    else:
        flash("Impossible de supprimer l'étagère : elle contient encore des bouteilles.", "error")

    return redirect(url_for('index'))


@app.route('/logout')
def logout():
    session.pop('user', None)
    flash("Vous êtes déconnecté.", "info")
    return redirect(url_for('login'))


@app.route("/register", methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        nom = request.form.get('nom')
        prenom = request.form.get('prenom')
        login = request.form.get('login')
        mot_de_passe = request.form.get('mot_de_passe')
        mot_de_passe2 = request.form.get('mot_de_passe2')

        # Vérification des champs
        if not nom or not prenom or not login or not mot_de_passe or not mot_de_passe2:
            flash("Tous les champs sont requis", "error")
            return render_template('register.html')

        if mot_de_passe != mot_de_passe2:
            flash("Les mots de passe ne correspondent pas", "error")
            return render_template('register.html')

        # Création de l'objet utilisateur
        user = Utilisateur(
            id_utilisateur=None,
            nom=nom,
            prenom=prenom,
            login=login,
            mot_de_passe=mot_de_passe,
            conn=get_db_connection()
        )

        # Sauvegarde dans la BDD
        user.sauvegarder_user()
        flash("Compte créé avec succès", "success")
        return redirect(url_for('login'))

    return render_template('register.html')


if __name__ == "__main__":
    app.run(debug=True, port=5080)
