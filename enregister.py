from flask import Flask, request, render_template, redirect, url_for, flash, session
import os
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
import pyodbc





UPLOAD_FOLDER = "static/images/photos"
ALLOWED_EXTENSIONS = {"png", "jpg", "jpeg", "gif"}

def allowed_file(filename):
    EXTENSIONS_AUTORISÉES = {'png', 'jpg', 'jpeg', 'gif'}
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in EXTENSIONS_AUTORISÉES



def register(app):
    if request.method == 'POST':
        Nom = request.form['Nom']
        Prenoms = request.form['Prenoms']
        Telephone = request.form['Telephone']
        Adresse = request.form['Adresse']
        Email = request.form.get('email')
        Mot_de_pass = request.form.get('Mot_de_pass')
        Roles = request.form.get('Roles')
        Date_embauche = request.form['Date_embauche']
        
        # Traitement des images
        image_urls = []
        if "myfiles[]" in request.files:
            image_files = request.files.getlist("myfiles[]")
            for image_file in image_files:
                if image_file and allowed_file(image_file.filename):
                    filename = secure_filename(image_file.filename)
                    image_path = os.path.join(app.config["UPLOAD_FOLDER"], filename)
                    image_file.save(image_path)
                    image_urls.append(image_path)
        
        try:
            # Vérifier si l'email existe déjà
            connection = pyodbc.connect(app.config['SQL_SERVER_CONNECTION_STRING'])
            cursor = connection.cursor()
            cursor.execute("SELECT IdUtilisateurs FROM Utilisateurs WHERE Email=?", (Email,))
            existing_user = cursor.fetchone()

            if existing_user:
                flash('L\'adresse e-mail existe déjà. Veuillez choisir une autre adresse e-mail.', 'error')
                return redirect(url_for('register'))

            mot_de_passe_hache = generate_password_hash(Mot_de_pass)
            
            # Insertion dans la table Personnels
            cursor.execute(
                "INSERT INTO Personnels (Images, Nom, Prenoms, Telephone, Adresse, Date_embauche) VALUES (?, ?, ?, ?, ?, ?)",
                (",".join(image_urls) if image_urls else None, Nom, Prenoms, Telephone, Adresse, Date_embauche)
            )
            connection.commit()
            
            # Insertion dans la table Utilisateurs
            cursor.execute(
                "INSERT INTO Utilisateurs (Email, Mot_de_pass, Roles) VALUES (?, ?, ?)",
                (Email, mot_de_passe_hache, Roles)
            )
            connection.commit()

            cursor.execute("SELECT IdUtilisateurs FROM Utilisateurs WHERE Email = ?", (Email,))
            IdUtilisateurs = cursor.fetchone()[0]

            session['IdUtilisateurs'] = IdUtilisateurs
            session['user'] = Email

            return redirect(url_for('login'))
        
        except pyodbc.Error as e:
            flash(f'Une erreur est survenue lors de l\'enregistrement : {e}', 'error')
            return redirect(url_for('connexion'))

    return render_template("Utilisateurs/register.html")



def connexion(app):
    if request.method == 'POST':
        Email = request.form.get('email')
        Mot_de_pass = request.form.get('Mot_de_pass')
        Roles = request.form.get('Roles')
        
        if not Email or not Mot_de_pass or not Roles:
            flash("Veuillez saisir une adresse email, un mot de passe et un rôle.", "danger")
            return redirect(url_for('login'))

        try:
            connection = pyodbc.connect(app.config['SQL_SERVER_CONNECTION_STRING'])
            cursor = connection.cursor()
            cursor.execute("SELECT * FROM Utilisateurs WHERE Email = ?", (Email,))
            utilisateurs = cursor.fetchone()

            if utilisateurs and check_password_hash(utilisateurs[2], Mot_de_pass):
                session['IdUtilisateurs'] = utilisateurs[0]
                if utilisateurs[3] == Roles:
                    if Roles == 'Administrateur':
                        return redirect(url_for('accueiladmin'))
                    elif Roles == 'Assistant':
                        return redirect(url_for('accueilAssistant'))
                    elif Roles == 'Formateur':
                        return redirect(url_for('accueilFormateur'))
                    elif Roles == 'Apprenant':
                        return redirect(url_for('accueilApprenant'))
                else:
                    flash("Rôle incorrect.", "danger")
            else:
                flash("Adresse Email ou mot de passe incorrects.", "danger")

        except pyodbc.Error as e:
            flash(f'Une erreur est survenue lors de la connexion : {e}', 'error')
            return redirect(url_for('login'))

    return render_template('Utilisateurs/login.html')




# Définir vos routes et la logique de votre application

# Exemple de route utilisant matplotlib et seaborn
# @app.route('/visualization')
# def visualization():
#     # Générer des données fictives
#     data = pd.DataFrame({
#         'x': range(1, 101),
#         'y': [random.randint(1, 100) for _ in range(100)]
#     })
    
#     # Créer une figure matplotlib
#     plt.figure(figsize=(10, 5))
#     sns.lineplot(x='x', y='y', data=data)
#     plt.title('Sample Line Plot')
#     plt.xlabel('X-axis')
#     plt.ylabel('Y-axis')
    
#     # Sauvegarder la figure dans un objet IO
#     img = io.BytesIO()
#     plt.savefig(img, format='png')
#     img.seek(0)
    
#     # Retourner l'image comme réponse
#     return send_file(img, mimetype='image/png')





# @app.route("/login", methods=['GET', 'POST'])
# def login():
#     log = login()
#     return log

# @app.route("/", methods=['GET', 'POST'])
# def register():
#     Reg = register()
#     return Reg



