from flask import Flask, render_template, url_for, redirect, request, session, flash, make_response, send_file, jsonify , send_from_directory 
from functools import wraps
from datetime import datetime, timedelta
from werkzeug.utils import secure_filename
from werkzeug.security import generate_password_hash, check_password_hash
import pyodbc
import os
import pandas as pd
import random
import string
from flask_paginate import Pagination, get_page_parameter
import plotly.express as px
import matplotlib.pyplot as plt
import seaborn as sns


from enregister import *

# Vous pouvez maintenant utiliser function1, function2, etc. dans ce fichier


# Pour l'envoi des emails et des sms
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

# from emailling  import *
from sms import *

# Pour générer des données fictives
from faker import Faker
import csv

# Exporter vers PDF, Excel
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Table
from reportlab.lib import colors
import io
from openpyxl import Workbook
import tabula
import pdfplumber


# Initialisation de Faker
fake = Faker()

app = Flask(__name__)



# Configuration des dossiers de téléchargement

app.config['UPLOAD_FOLDER_IMAGES'] = 'static/uploads/images/'
app.config['UPLOAD_FOLDER_DIPLOMAS'] = 'static/uploads/diplomas/'
app.config['UPLOAD_FOLDER_ID'] = 'static/uploads/ids/'
os.makedirs(app.config['UPLOAD_FOLDER_IMAGES'], exist_ok=True)
os.makedirs(app.config['UPLOAD_FOLDER_DIPLOMAS'], exist_ok=True)
os.makedirs(app.config['UPLOAD_FOLDER_ID'], exist_ok=True)

UPLOAD_FOLDER = "static/images/photos"
ALLOWED_EXTENSIONS = {"png", "jpg", "jpeg", "gif"}
app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER

@app.route('/uploads/<filename>')
def uploaded_file(filename):
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)


def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in {'png', 'jpg', 'jpeg', 'gif'}


if not os.path.exists(app.config['UPLOAD_FOLDER']):
    os.makedirs(app.config['UPLOAD_FOLDER'])

app.secret_key = "messages"

# Configuration de la connexion à SQL Server
app.config["SQL_SERVER_CONNECTION_STRING"] = """
    Driver={SQL Server};
    Server=DESKTOP-VJVVU51\SQLEXPRESS;
    Database=BD_SOUTENANCE;
    Trusted_Connection=yes;
"""

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def get_db_connection():
    return pyodbc.connect(app.config['SQL_SERVER_CONNECTION_STRING'])






# *********************** enregistrement***********************




@app.route("/register", methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        Nom = request.form['Nom']
        Prenoms = request.form['Prenoms']
        Telephone = request.form['Telephone']
        Adresse = request.form['Adresse']
        Email = request.form['Email']
        Mot_de_pass = request.form['Mot_de_pass']
        Roles = request.form['Roles']
        Date_embauche = request.form['Date_embauche']
        Date_Creation = request.form['Date_Creation']
        Genre = request.form['Genre']
        
        Date_embauche = datetime.strptime(Date_embauche, '%Y-%m-%d')
        Date_Creation = datetime.strptime(Date_Creation, '%Y-%m-%d')
        
        # Assurez-vous que le dossier UPLOAD_FOLDER existe
        if not os.path.exists(app.config['UPLOAD_FOLDER']):
            os.makedirs(app.config['UPLOAD_FOLDER'])
        
        # Traitement des images
        image_urls = []
        if "myfiles[]" in request.files:
            image_files = request.files.getlist("myfiles[]")
            for image_file in image_files:
                if image_file and allowed_file(image_file.filename):
                    filename = secure_filename(image_file.filename)
                    image_path = os.path.join(app.config["UPLOAD_FOLDER"], filename)
                    image_file.save(image_path)
                    image_urls.append(url_for('uploaded_file', filename=filename))
        
        print(f"Nom: {Nom}")
        print(f"Prenoms: {Prenoms}")
        print(f"Telephone: {Telephone}")
        print(f"Adresse: {Adresse}")
        print(f"Email: {Email}")
        print(f"Mot_de_pass: {Mot_de_pass}")
        print(f"Roles: {Roles}")
        print(f"Date_embauche: {Date_embauche}")
        print(f"Date_Creation: {Date_Creation}")
        print(f"Image_urls: {image_urls}")
        print(f"Genre: {Genre}")
        
        try:
            connection = pyodbc.connect(app.config['SQL_SERVER_CONNECTION_STRING'])
            cursor = connection.cursor()
            
            cursor.execute("SELECT IdUtilisateurs FROM Utilisateurs WHERE Email=?", (Email,))
            existing_user = cursor.fetchone()
            
            if existing_user:
                print("L'adresse e-mail existe déjà. Veuillez choisir une autre adresse e-mail.")
                return redirect(url_for('register'))

            mot_de_passe_hache = generate_password_hash(Mot_de_pass)
            
            # Insertion dans la table Utilisateurs avec OUTPUT pour obtenir l'ID inséré
            query = """
                INSERT INTO Utilisateurs (Nom, Prenoms, Telephone, Adresse, Genre, Email, Mot_de_pass, Roles, Date_Creation)
                OUTPUT INSERTED.IdUtilisateurs
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """
            cursor.execute(query, (Nom, Prenoms, Telephone, Adresse, Genre, Email, mot_de_passe_hache, Roles, Date_Creation))
            utilisateur_id = cursor.fetchone()[0]
            print(f"Utilisateur Id: {utilisateur_id}")

            # Insertion dans la table Personnels avec l'ID de l'utilisateur
            cursor.execute(
                "INSERT INTO Personnels (Date_embauche, IdUtilisateurs) VALUES (?, ?)",
                (Date_embauche, utilisateur_id)
            )
            
            # Insertion des images
            for image_url in image_urls:
                cursor.execute(
                    "INSERT INTO Images (Image_Url, IdUtilisateurs) VALUES (?, ?)",
                    (image_url, utilisateur_id)
                )
            
            connection.commit()

        except Exception as e:
            print(f"Erreur lors de l'insertion dans la base de données: {e}")
            connection.rollback()  # Revertir les changements en cas d'erreur

        finally:
            cursor.close()
            connection.close()

        return render_template("Utilisateurs/login.html")

    return render_template("Utilisateurs/register.html")



@app.route("/", methods=['GET', 'POST'])
def connexion():
    if request.method == 'POST':
        Email = request.form.get('Email')
        Mot_de_pass = request.form.get('Mot_de_pass')
        
        # Vérifier si les champs Email et Mot_de_pass sont vides
        if not Email or not Mot_de_pass:
            flash("Veuillez saisir une adresse email et un mot de passe.", "danger")
            return redirect(url_for('connexion'))

        try:
            connection = pyodbc.connect(app.config['SQL_SERVER_CONNECTION_STRING'])
            cursor = connection.cursor()
            
            # Exécutez une requête SQL pour récupérer l'utilisateur avec l'e-mail donné
            cursor.execute("SELECT * FROM Utilisateurs WHERE Email = ?", (Email,))
            utilisateurs = cursor.fetchone()
            print(f"utilisateurs: {utilisateurs}")
           
            if utilisateurs and check_password_hash(utilisateurs[7], Mot_de_pass):
                session['IdUtilisateurs'] = utilisateurs[0]
                # session['role'] = utilisateurs[8]
                role = utilisateurs[8]
                
                if role == 'Personnels':
                    return redirect(url_for('dashbord'))
                elif role == 'Formateurs':
                    return redirect(url_for('accueilFormateurs'))
                elif role == 'Apprenants':
                    return redirect(url_for('accueilApprenants'))
                else:
                    
                    flash("Rôle incorrect.", "danger")
            else:
                flash("Adresse Email ou mot de passe incorrect.", "danger")
        
        except pyodbc.Error as e:
            flash(f'Une erreur est survenue lors de la connexion : {e}', 'error')
            return redirect(url_for('connexion'))

    return render_template('Utilisateurs/login.html')




# *************************  page de connexion(authentification ) **********************************



# @app.route("/")
# def home():
#     return render_template("base.html")




@app.route("/Agenda/")
def Agenda():
    # Vérifier si l'utilisateur est connecté
    if 'IdUtilisateurs' not in session:
        return redirect(url_for('login'))

    # Récupérer les informations de l'utilisateur connecté
    IdUser = session.get('IdUtilisateurs')
    connection = pyodbc.connect(app.config['SQL_SERVER_CONNECTION_STRING'])
    cursor = connection.cursor()
    cursor.execute("SELECT * FROM Utilisateurs WHERE IdUtilisateurs = ?", (IdUser,))
    Utilisateur = cursor.fetchone()

   
    return render_template('Agenda.html', Utilisateurs=Utilisateur)






@app.route("/dashbord/")
def dashbord():
    # Vérifier si l'utilisateur est connecté
    if 'IdUtilisateurs' not in session:
        return redirect(url_for('login'))
    IdUser = session.get('IdUtilisateurs')
    connection = pyodbc.connect(app.config['SQL_SERVER_CONNECTION_STRING'])
    cursor = connection.cursor()
    
    cursor.execute("SELECT * FROM Utilisateurs WHERE IdUtilisateurs = ?", (IdUser,))
    Utilisateur = cursor.fetchone()
    

    return render_template("/dashbord/dashbord.html", Utilisateurs=Utilisateur)


@app.route('/accueilFormateurs')
def accueilFormateurs():
    # Vérifier si l'utilisateur est connecté
    if 'IdUtilisateurs' not in session:
        return redirect(url_for('login'))
    IdUser = session.get('IdUtilisateurs')
    connection = pyodbc.connect(app.config['SQL_SERVER_CONNECTION_STRING'])
    cursor = connection.cursor()
    
    
    cursor.execute("SELECT * FROM Utilisateurs WHERE IdUtilisateurs = ?", (IdUser))
    Utilisateurs = cursor.fetchone()
    return render_template('/accueilFormateurs/dashbord_formateur.html',Utilisateurs=Utilisateurs)




@app.route('/accueilApprenants')
def accueilApprenants():
    # Vérifier si l'utilisateur est connecté
    if 'IdUtilisateurs' not in session:
        return redirect(url_for('login'))
    IdUser = session.get('IdUtilisateurs')
    connection = pyodbc.connect(app.config['SQL_SERVER_CONNECTION_STRING'])
    cursor = connection.cursor()
    
    
    cursor.execute("SELECT * FROM Utilisateurs WHERE IdUtilisateurs = ?", (IdUser))
    Utilisateurs = cursor.fetchone()
    return render_template('accueilApprenants/dashbord_apprenant.html',Utilisateurs=Utilisateurs)



# *************************  page de deconnexion **********************************


@app.route("/deconnexion", methods=['GET'])
def deconnexion():
    # Vérifier si l'utilisateur est connecté
    if 'IdUtilisateurs' not in session:
        return redirect(url_for('login'))
    
    IdUser = session.get('IdUtilisateurs')
    
    try:
        # Connexion à la base de données
        connection = pyodbc.connect(app.config['SQL_SERVER_CONNECTION_STRING'])
        cursor = connection.cursor()
        
        # Sélectionner l'utilisateur pour afficher un message de déconnexion
        cursor.execute("SELECT * FROM Utilisateurs WHERE IdUtilisateurs = ?", (IdUser,))
        Utilisateurs = cursor.fetchone()
        
        # Effacer toutes les clés de session
        session.clear()
        
        # Rediriger vers la page de connexion avec un message de succès
        flash("Vous avez été déconnecté avec succès.", "success")
        return redirect(url_for('connexion'))
    
    except pyodbc.Error as e:
        flash(f"Une erreur s'est produite lors de la déconnexion : {e}", "danger")
        return redirect(url_for('connexion'))
    
    finally:
        # Toujours fermer le curseur et la connexion à la base de données
        cursor.close()
        connection.close()
        
# *************************  fin-deconnexion **********************************








#*****************************PERSONNELS*******************************#

@app.route("/list-personnels", methods=['GET', 'POST'])
def listpersonnels():
    #   Vérifier si l'utilisateur est connecté
    if 'IdUtilisateurs' not in session:
        return redirect(url_for('login'))
    
    IdUser = session.get('IdUtilisateurs')
    connection = pyodbc.connect(app.config['SQL_SERVER_CONNECTION_STRING'])
    cursor = connection.cursor()
    
    # Récupérer les informations de l'utilisateur connecté
    cursor.execute("SELECT * FROM Utilisateurs WHERE IdUtilisateurs = ?", (IdUser,))
    Utilisateurs = cursor.fetchone()
    
    connection = pyodbc.connect(app.config['SQL_SERVER_CONNECTION_STRING'])
    cursor = connection.cursor()
    
    cursor.execute("""
        SELECT u.IdUtilisateurs, u.Nom, u.Prenoms, u.Roles, u.Adresse, u.Telephone, u.Email, 
               p.Date_embauche, i.Image_Url, u.Date_Creation, p.IdPersonnels
        FROM Personnels p
        JOIN Utilisateurs u ON p.IdUtilisateurs = u.IdUtilisateurs
        LEFT JOIN Images i ON u.IdUtilisateurs = i.IdUtilisateurs
    """)
    personnels = cursor.fetchall()
    cursor.close()
    connection.close()
    return render_template("Personnels/list-personnels.html", personnels=personnels, Utilisateurs= Utilisateurs)




@app.route("/ajout-personnels/", methods=['GET', 'POST'])
def ajoutpersonnels():
    if 'IdUtilisateurs' not in session:
        return redirect(url_for('login'))
    
    IdUser = session.get('IdUtilisateurs')
    connection = pyodbc.connect(app.config['SQL_SERVER_CONNECTION_STRING'])
    cursor = connection.cursor()
    
    cursor.execute("SELECT * FROM Utilisateurs WHERE IdUtilisateurs = ?", (IdUser,))
    Utilisateurs = cursor.fetchone()
    
    if request.method == 'POST':
        try:
            Nom = request.form['Nom']
            Prenoms = request.form['Prenoms']
            Email = request.form['Email']
            Mot_de_pass = request.form['Mot_de_pass']  
            Roles = request.form['Roles']
            Telephone = request.form['Telephone']
            Adresse = request.form['Adresse']
            Genre = request.form['Genre']
            Date_Creation = datetime.strptime(request.form['Date_Creation'], '%Y-%m-%d')
            Date_embauche = datetime.strptime(request.form['Date_embauche'], '%Y-%m-%d')
            
            # Vérifier si l'e-mail existe déjà
            cursor.execute("SELECT * FROM Utilisateurs WHERE Email = ?", (Email,))
            existing_user = cursor.fetchone()
            if existing_user:
                flash('Un utilisateur avec cet e-mail existe déjà', 'danger')
                return redirect(url_for('ajoutformateurs'))
            
            # Hacher le mot de passe
            hashed_password = generate_password_hash(Mot_de_pass)
            
            image_file = request.files['file']
            if image_file:
                image_url = f"static/images/{image_file.filename}"
                image_file.save(image_url)
            else:
                image_url = None
            
            print(f"Nom: {Nom}")
            print(f"Prenoms: {Prenoms}")
            print(f"date_embauche: {Date_embauche}")
            
            cursor.execute("""
                INSERT INTO Utilisateurs (Nom, Prenoms, Email, Mot_de_pass, Roles, Telephone, Adresse, Genre, Date_Creation)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, 
            (Nom, Prenoms, Email, hashed_password, Roles, Telephone, Adresse, Genre, Date_Creation))
            
            
            connection.commit()
            
            cursor.execute("SELECT IdUtilisateurs FROM Utilisateurs WHERE Email = ?", (Email,))
            new_user = cursor.fetchone()
            new_user_id = new_user.IdUtilisateurs
            
            cursor.execute("""
                INSERT INTO Personnels (Date_embauche, IdUtilisateurs)
                VALUES (?, ?)
            """, (Date_embauche, new_user_id))
            connection.commit()
            
            if image_url:
                cursor.execute("""
                    INSERT INTO Images (Image_Url, IdUtilisateurs)
                    VALUES (?, ?)
                """, (image_url, new_user_id))
                connection.commit()
            
            flash('Personnel ajouté avec succès', 'success')
            return redirect(url_for('listpersonnels'))
        
        except Exception as e:
            flash(f'Erreur lors de l\'ajout du personnel : {str(e)}', 'danger')
            connection.rollback()
        
        finally:
            cursor.close()
            connection.close()
    
    return render_template("Personnels/ajout-personnels.html", Utilisateurs=Utilisateurs)







@app.route("/modifie-personnels/<int:IdPersonnels>", methods=['GET', 'POST'])
def modifiepersonnels(IdPersonnels):
    # Vérifier si l'utilisateur est connecté
    if 'IdUtilisateurs' not in session:
        return redirect(url_for('login'))
    
    IdUser = session.get('IdUtilisateurs')
    connection = pyodbc.connect(app.config['SQL_SERVER_CONNECTION_STRING'])
    cursor = connection.cursor()
    
    cursor.execute("SELECT * FROM Utilisateurs WHERE IdUtilisateurs = ?", (IdPersonnels,))
    Utilisateurs = cursor.fetchone()
    
    # cursor.execute("SELECT * FROM Personnels WHERE IdPersonnels = ?", (IdPersonnels,))
    # personnel = cursor.fetchone()
    
    cursor.execute(
        """
        SELECT u.*, p.*
        FROM Personnels p
        JOIN Utilisateurs u ON p.IdUtilisateurs = u.IdUtilisateurs
        WHERE IdPersonnels = ?
        """, (IdPersonnels,)
    )
    info = cursor.fetchone()
    
    if not info:
        flash("Personnel introuvable", 'danger')
        cursor.close()
        connection.close()
        return redirect(url_for('listpersonnels'))
    
    if request.method == 'POST':
        # Récupérer les données du formulaire
        Nom = request.form['Nom']
        Prenoms = request.form['Prenoms']
        Email = request.form['Email']
        Mot_de_pass = request.form['Mot_de_pass']
        Roles = request.form['Roles']
        Telephone = request.form['Telephone']
        Adresse = request.form['Adresse']
        Genre = request.form['Genre']
        Date_Creation = datetime.strptime(request.form['Date_Creation'], '%Y-%m-%d')
        Date_embauche = datetime.strptime(request.form['Date_embauche'], '%Y-%m-%d')
        
        # Gestion du fichier image
        image_url = None
        if 'file' in request.files:
            image_file = request.files['file']
            if image_file and allowed_file(image_file.filename):
                filename = secure_filename(image_file.filename)
                image_path = os.path.join('static/images', filename)
                image_file.save(image_path)
                image_url = image_path
        
        try:
            # Mettre à jour les informations de l'utilisateur
            cursor.execute("""
                UPDATE Utilisateurs
                SET Nom = ?, Prenoms = ?, Email = ?, Mot_de_passe = ?, Roles = ?, Telephone = ?, Adresse = ?, Genre = ?, Date_Creation = ?
                WHERE IdUtilisateurs = ?
            """, (Nom, Prenoms, Email, Mot_de_pass, Roles, Telephone, Adresse, Genre, Date_Creation, IdPersonnels))
            
            # Mettre à jour les informations de la table Personnels
            cursor.execute("""
                UPDATE Personnels
                SET Date_embauche = ?
                WHERE IdPersonnels = ?
            """, (Date_embauche, IdPersonnels))
            
            # Mettre à jour l'image
            if image_url:
                cursor.execute("SELECT * FROM Images WHERE IdUtilisateurs = ?", (IdPersonnels,))
                image_record = cursor.fetchone()
                if image_record:
                    cursor.execute("""
                        UPDATE Images
                        SET Image_Url = ?
                        WHERE IdUtilisateurs = ?
                    """, (image_url, IdPersonnels))
                else:
                    cursor.execute("""
                        INSERT INTO Images (Image_Url, IdUtilisateurs)
                        VALUES (?, ?)
                    """, (image_url, IdPersonnels))
            
            connection.commit()
            flash('Personnel mis à jour avec succès', 'success')
            return redirect(url_for('listpersonnels'))
        
        except Exception as e:
            flash(f"Erreur lors de la mise à jour du personnel: {str(e)}", 'danger')
            connection.rollback()
        
        finally:
            cursor.close()
            connection.close()
    
    return render_template("Personnels/modifie-personnels.html", Utilisateurs=Utilisateurs, info=info)






@app.route("/suprime-personnels/<int:IdPersonnels>", methods=['GET', 'POST'])
def suprimepersonnels(IdPersonnels):
    # Vérifier si l'utilisateur est connecté
    if 'IdUtilisateurs' not in session:
        return redirect(url_for('login'))
    
    connection = pyodbc.connect(app.config['SQL_SERVER_CONNECTION_STRING'])
    cursor = connection.cursor()
    
    
    # Récupérer les informations du Personnels
    cursor.execute("SELECT * FROM Personnels WHERE IdPersonnels = ?", (IdPersonnels,))
    personnel = cursor.fetchone()
    if not personnel:
        flash("Personnels introuvable", 'danger')
        return redirect(url_for('listpersonnels'))

    if request.method == 'POST':
        try:
            # Supprimer l'utilisateur
            cursor.execute("DELETE FROM Utilisateurs WHERE IdUtilisateurs = ?", (IdPersonnels,))
            connection.commit()
            
            # Supprimer les informations liées dans la table Personnels
            cursor.execute("DELETE FROM Personnels WHERE IdUtilisateurs = ?", (IdPersonnels,))
            cursor.execute("DELETE FROM Utilisateurs WHERE IdUtilisateurs = ?", (personnel.IdUtilisateurs,))
            cursor.execute("DELETE FROM Images WHERE IdImages = ?", (personnel.IdImages,))
            connection.commit()
            
        except Exception as e:
            print(f"Erreur lors de la suppression du personnel: {e}")
            connection.rollback()
        
        finally:
            cursor.close()
            connection.close()
        
        return redirect(url_for('listpersonnels'))

    

# *************************Gestion du profile **********************************


@app.route("/profile/")
def profile():
     # Vérifier si l'utilisateur est connecté
    if 'IdUtilisateurs' not in session:
        return redirect(url_for('connexion'))
    
    IdUtilisateurs = session['IdUtilisateurs']
    connection = pyodbc.connect(app.config['SQL_SERVER_CONNECTION_STRING'])
    cursor = connection.cursor()

    # Récupérer les informations de l'utilisateur
    cursor.execute("SELECT * FROM Utilisateurs WHERE IdUtilisateurs = ?", (IdUtilisateurs,))
    Utilisateurs = cursor.fetchone()

    # Récupérer l'image de l'utilisateur depuis la table Images
    cursor.execute("SELECT * FROM Images WHERE IdUtilisateurs = ?", (IdUtilisateurs,))
    image_utilisateur = cursor.fetchone()

    connection.close()

    # Vérifier si l'utilisateur a une image
    if image_utilisateur:
        image_url = url_for('static', filename='images/' + image_utilisateur[1])
    else:
        image_url = url_for('static', filename='images/default.jpg')  # URL par défaut si aucune image n'est trouvée

    return render_template("Personnels/profile.html", Utilisateurs=Utilisateurs, ImageUrl=image_url)



@app.route("/modifie-profil", methods=['GET', 'POST'])
def modifieprofil():
    if 'IdUtilisateurs' not in session:
        return redirect(url_for('connexion'))
    
     # Obtenir l'identifiant de l'utilisateur connecté
    IdUser = session.get('IdUtilisateurs')
    IdUtilisateurs = session['IdUtilisateurs']
    connection = pyodbc.connect(app.config['SQL_SERVER_CONNECTION_STRING'])
    cursor = connection.cursor()
    
    # Sélectionner les informations de l'utilisateur connecté
    cursor.execute("SELECT * FROM Utilisateurs WHERE IdUtilisateurs = ?", (IdUser,))
    Utilisateurs = cursor.fetchone()

    # Récupérer les informations de l'utilisateur
    cursor.execute("SELECT * FROM Utilisateurs WHERE IdUtilisateurs = ?", (IdUtilisateurs,))
    IdUtilisateurs = cursor.fetchone()

    # Récupérer l'image de l'utilisateur depuis la table Images
    cursor.execute("SELECT * FROM Images WHERE IdImages = ?", [0])
    image_utilisateur = cursor.fetchone()

    connection.close()

    # Vérifier si l'utilisateur a une image
    if image_utilisateur:
        image_url = url_for('static', filename='images/' + image_utilisateur[1])
    else:
        image_url = url_for('static', filename='images/default.jpg')  # URL par défaut si aucune image n'est trouvée

    if request.method == 'POST':
        # Récupérer les données du formulaire
        Nom = request.form['Nom']
        Prenoms = request.form['Prenoms']
        Telephone = request.form['Telephone']
        Adresse = request.form['Adresse']
        Genre = request.form['Genre']

        # Mettre à jour les données de l'utilisateur dans la base de données
        cursor.execute("""
            UPDATE Utilisateurs
            SET Nom = ?, Prenoms = ?, Telephone = ?, Adresse = ?, Genre = ?
            WHERE IdUtilisateurs = ?
        """, (Nom, Prenoms, Telephone, Adresse, Genre, IdUtilisateurs))
        
        connection.commit()
        
        flash('Profil mis à jour avec succès.', 'success')
        return redirect(url_for('profile'))

    return render_template("Personnels/modifie-profile.html", Utilisateurs=Utilisateurs, ImageUrl=image_url)



# *************************fin du profile **********************************






#*****************************FORMATEURS*******************************#

@app.route("/list-formateurs/", methods=['GET', 'POST'])
def listformateurs():
    # Vérifier si l'utilisateur est connecté
    if 'IdUtilisateurs' not in session:
        return redirect(url_for('login'))
    
    # Obtenir l'identifiant de l'utilisateur connecté
    IdUser = session.get('IdUtilisateurs')
    
    # Connexion à la base de données
    connection = pyodbc.connect(app.config['SQL_SERVER_CONNECTION_STRING'])
    cursor = connection.cursor()
    
    # Sélectionner les informations de l'utilisateur connecté
    cursor.execute("SELECT * FROM Utilisateurs WHERE IdUtilisateurs = ?", (IdUser,))
    Utilisateurs = cursor.fetchone()
    
    # Sélectionner les formateurs et les informations associées
    # cursor.execute("""
    #     SELECT U.Nom, U.Prenoms, U.Genre, U.Telephone, U.Email, U.Adresse, I.Image_Url, P.Titre, U.IdUtilisateurs, IdFormateurs
    #     FROM Utilisateurs U
    #     JOIN Formateurs F ON U.IdUtilisateurs = F.IdUtilisateurs
    #     JOIN Images I ON U.IdUtilisateurs = I.IdUtilisateurs
    #     JOIN Programmes P ON F.IdProgrammes = P.IdProgrammes
    # """)
    # formateurs = cursor.fetchall()
    
    
    cursor.execute("""
        SELECT U.Nom, U.Prenoms, U.Genre, U.Telephone, U.Email, U.Adresse, I.Image_Url, P.Titre, U.IdUtilisateurs, F.IdFormateurs
        FROM Utilisateurs U
        JOIN Formateurs F ON U.IdUtilisateurs = F.IdUtilisateurs
        JOIN Images I ON U.IdUtilisateurs = I.IdUtilisateurs
        JOIN Programmes P ON F.IdProgrammes = P.IdProgrammes
    """)
    formateurs = cursor.fetchall()
    
    # Fermer la connexion à la base de données
    cursor.close()
    connection.close()
    
    # Rendre le template avec les données des utilisateurs et formateurs
    return render_template("/Formateurs/list-formateurs.html", Utilisateurs=Utilisateurs, formateurs=formateurs)





@app.route("/ajout-formateurs/", methods=['GET', 'POST'])
def ajoutformateurs():
    if 'IdUtilisateurs' not in session:
        return redirect(url_for('login'))
    
    IdUser = session.get('IdUtilisateurs')
    connection = pyodbc.connect(app.config['SQL_SERVER_CONNECTION_STRING'])
    cursor = connection.cursor()
    
    cursor.execute("SELECT * FROM Utilisateurs WHERE IdUtilisateurs = ?", (IdUser,))
    Utilisateurs = cursor.fetchone()
    
    cursor.execute("SELECT IdProgrammes, Titre FROM Programmes")
    Programmes = cursor.fetchall()

    if request.method == 'POST':
        try:
            # Extraire les données du formulaire
            Nom = request.form['Nom']
            Prenoms = request.form['Prenoms']
            Genre = request.form['Genre']
            Telephone = request.form['Telephone']
            Adresse = request.form['Adresse']
            Email = request.form['Email']
            Mot_de_pass = request.form['Mot_de_pass']
            confirmer_Mot_de_pass = request.form['confirmer_Mot_de_pass']
            Roles = request.form['Roles']
            Date_Creation = datetime.strptime(request.form['Date_Creation'], '%Y-%m-%d')
            Annees_Experiences = request.form['Annees_Experiences']
            IdProgrammes = request.form['IdProgrammes']

            
            # Vérifier la confirmation du mot de passe
            if Mot_de_pass != confirmer_Mot_de_pass:
                flash('Les mots de passe ne correspondent pas', 'danger')
                return redirect(url_for('ajoutformateurs'))
            
            # Vérifier si l'e-mail existe déjà
            cursor.execute("SELECT * FROM Utilisateurs WHERE Email = ?", (Email,))
            existing_user = cursor.fetchone()
            if existing_user:
                flash('Un utilisateur avec cet e-mail existe déjà', 'danger')
                return redirect(url_for('ajoutformateurs'))
            
            # Hacher le mot de passe
            hashed_password = generate_password_hash(Mot_de_pass)
            
            # Gérer les fichiers
            diplome_file = request.files['Diplomes']
            if diplome_file:
                diplome_filename = os.path.join(app.config['UPLOAD_FOLDER'], diplome_file.filename)
                diplome_file.save(diplome_filename)
            else:     
                diplome_filename = None
            
            image_file = request.files['Images']
            if image_file:
                image_url = os.path.join(app.config['UPLOAD_FOLDER'], image_file.filename)
                image_file.save(image_url)
            else:    
                image_url = None
                   
            
            print(f"Nom: {Nom}")
            print(f"Prenoms: {Prenoms}")
            print(f"Annees_Experiences: {Annees_Experiences}")
            print(f"diplome_filename: {diplome_filename}")
            print(f"image_url: {image_url}")

            # Insérer dans la table Utilisateurs
            cursor.execute("""
                INSERT INTO Utilisateurs (Nom, Prenoms, Genre, Telephone, Adresse, Email, Mot_de_pass, Roles, Date_Creation)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (Nom, Prenoms, Genre, Telephone, Adresse, Email, hashed_password, Roles, Date_Creation))
            connection.commit()

            cursor.execute("SELECT IdUtilisateurs FROM Utilisateurs WHERE Email = ?", (Email,))
            new_user = cursor.fetchone()
            new_user_id = new_user.IdUtilisateurs
            
            # Insérer dans la table Formateurs
            cursor.execute("""
                INSERT INTO Formateurs (Diplomes, Annees_Experiences, IdProgrammes, IdUtilisateurs)
                VALUES (?, ?, ?, ?)
            """, (diplome_filename, Annees_Experiences, IdProgrammes, new_user_id))
            connection.commit()
            
            # Insérer dans la table Images
            if image_url:
                cursor.execute("""
                    INSERT INTO Images (Image_Url, IdUtilisateurs)
                    VALUES (?, ?)
                """, (image_url, new_user_id))
                connection.commit()
                
            print(f"diplome_filename: {diplome_filename}")
            print(f"image_url: {image_url}")
            
            flash('Formateur ajouté avec succès', 'success')
            return redirect(url_for('listformateurs'))
        
        except Exception as e:
            flash(f'Erreur lors de l\'ajout du formateur : {str(e)}', 'danger')
            connection.rollback()
        finally:
            cursor.close()
            connection.close()
    
    return render_template("Formateurs/ajout-formateurs.html", Utilisateurs=Utilisateurs, Programmes=Programmes)



@app.route("/modifie-formateurs/<int:IdFormateurs>", methods=['GET', 'POST'])
def modifieformateurs(IdFormateurs):
    print(f"IdFormateurs: {IdFormateurs}")
    # Vérifier si l'utilisateur est connecté
    if 'IdUtilisateurs' not in session:
        return redirect(url_for('login'))
    IdUser = session.get('IdUtilisateurs')
    print(IdUser)
    
    connection = pyodbc.connect(app.config['SQL_SERVER_CONNECTION_STRING'])
    cursor = connection.cursor()
    
    cursor.execute("SELECT * FROM Utilisateurs WHERE IdUtilisateurs = ?", (IdUser,))
    Utilisateurs = cursor.fetchone()

    # # Récupérer les informations du formateur spécifique à modifier
    # cursor.execute("SELECT * FROM Formateurs WHERE IdFormateurs = ?", (IdFormateurs,))
    # formateurs = cursor.fetchone()
    
    
    cursor.execute(
        """
        SELECT F.*, U.*, I.*
        FROM Formateurs F
        JOIN Utilisateurs U ON F.IdUtilisateurs = U.IdUtilisateurs
        JOIN Images I ON F.IdUtilisateurs = I.IdUtilisateurs
        WHERE F.IdFormateurs = ?

        """, (IdFormateurs,)
    )
    formateurs = cursor.fetchone()
    
    if not formateurs:
        flash("Formateur introuvable", 'danger')
        return redirect(url_for('listformateurs'))

    # Récupérer les informations de l'utilisateur associé
    cursor.execute("SELECT * FROM Utilisateurs WHERE IdUtilisateurs = ?", (IdFormateurs,))
    Utilisateurs = cursor.fetchone()

    if request.method == 'POST':
        try:
            # Extraire les données du formulaire
            Nom = request.form['Nom']
            Prenoms = request.form['Prenoms']
            Genre = request.form['Genre']
            Telephone = request.form['Telephone']
            Adresse = request.form['Adresse']
            Email = request.form['Email']
            Mot_de_pass = request.form['Mot_de_pass']
            confirmer_Mot_de_pass = request.form['confirmer_Mot_de_pass']
            Roles = request.form['Roles']
            Date_Creation = datetime.strptime(request.form['Date_Creation'], '%Y-%m-%d')
            Annees_Experiences = request.form['Annees_Experiences']
            IdProgrammes = request.form['IdProgrammes']
            
            # Vérifier la confirmation du mot de passe
            if Mot_de_pass != confirmer_Mot_de_pass:
                flash('Les mots de passe ne correspondent pas', 'danger')
                return redirect(url_for('modifieformateurs', IdFormateurs=IdFormateurs))

            # Hacher le mot de passe si changé
            if Mot_de_pass:
                hashed_password = generate_password_hash(Mot_de_pass)
            else:
                hashed_password = Utilisateurs.Mot_de_pass
            
            # Gérer les fichiers
            diplome_file = request.files['Diplomes']
            diplome_filename = formateurs.Diplomes
            if diplome_file:
                diplome_filename = os.path.join(app.config['UPLOAD_FOLDER'], diplome_file.filename)
                diplome_file.save(diplome_filename)
            
            image_file = request.files['Images']
            image_filename = None
            if image_file:
                image_filename = os.path.join(app.config['UPLOAD_FOLDER'], image_file.filename)
                image_file.save(image_filename)

            # Mettre à jour la table Utilisateurs
            cursor.execute("""
                UPDATE Utilisateurs SET Nom = ?, Prenoms = ?, Genre = ?, Telephone = ?, Adresse = ?, Email = ?, Mot_de_pass = ?, Roles = ?, Date_Creation = ?,
                WHERE IdUtilisateurs = ?
            """, (Nom, Prenoms, Genre, Telephone, Adresse, Email, hashed_password, Roles, Date_Creation,  IdFormateurs))
            connection.commit()
            
            print(f"Prenoms: {Prenoms}")

            # Mettre à jour la table Formateurs
            cursor.execute("""
                UPDATE Formateurs SET Diplomes = ?, Annees_Experiences = ?, IdProgrammes = ?
                WHERE IdFormateurs = ?
            """, (diplome_filename, Annees_Experiences, IdProgrammes, IdFormateurs))
            connection.commit()
            
            print(f"Annees_Experiences: {Annees_Experiences}")

            # Mettre à jour la table Images si une nouvelle image est téléchargée
            if image_filename:
                cursor.execute("""
                    UPDATE Images SET Image_Url = ?
                    WHERE IdUtilisateurs = ?
                """, (image_filename, IdFormateurs))
                connection.commit()
            
            flash('Formateur modifié avec succès', 'success')
            return redirect(url_for('listformateurs'))

        except Exception as e:
            flash(f'Erreur lors de la modification du formateur : {str(e)}', 'danger')
            connection.rollback()
        finally:
            cursor.close()
            connection.close()   
        return redirect(url_for('listformateurs'))
    

    cursor.execute("SELECT IdProgrammes, Titre FROM Programmes")
    Programmes = cursor.fetchall()
    
    return render_template("Formateurs/modifie-formateurs.html", Utilisateurs=Utilisateurs, formateurs=formateurs, Programmes=Programmes, IdFormateurs=IdFormateurs)





@app.route("/suprime-formateurs/<int:IdFormateurs>", methods=['GET', 'POST'])
def suprimeformateurs(IdFormateurs):
    # Vérifier si l'utilisateur est connecté
    if 'IdUtilisateurs' not in session:
        return redirect(url_for('login'))
    IdUser = session.get('IdUtilisateurs')
    
    connection = pyodbc.connect(app.config['SQL_SERVER_CONNECTION_STRING'])
    cursor = connection.cursor()

    # Vérifier les informations de l'utilisateur
    cursor.execute("SELECT * FROM Utilisateurs WHERE IdUtilisateurs = ?", (IdUser,))
    Utilisateurs = cursor.fetchone()

    # Récupérer les informations du formateur
    cursor.execute("""
        SELECT U.Nom, U.Prenoms, U.Genre, U.Telephone, U.Email, U.Adresse, F.Annees_Experiences, I.Image_Url, P.Titre, U.IdUtilisateurs, F.IdFormateurs
        FROM Utilisateurs U
        JOIN Formateurs F ON U.IdUtilisateurs = F.IdUtilisateurs
        LEFT JOIN Images I ON U.IdUtilisateurs = I.IdUtilisateurs
        JOIN Programmes P ON F.IdProgrammes = P.IdProgrammes
        WHERE F.IdFormateurs = ?
    """, (IdFormateurs,))
    formateurs = cursor.fetchone()

    if not formateurs:
        flash("Formateur introuvable", 'danger')
        cursor.close()
        connection.close()
        return redirect(url_for('listformateurs'))

    if request.method == 'POST':
        try:
            # Supprimer le formateur de la base de données
            cursor.execute("DELETE FROM Formateurs WHERE IdFormateurs = ?", (IdFormateurs,))
            cursor.execute("DELETE FROM Utilisateurs WHERE IdUtilisateurs = ?", (formateurs.IdUtilisateurs,))
            cursor.execute("DELETE FROM Images WHERE IdUtilisateurs = ?", (formateurs.IdUtilisateurs,))
            connection.commit()

            flash('Formateur supprimé avec succès', 'success')
            return redirect(url_for('listformateurs'))
        
        except Exception as e:
            flash(f'Erreur lors de la suppression du formateur : {str(e)}', 'danger')
            connection.rollback()
        finally:
            cursor.close()
            connection.close()
        
        return redirect(url_for('listformateurs'))

    cursor.close()
    connection.close()
    return redirect(url_for('listformateurs'))







@app.route("/profile-formateurs/<int:IdFormateurs>", methods=['GET'])
def profileformateurs(IdFormateurs):
    # Vérifier si l'utilisateur est connecté
    if 'IdUtilisateurs' not in session:
        return redirect(url_for('login'))
    IdUser = session.get('IdUtilisateurs')
    
    connection = pyodbc.connect(app.config['SQL_SERVER_CONNECTION_STRING'])
    cursor = connection.cursor()

    # Récupérer les informations du formateur
    cursor.execute("SELECT * FROM Formateurs WHERE IdFormateurs = ?", (IdFormateurs,))
    formateur = cursor.fetchone()
    if not formateur:
        flash("Formateur introuvable", 'danger')
        return redirect(url_for('listformateurs'))

    # Récupérer les informations de l'utilisateur associé
    cursor.execute("SELECT * FROM Utilisateurs WHERE IdUtilisateurs = ?", (formateur.IdUtilisateurs,))
    Utilisateurs = cursor.fetchone()

    return render_template("Formateurs/profile-formateurs.html", Utilisateurs= Utilisateurs, Formateur= formateur)


#*****************************FIN-FORMATEURS*******************************#



#************************************************APPRENANTS**************************************************#

@app.route("/list-apprenants/", methods=['GET', 'POST'])
def listapprenants():
    # Vérifier si l'utilisateur est connecté
    if 'IdUtilisateurs' not in session:
        return redirect(url_for('login'))
    
    # Obtenir l'identifiant de l'utilisateur connecté
    IdUser = session.get('IdUtilisateurs')
    
    # Connexion à la base de données
    connection = pyodbc.connect(app.config['SQL_SERVER_CONNECTION_STRING'])
    cursor = connection.cursor()
    
    # Sélectionner les informations de l'utilisateur connecté
    cursor.execute("SELECT * FROM Utilisateurs WHERE IdUtilisateurs = ?", (IdUser,))
    Utilisateurs = cursor.fetchone()

    try:
        # Sélectionner les Apprenants et les informations associées
        cursor.execute("""
            SELECT U.Nom, U.Prenoms, U.Genre, U.Telephone, U.Email, A.Niveau_Etudes, I.Image_Url, P.Titre, U.IdUtilisateurs, A.IdApprenants
            FROM Utilisateurs U
            JOIN Apprenants A ON U.IdUtilisateurs = A.IdUtilisateurs
            LEFT JOIN Images I ON U.IdUtilisateurs = I.IdUtilisateurs
            JOIN Programmes P ON A.IdProgrammes = P.IdProgrammes
        """)
        apprenant = cursor.fetchall()

    except pyodbc.Error as e:
        print("Erreur lors de la récupération des données :", e)
        apprenant = []
        # return redirect(url_for('error_page')) 

    finally:
        # Fermer la connexion à la base de données
        cursor.close()
        connection.close()

    return render_template("/Apprenants/list-apprenants.html", Utilisateurs=Utilisateurs, apprenant=apprenant)



@app.route("/ajout-apprenants/", methods=['GET', 'POST'])
def ajoutapprenants():
    if 'IdUtilisateurs' not in session:
        return redirect(url_for('login'))
    
    IdUser = session.get('IdUtilisateurs')
    connection = pyodbc.connect(app.config['SQL_SERVER_CONNECTION_STRING'])
    cursor = connection.cursor()
    
    cursor.execute("SELECT * FROM Utilisateurs WHERE IdUtilisateurs = ?", (IdUser,))
    Utilisateurs = cursor.fetchone()
    
    cursor.execute("SELECT IdProgrammes, Titre FROM Programmes")
    Programmes = cursor.fetchall()
    
    if request.method == 'POST':
        try:
            # Récupérer les données du formulaire
            Nom = request.form['Nom']
            Prenoms = request.form['Prenoms']
            Email = request.form['Email']
            Mot_de_pass = request.form['Mot_de_pass']
            confirmer_Mot_de_pass = request.form['confirmer_Mot_de_pass']
            Roles = request.form['Roles']
            Telephone = request.form['Telephone']
            Adresse = request.form['Adresse']
            Genre = request.form['Genre']
            Date_Creation = datetime.strptime(request.form['Date_Creation'], '%Y-%m-%d')
            
            Niveau_Etudes = request.form['Niveau_Etudes']
            Age = request.form['Age']
            Nom_Complet_Parent = request.form['Nom_Complet_Parent']
            Telephone_Parent = request.form['Telephone_Parent']
            Adresse_Parent = request.form['Adresse_Parent']
            IdProgrammes = request.form['IdProgrammes']
            
            Images = request.files['Images']
            Piece_Identite = request.files['Piece_Identite']
            Diplomes = request.files['Diplomes']

            # Traitement des fichiers téléchargés
            piece_identite_url = f'static/uploads/{Piece_Identite.filename}'
            Piece_Identite.save(piece_identite_url)

            diplomes_url = f'static/uploads/{Diplomes.filename}'
            Diplomes.save(diplomes_url)

            image_url = None
            if Images:
                image_url = f'static/uploads/{Images.filename}'
                Images.save(image_url)

            # Vérifier la confirmation du mot de passe
            if Mot_de_pass != confirmer_Mot_de_pass:
                flash('Les mots de passe ne correspondent pas', 'danger')
                return redirect(url_for('ajoutapprenants'))

            # Vérifier si l'e-mail existe déjà
            cursor.execute("SELECT * FROM Utilisateurs WHERE Email = ?", (Email,))
            existing_user = cursor.fetchone()
            if existing_user:
                flash('Un utilisateur avec cet e-mail existe déjà', 'danger')
                return redirect(url_for('ajoutapprenants'))

            # Hacher le mot de passe
            hashed_password = generate_password_hash(Mot_de_pass)
            
            
            print(f"Nom: {Nom}")
            print(f"Prenoms: {Prenoms}")
            print(f"Niveau_Etudes: {Niveau_Etudes}")
            print(f"Nom_Complet_Parent: {Nom_Complet_Parent}")

            # Insérer les informations de l'utilisateur
            cursor.execute("""
                INSERT INTO Utilisateurs (Nom, Prenoms, Email, Mot_de_pass, Roles, Telephone, Adresse, Genre, Date_Creation)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (Nom, Prenoms, Email, hashed_password, Roles, Telephone, Adresse, Genre, Date_Creation))
            
            connection.commit()
            
            cursor.execute("SELECT IdUtilisateurs FROM Utilisateurs WHERE Email = ?", (Email,))
            new_user = cursor.fetchone()
            new_user_id = new_user.IdUtilisateurs
            
            # Insérer les informations de l'apprenant
            cursor.execute("""
                INSERT INTO Apprenants (Niveau_Etudes,Piece_Identite, Diplomes, Age, Nom_Complet_Parent,Telephone_Parent, Adresse_Parent, IdProgrammes, IdUtilisateurs )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (Niveau_Etudes, piece_identite_url, diplomes_url, Age, Nom_Complet_Parent, Telephone_Parent, Adresse_Parent, IdProgrammes, new_user_id ))
            connection.commit()
            
            if image_url:
                cursor.execute("""
                    INSERT INTO Images (Image_Url, IdUtilisateurs)
                    VALUES (?, ?)
                """, (image_url, new_user_id))
                connection.commit()
            
            flash('Apprenant ajouté avec succès', 'success')
            return redirect(url_for('listapprenants'))
        
        except Exception as e:
            flash(f'Erreur lors de l\'ajout de l\'apprenant : {str(e)}', 'danger')
            connection.rollback()
        
        finally:
            cursor.close()
            connection.close()
            
        print(f"piece_identite_url: {piece_identite_url}")
    
    return render_template("Apprenants/ajout-apprenants.html", Utilisateurs=Utilisateurs,Programmes=Programmes)






@app.route("/modifie-apprenants/<int:IdApprenants>", methods=['GET', 'POST'])
def modifieapprenants(IdApprenants):
    # Vérifier si l'utilisateur est connecté
    if 'IdUtilisateurs' not in session:
        return redirect(url_for('login'))
    
    IdUser = session.get('IdUtilisateurs')
    connection = pyodbc.connect(app.config['SQL_SERVER_CONNECTION_STRING'])
    cursor = connection.cursor()
    
    cursor.execute("SELECT * FROM Utilisateurs WHERE IdUtilisateurs = ?", (IdUser,))
    Utilisateurs = cursor.fetchone()
    
    cursor.execute("SELECT IdProgrammes, Titre FROM Programmes")
    Programmes = cursor.fetchall()
    
    
    cursor.execute(
        """
        SELECT A.*, U.*, I.*
        FROM Apprenants A
        JOIN Utilisateurs U ON A.IdUtilisateurs = U.IdUtilisateurs
        JOIN Images I ON A.IdUtilisateurs = I.IdUtilisateurs
        WHERE A.IdApprenants = ?

        """, (IdApprenants,)
    )
    apprenant = cursor.fetchone()

    if request.method == 'POST':
        try:
            Nom = request.form['Nom']
            Prenoms = request.form['Prenoms']
            Email = request.form['Email']
            Roles = request.form['Roles']
            Telephone = request.form['Telephone']
            Adresse = request.form['Adresse']
            Genre = request.form['Genre']
            Date_Creation = datetime.strptime(request.form['Date_Creation'], '%Y-%m-%d')
            Niveau_Etudes = request.form['Niveau_Etudes']
            Age = request.form['Age']
            Nom_Complet_Parent = request.form['Nom_Complet_Parent']
            Telephone_Parent = request.form['Telephone_Parent']
            Adresse_Parent = request.form['Adresse_Parent']
            IdProgrammes = request.form['IdProgrammes']
            Piece_Identite = request.files['Piece_Identite']
            Diplomes = request.files['Diplomes']
            Images = request.files['Images']

            # Convertir Date_Creation au format approprié pour SQL Server
            Date_Creation = datetime.strptime(Date_Creation, '%Y-%m-%d').strftime('%Y-%m-%d %H:%M:%S')

            # Traitement des fichiers téléchargés
            piece_identite_url = apprenant.Piece_Identite
            if Piece_Identite:
                piece_identite_url = f'static/uploads/{Piece_Identite.filename}'
                Piece_Identite.save(piece_identite_url)

            diplomes_url = apprenant.Diplomes
            if Diplomes:
                diplomes_url = f'static/uploads/{Diplomes.filename}'
                Diplomes.save(diplomes_url)

            image_url = apprenant.Images
            if Images:
                image_url = f'static/uploads/{Images.filename}'
                Images.save(image_url)

        # Mise à jour des informations utilisateur
            cursor.execute("""
                UPDATE Utilisateurs 
                SET Nom = ?, Prenoms = ?, Email = ?, Roles = ?, Telephone = ?, Adresse = ?, Genre = ?, Date_Creation = ?
                WHERE IdUtilisateurs = ?
            """, (Nom, Prenoms, Email, Roles, Telephone, Adresse, Genre, Date_Creation, IdApprenants))
            
            connection.commit()

        # Mise à jour des informations apprenant
            cursor.execute("""
                UPDATE Apprenants 
                SET Niveau_Etudes = ?, Piece_Identite = ?, Diplomes = ?, Age = ?, Nom_Complet_Parent = ?, Telephone_Parent = ?, Adresse_Parent = ?, IdProgrammes = ?
                WHERE IdUtilisateurs = ?
            """, (Niveau_Etudes, piece_identite_url, diplomes_url, Age, Nom_Complet_Parent, Telephone_Parent, Adresse_Parent, IdProgrammes, IdApprenants))
            connection.commit()

            if image_url:
                cursor.execute("""
                    UPDATE Images 
                    SET Image_Url = ?
                    WHERE IdUtilisateurs = ?
                """, (image_url, IdApprenants))
                connection.commit()

            flash('Apprenant modifié avec succès', 'success')
            return redirect(url_for('listapprenants'))

        except Exception as e:
            flash(f'Erreur lors de la modification de l\'apprenant : {str(e)}', 'danger')
            connection.rollback()

        finally:
            cursor.close()
            connection.close()
    return render_template("Apprenants/modifie-apprenants.html", Utilisateurs=Utilisateurs,Programmes=Programmes, apprenant=apprenant, IdApprenants=IdApprenants)





@app.route("/suprime-apprenants/<int:IdApprenants>", methods=['GET', 'POST'])
def suprimeapprenants(IdApprenants):
    # Vérifier si l'utilisateur est connecté
    if 'IdUtilisateurs' not in session:
        return redirect(url_for('login'))
    IdUser = session.get('IdUtilisateurs')
    
    connection = pyodbc.connect(app.config['SQL_SERVER_CONNECTION_STRING'])
    cursor = connection.cursor()

    # Vérifier les informations de l'utilisateur
    cursor.execute("SELECT * FROM Utilisateurs WHERE IdUtilisateurs = ?", (IdUser,))
    Utilisateurs = cursor.fetchone()

    # Récupérer les informations de l'apprenant
    cursor.execute("""
        SELECT U.Nom, U.Prenoms, U.Genre, U.Telephone, U.Email, A.Niveau_Etudes, I.Image_Url, P.Titre, U.IdUtilisateurs, A.IdApprenants
        FROM Utilisateurs U
        JOIN Apprenants A ON U.IdUtilisateurs = A.IdUtilisateurs
        LEFT JOIN Images I ON U.IdUtilisateurs = I.IdUtilisateurs
        JOIN Programmes P ON A.IdProgrammes = P.IdProgrammes
        WHERE A.IdApprenants = ?
    """, (IdApprenants,))
    apprenant = cursor.fetchone()

    if not apprenant:
        flash("Apprenant introuvable", 'danger')
        cursor.close()
        connection.close()
        return redirect(url_for('listapprenants'))

    if request.method == 'POST':
        try:
            # Supprimer l'apprenant de la base de données
            cursor.execute("DELETE FROM Apprenants WHERE IdApprenants = ?", (IdApprenants,))
            cursor.execute("DELETE FROM Utilisateurs WHERE IdUtilisateurs = ?", (apprenant.IdUtilisateurs,))
            cursor.execute("DELETE FROM Images WHERE IdUtilisateurs = ?", (apprenant.IdUtilisateurs,))
            connection.commit()

            flash('Apprenant supprimé avec succès', 'success')
            return redirect(url_for('listapprenants'))
        
        except Exception as e:
            flash(f'Erreur lors de la suppression de l\'apprenant : {str(e)}', 'danger')
            connection.rollback()
        finally:
            cursor.close()
            connection.close()
        
        return redirect(url_for('listapprenants'))

    cursor.close()
    connection.close()
    return redirect(url_for('listapprenants'))














@app.route("/infos-apprenants/")
def infosapprenants():
    # Vérifier si l'utilisateur est connecté
    if 'IdUtilisateurs' not in session:
        return redirect(url_for('login'))
    IdUser = session.get('IdUtilisateurs')
    connection = pyodbc.connect(app.config['SQL_SERVER_CONNECTION_STRING'])
    cursor = connection.cursor()
    
    
    cursor.execute("SELECT * FROM Utilisateurs WHERE IdUtilisateurs = ?", (IdUser))
    Utilisateur = cursor.fetchone()
    return render_template("/Apprenants/infos-apprenants.html",Utilisateurs=Utilisateur)


#***************************** Avis de l'Apprenant*******************************#


@app.route("/monespace/")
def monespace():
    # Vérifier si l'utilisateur est connecté
    if 'IdUtilisateurs' not in session:
        return redirect(url_for('login'))

    IdUser = session.get('IdUtilisateurs')
    connection = pyodbc.connect(app.config['SQL_SERVER_CONNECTION_STRING'])
    cursor = connection.cursor()
    
    # Récupérer les informations de l'utilisateur connecté
    cursor.execute("SELECT * FROM Utilisateurs WHERE IdUtilisateurs = ?", IdUser)
    Utilisateurs = cursor.fetchone()

    # Récupérer les programmes associés à l'utilisateur
    cursor.execute("""
        SELECT P.IdProgrammes, P.Titre, P.DetailsProgrammes, P.Duree_programmes, P.Date_debut, P.Date_fin
        FROM Programmes P
        INNER JOIN Apprenants A ON P.IdProgrammes = A.IdProgrammes
        WHERE A.IdUtilisateurs = ?
    """, IdUser)
    programmes = cursor.fetchall()

    # Récupérer les formateurs associés à chaque programme
    formateurs = []
    for programme in programmes:
        cursor.execute("""
            SELECT U.IdUtilisateurs, U.Nom, U.Prenoms, U.Email, U.Telephone, F.IdProgrammes
            FROM Utilisateurs U
            INNER JOIN Formateurs F ON U.IdUtilisateurs = F.IdUtilisateurs
            WHERE F.IdProgrammes = ?
        """, programme.IdProgrammes)
        formateurs += cursor.fetchall()

    return render_template('/Apprenants/mon_espace.html', Utilisateurs=Utilisateurs, programmes=programmes, formateurs=formateurs)

@app.route("/analyze_comment", methods=['POST'])
def analyze_comment():
    data = request.json
    comment = data['comment']
    # Analyse de sentiment fictive pour démonstration
    sentiment = "Positif" if "good" in comment.lower() else "Négatif"
    return jsonify({'sentiment': sentiment})





@app.route('/avisprogramme')
def avisprogramme():
    # avis = request.form['avis_programme']
    # Sauvegardez l'avis sur le programme dans la base de données
    flash('Votre avis sur le programme a été soumis avec succès', 'success')
    return redirect(url_for('mon_espace'))

@app.route('/avisformateur')
def avisformateur():
    # avis = request.form['avis_formateur']
    # Sauvegardez l'avis sur le formateur dans la base de données
    flash('Votre avis sur le formateur a été soumis avec succès', 'success')
    return redirect(url_for('monespace'))




#*****************************CATEGORIES*******************************#

@app.route("/list-categories/", methods=["GET", "POST"])
def listcategories():
    if 'IdUtilisateurs' not in session:
        return redirect(url_for('login'))

    IdUser = session.get('IdUtilisateurs')
    connection = pyodbc.connect(app.config['SQL_SERVER_CONNECTION_STRING'])
    cursor = connection.cursor()

    cursor.execute("SELECT * FROM Utilisateurs WHERE IdUtilisateurs = ?", (IdUser,))
    Utilisateurs = cursor.fetchone()
    cursor.close()

    if request.method == "POST":
        Titre = request.form["Titre"]
        DetailsCategories = request.form["DetailsCategories"]
        Images = request.files["Images"]

        filename = secure_filename(Images.filename)
        image_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        Images.save(image_path)
        
        print(f"Titre: {Titre}")
        print(f"DetailsCategories: {DetailsCategories}")
        print(f"Images: {Images}")

        connection = pyodbc.connect(app.config['SQL_SERVER_CONNECTION_STRING'])
        cursor = connection.cursor()
        cursor.execute("INSERT INTO Categories (Images, Titre, DetailsCategories, IdUtilisateurs) VALUES (?, ?, ?, ?)",
                       (filename, Titre, DetailsCategories, IdUser))
        connection.commit()
        cursor.close()

        return redirect(url_for('listcategories'))
    
    connection = pyodbc.connect(app.config['SQL_SERVER_CONNECTION_STRING'])
    cursor = connection.cursor()
    
    cursor.execute("SELECT * FROM Categories")
    Categories = cursor.fetchall()
    print(f"Categories: {Categories}")

    connection.close()

    return render_template("/Categories/list-categories.html", Utilisateurs=Utilisateurs, Categories=Categories)




@app.route("/ajout-categories", methods=["GET", "POST"])
def ajoutcategories():
    # Vérifier si l'utilisateur est connecté
    if 'IdUtilisateurs' not in session:
        return redirect(url_for('login'))

    IdUser = session.get('IdUtilisateurs')
    connection = pyodbc.connect(app.config['SQL_SERVER_CONNECTION_STRING'])
    cursor = connection.cursor()
     
    try:
        # Récupérer les informations de l'utilisateur
        cursor.execute("SELECT * FROM Utilisateurs WHERE IdUtilisateurs = ?", (IdUser))
        Utilisateurs = cursor.fetchone()

        if request.method == "POST":
            # Récupérer les données du formulaire
            Titre = request.form["Titre"]
            DetailsCategories = request.form["DetailsCategories"]
            Images = request.files["Images"]
            
            print(f"Titre: {Titre}")
            print(f"DetailsCategories: {DetailsCategories}")
            print(f"Images: {Images}")
            
            filename = secure_filename(Images.filename)
            image_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            Images.save(image_path)
         
            connection = pyodbc.connect(app.config['SQL_SERVER_CONNECTION_STRING'])
            cursor = connection.cursor()
    
            # Insérer les données dans la base de données
            cursor.execute("INSERT INTO Categories (Images,Titre, DetailsCategories) VALUES (?,?, ?)",
                           (filename, Titre, DetailsCategories))
            connection.commit()
            return redirect(url_for("listcategories"))

    except Exception as e:
        # Gérer l'erreur et afficher un message d'erreur approprié
        flash(f'Une erreur est survenue lors de l\'ajout de la Categorie : {str(e)}', 'danger')

    finally:
        # Fermer la connexion à la base de données
        cursor.close()
        connection.close()

    return render_template("/Categories/ajout-categories.html" ,Utilisateurs=Utilisateurs)




@app.route('/modifiecategories/<int:IdCategories>', methods=['GET', 'POST'])
def modifiecategories(IdCategories):
    # Vérifier si l'utilisateur est connecté
    if 'IdUtilisateurs' not in session:
        return redirect(url_for('login'))

    IdUser = session.get('IdUtilisateurs')
    connection = pyodbc.connect(app.config['SQL_SERVER_CONNECTION_STRING'])
    cursor = connection.cursor()
    
    try:
        # Récupérer les informations de l'utilisateur
        cursor.execute("SELECT * FROM Utilisateurs WHERE IdUtilisateurs = ?", (IdUser))
        Utilisateurs = cursor.fetchone()

        # Récupérer les informations de la catégorie
        cursor.execute("SELECT * FROM Categories WHERE IdCategories = ?", (IdCategories))
        categorie = cursor.fetchone()

        if request.method == 'POST':
            # Récupérer les données du formulaire
            Titre = request.form['Titre']
            DetailsCategories = request.form['DetailsCategories']
            Images = request.files.get('Images')

            if Images and Images.filename != '':
                filename = secure_filename(Images.filename)
                image_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
                Images.save(image_path)
            else:
                filename = categorie.Images

            # Mettre à jour les données dans la base de données
            cursor.execute("""
                UPDATE Categories 
                SET Titre = ?, DetailsCategories = ?, Images = ?
                WHERE IdCategories = ?
            """, (Titre, DetailsCategories, filename, IdCategories))
            connection.commit()
            
            flash('Catégorie mise à jour avec succès', 'success')
            return redirect(url_for('listcategories'))

    except Exception as e:
        flash(f'Une erreur est survenue lors de la modification de la catégorie : {str(e)}', 'danger')

    finally:
        cursor.close()
        connection.close()

    return render_template("/Categories/modifie-categories.html", Utilisateurs=Utilisateurs, categorie=categorie)




@app.route('/supprimecategories/<int:IdCategories>', methods=['GET', 'POST'])
def supprimecategories(IdCategories):
    # Vérifier si l'utilisateur est connecté
    if 'IdUtilisateurs' not in session:
        return redirect(url_for('login'))

    IdUser = session.get('IdUtilisateurs')
    connection = pyodbc.connect(app.config['SQL_SERVER_CONNECTION_STRING'])
    cursor = connection.cursor()
    
    try:
        # Vérifier d'abord si la catégorie existe
        cursor.execute("SELECT * FROM Categories WHERE IdCategories = ?", (IdCategories,))
        categorie = cursor.fetchone()

        if not categorie:
            flash("La catégorie que vous essayez de supprimer n'existe pas.", 'danger')
            return redirect(url_for('listcategories'))

        
        # Ensuite, supprimer la catégorie elle-même
        cursor.execute("DELETE FROM Categories WHERE IdCategories = ?", (IdCategories,))
        
        connection.commit()
        flash('Catégorie supprimée avec succès', 'success')
        return redirect(url_for('listcategories'))
    
    except Exception as e:
        flash(f'Une erreur est survenue lors de la suppression de la catégorie : {str(e)}', 'danger')
        return redirect(url_for('listcategories'))
    
    finally:
        cursor.close()
        connection.close()


# ***********************fin-categories***********************



@app.route("/list-cours/", methods=["GET", "POST"])
def listCours():
    if 'IdUtilisateurs' not in session:
        return redirect(url_for('login'))

    IdUser = session.get('IdUtilisateurs')
    connection = pyodbc.connect(app.config['SQL_SERVER_CONNECTION_STRING'])
    cursor = connection.cursor()

    cursor.execute("SELECT * FROM Utilisateurs WHERE IdUtilisateurs = ?", (IdUser,))
    Utilisateur = cursor.fetchone()
    cursor.close()

    if request.method == "POST":
        Titre = request.form["Titre"]
        DetailsCours = request.form["DetailsCours"]
        Images = request.files["Images"]
        IdCategories = request.form["IdCategories"] 

        filename = secure_filename(Images.filename)
        image_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        Images.save(image_path)
        
        connection = pyodbc.connect(app.config['SQL_SERVER_CONNECTION_STRING'])
        cursor = connection.cursor()
        
        cursor.execute("INSERT INTO Cours (Images, Titre, DetailsCours, IdCategories) VALUES (?, ?, ?, ?)",
                       (filename, Titre, DetailsCours, IdCategories))
        connection.commit()
        cursor.close()

        return redirect(url_for('listcours'))
    
    connection = pyodbc.connect(app.config['SQL_SERVER_CONNECTION_STRING'])
    cursor = connection.cursor()
    
    cursor.execute("SELECT * FROM Cours")
    Cours = cursor.fetchall()

    connection.close()

    return render_template("/Cours/list-cours.html", Utilisateurs=Utilisateur, Cours=Cours)




@app.route("/ajout-cours/", methods=["GET", "POST"])
def ajoutCours():
    # Vérifier si l'utilisateur est connecté
    if 'IdUtilisateurs' not in session:
        return redirect(url_for('login'))

    IdUser = session.get('IdUtilisateurs')
    connection = pyodbc.connect(app.config['SQL_SERVER_CONNECTION_STRING'])
    cursor = connection.cursor()

    try:
        # Récupérer les informations de l'utilisateur
        cursor.execute("SELECT * FROM Utilisateurs WHERE IdUtilisateurs = ?", (IdUser,))
        Utilisateur = cursor.fetchone()

        if request.method == "POST":
            # Récupérer les données du formulaire
            Titre = request.form["Titre"]
            DetailsCours = request.form["DetailsCours"]
            Images = request.files["Images"]
            IdCategories = request.form["IdCategories"] 
            
            filename = secure_filename(Images.filename)
            image_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            Images.save(image_path)
         
            # Insérer les données dans la base de données
            cursor.execute("INSERT INTO Cours (Images, Titre, DetailsCours, IdCategories) VALUES (?, ?, ?, ?)",
                           (filename, Titre, DetailsCours, IdCategories))
            connection.commit()
            flash('Cours ajouté avec succès', 'success')
            return redirect(url_for('listcours'))

    except Exception as e:
        # Gérer l'erreur et afficher un message d'erreur approprié
        flash(f'Une erreur est survenue lors de l\'ajout du cours : {str(e)}', 'danger')

    finally:
        # Fermer la connexion à la base de données
        cursor.close()
        connection.close()

    return render_template("/Cours/ajout-cours.html" ,Utilisateurs=Utilisateur)



@app.route("/modifie-cours/", methods=["GET", "POST"])
def modifieCours(id):
    # Vérifier si l'utilisateur est connecté
    if 'IdUtilisateurs' not in session:
        return redirect(url_for('login'))

    IdUser = session.get('IdUtilisateurs')
    connection = pyodbc.connect(app.config['SQL_SERVER_CONNECTION_STRING'])
    cursor = connection.cursor()
    
    connection = pyodbc.connect(app.config['SQL_SERVER_CONNECTION_STRING'])
    cursor = connection.cursor()


    IdUser = session.get('IdUtilisateurs')
    connection = pyodbc.connect(app.config['SQL_SERVER_CONNECTION_STRING'])
    cursor = connection.cursor()
    
    
    cursor.execute("SELECT * FROM Utilisateurs WHERE IdUtilisateurs = ?", (IdUser))
    Utilisateur = cursor.fetchone()
    return render_template("/Cours/modifie-cours.html" ,Utilisateurs=Utilisateur)



@app.route("/supprime-cours/", methods=["GET", "POST"])
def supprimeCours():
    if 'IdUtilisateurs' not in session:
        return redirect(url_for('login'))

    connection = pyodbc.connect(app.config['SQL_SERVER_CONNECTION_STRING'])
    cursor = connection.cursor()


    IdUser = session.get('IdUtilisateurs')
    connection = pyodbc.connect(app.config['SQL_SERVER_CONNECTION_STRING'])
    cursor = connection.cursor()
    
    
    cursor.execute("SELECT * FROM Utilisateurs WHERE IdUtilisateurs = ?", (IdUser))
    Utilisateur = cursor.fetchone()
    return render_template("/Cours/supprime-cours.html" ,Utilisateurs=Utilisateur)



#********************************Debut-Programmes*******************************#


@app.route("/list-programmes/", methods=["GET", "POST"])
def listprogrammes():
     # Vérifier si l'utilisateur est connecté
    if 'IdUtilisateurs' not in session:
        return redirect(url_for('login'))

    connection = pyodbc.connect(app.config['SQL_SERVER_CONNECTION_STRING'])
    cursor=connection.cursor()
    
    IdUser = session.get('IdUtilisateurs')
    cursor.execute("SELECT * FROM Utilisateurs WHERE IdUtilisateurs = ?", (IdUser))
    Utilisateurs = cursor.fetchone()
    role = Utilisateurs[8]
    print(f"Role: {role}")

    # Récupération des programmes
    cursor.execute("SELECT IdProgrammes, Images, Titre, Date_debut, Duree_programmes, Nombre_apprenants FROM Programmes")
    programmes = cursor.fetchall()
    print(f"Mes Programmes: {programmes}")
    
    connection.close()

    return render_template("/Programmes/list-programmes.html", Utilisateurs=Utilisateurs, programmes=programmes,role=role)




@app.route("/ajout-programmes", methods=["GET", "POST"])
def ajoutprogrammes():
    # Vérifier si l'utilisateur est connecté
    if 'IdUtilisateurs' not in session:
        return redirect(url_for('login'))
    
    IdUser = session.get('IdUtilisateurs')
    connection = pyodbc.connect(app.config['SQL_SERVER_CONNECTION_STRING'])
    cursor = connection.cursor()

    cursor.execute("SELECT * FROM Utilisateurs WHERE IdUtilisateurs = ?", (IdUser,))
    Utilisateurs = cursor.fetchone()
    
    cursor.execute("SELECT IdCategories, Titre FROM Categories")
    Categories = cursor.fetchall()
    
    print(f"Les Categories: {Categories}")
    
    cursor.close()

    if request.method == "POST":
        Titre = request.form["Titre"]
        DetailsProgrammes = request.form["DetailsProgrammes"]
        Duree_programmes = request.form["Duree_programmes"]
        Date_debut = request.form["Date_debut"]
        Date_fin = request.form["Date_fin"]
        IdCategories = request.form["IdCategories"]
        Images = request.files["Images"]

        filename = secure_filename(Images.filename)
        image_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        Images.save(image_path)
        
        connection = pyodbc.connect(app.config['SQL_SERVER_CONNECTION_STRING'])
        cursor = connection.cursor()
        cursor.execute("""
            INSERT INTO Programmes (Images, Titre, DetailsProgrammes, Duree_programmes, Date_debut, Date_fin, IdCategories) 
            VALUES (?, ?, ?, ?, ?, ?, ?)""",
            (filename, Titre, DetailsProgrammes, Duree_programmes, Date_debut, Date_fin, IdCategories))
        connection.commit()
        cursor.close()

        return redirect(url_for('listprogrammes'))

    return render_template("Programmes/ajout-programmes.html",Utilisateurs=Utilisateurs, Categories=Categories)





@app.route('/modifieprogrammes/<int:IdProgrammes>', methods=['GET', 'POST'])
def modifieprogrammes(IdProgrammes):
    # Vérifier si l'utilisateur est connecté
    if 'IdUtilisateurs' not in session:
        return redirect(url_for('login'))

    IdUser = session.get('IdUtilisateurs')
    connection = pyodbc.connect(app.config['SQL_SERVER_CONNECTION_STRING'])
    cursor = connection.cursor()

    cursor.execute("SELECT * FROM Utilisateurs WHERE IdUtilisateurs = ?", (IdUser,))
    Utilisateurs = cursor.fetchone()
    
    # Récupérer le programme spécifique à modifier
    cursor.execute("SELECT * FROM Programmes WHERE IdProgrammes = ?", (IdProgrammes,))
    programme = cursor.fetchone()
    
    if request.method == 'POST':
        Titre = request.form['Titre']
        DetailsProgrammes = request.form['DetailsProgrammes']
        Duree_programmes = request.form['Duree_programmes']
        Date_debut = request.form['Date_debut']
        Date_fin = request.form['Date_fin']
        Nombre_apprenants = request.form['Nombre_apprenants']
        IdCategories = request.form['IdCategories']
        
        
        print("Form data received:")
        print(f"Titre: {Titre}")
        print(f"DetailsProgrammes: {DetailsProgrammes}")
        print(f"Duree_programmes: {Duree_programmes}")
        print(f"Date_debut: {Date_debut}")
        print(f"Date_fin: {Date_fin}")
        print(f"Nombre_apprenants: {Nombre_apprenants}")
        print(f"IdCategories: {IdCategories}")
        
        Images = request.files['Images']
        if Images:
            filename = secure_filename(Images.filename)
            image_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            Images.save(image_path)
        else:
            filename = programme.Images  # Garder l'image existante si aucune nouvelle image n'est uploadée

        cursor.execute("""
            UPDATE Programmes 
            SET Images = ?, Titre = ?, DetailsProgrammes = ?, Duree_programmes = ?, Date_debut = ?, Date_fin = ?, Nombre_apprenants = ?, IdCategories = ?
            WHERE IdProgrammes = ?""",
            (filename, Titre, DetailsProgrammes, Duree_programmes, Date_debut, Date_fin, Nombre_apprenants, IdCategories, IdProgrammes))
        
        connection.commit()
        connection.close()
        return redirect(url_for('listprogrammes'))
    
    cursor.execute("SELECT IdCategories, Titre FROM Categories")
    Categories = cursor.fetchall()

    connection.close()
    return render_template('Programmes/modifie-programmes.html', programme=programme, Categories=Categories, Utilisateurs=Utilisateurs)





@app.route('/supprimeprogrammes/<int:IdProgrammes>', methods=['GET', 'POST'])
def supprimeprogrammes(IdProgrammes):
    # Vérifier si l'utilisateur est connecté
    if 'IdUtilisateurs' not in session:
        return redirect(url_for('login'))

    IdUser = session.get('IdUtilisateurs')
    connection = pyodbc.connect(app.config['SQL_SERVER_CONNECTION_STRING'])
    cursor = connection.cursor()
    
    try:
        # Vérifier d'abord si le programme existe
        cursor.execute("SELECT * FROM Programmes WHERE IdProgrammes = ?", (IdProgrammes,))
        programme = cursor.fetchone()
        
        if not programme:
            flash("Le programme que vous essayez de supprimer n'existe pas.", 'danger')
            return redirect(url_for('listprogrammes'))

        # Supprimer le programme
        cursor.execute("DELETE FROM Programmes WHERE IdProgrammes = ?", (IdProgrammes,))
        
        connection.commit()
        flash('Le programme a été supprimé avec succès', 'success')
        return redirect(url_for('listprogrammes'))
    
    except Exception as e:
        flash(f'Une erreur est survenue lors de la suppression du programme : {str(e)}', 'danger')
        return redirect(url_for('listprogrammes'))
    
    finally:
        cursor.close()
        connection.close()


    
 


@app.route("/infos-programmes/")
def infosprogrammes():
    # Vérifier si l'utilisateur est connecté
    if 'IdUtilisateurs' not in session:
        return redirect(url_for('login'))

    IdUser = session.get('IdUtilisateurs')
    connection = pyodbc.connect(app.config['SQL_SERVER_CONNECTION_STRING'])
    cursor = connection.cursor()
    
    
    cursor.execute("SELECT * FROM Utilisateurs WHERE IdUtilisateurs = ?", (IdUser))
    Utilisateur = cursor.fetchone()
    return render_template("/Programmes/infos-programmes.html" ,Utilisateurs=Utilisateur) 

#*********************************fin-Programmes*******************************#








#*****************************BAILLEURS*******************************#


@app.route("/list-bailleurs/", methods=["GET", "POST"])
def listbailleurs():
    if 'IdUtilisateurs' not in session:
        return redirect(url_for('login'))

    IdUser = session.get('IdUtilisateurs')
    connection = pyodbc.connect(app.config['SQL_SERVER_CONNECTION_STRING'])
    cursor = connection.cursor()

    cursor.execute("SELECT * FROM Utilisateurs WHERE IdUtilisateurs = ?", (IdUser,))
    Utilisateur = cursor.fetchone()
    cursor.close()

    if request.method == "POST":
        NomEntreprise = request.form["NomEntreprise"]
        Adresse = request.form["Adresse"]
        Telephone = request.form["Telephone"]
        Email = request.form["Email"]
        TypeFinancement = request.form["TypeFinancement"]
        DetailsFinancement = request.form["DetailsFinancement"]
        MontantFinancement = request.form["MontantFinancement"]
        Nom_Contact = request.form["Nom_Contact"]
        Poste_Contact = request.form["Poste_Contact"]
        Telephone_Contact = request.form["Telephone_Contact"]
        Email_Contact = request.form["Email_Contact"]
        IdProgrammes = request.form["IdProgrammes"]

        connection = pyodbc.connect(app.config['SQL_SERVER_CONNECTION_STRING'])
        cursor = connection.cursor()

        cursor.execute("""INSERT INTO Bailleurs (NomEntreprise, Adresse, Telephone, Email, TypeFinancement, DetailsFinancement, MontantFinancement, Nom_Contact, Poste_Contact, Telephone_Contact, Email_Contact, IdProgrammes)
                          VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                       (NomEntreprise, Adresse, Telephone, Email, TypeFinancement, DetailsFinancement, MontantFinancement, Nom_Contact, Poste_Contact, Telephone_Contact, Email_Contact, IdProgrammes))
        connection.commit()
        cursor.close()

        return redirect(url_for('listbailleurs'))

    connection = pyodbc.connect(app.config['SQL_SERVER_CONNECTION_STRING'])
    cursor = connection.cursor()

    cursor.execute("SELECT * FROM Bailleurs")
    Bailleurs = cursor.fetchall()

    connection.close()

    return render_template("/Bailleurs/list-bailleurs.html", Utilisateurs=Utilisateur, Bailleurs=Bailleurs)





@app.route("/ajout-bailleurs/", methods=["GET", "POST"])
def ajoutbailleurs():
    # Vérifier si l'utilisateur est connecté
    if 'IdUtilisateurs' not in session:
        return redirect(url_for('login'))

    IdUser = session.get('IdUtilisateurs')
    connection = pyodbc.connect(app.config['SQL_SERVER_CONNECTION_STRING'])
    cursor = connection.cursor()

    cursor.execute("SELECT * FROM Utilisateurs WHERE IdUtilisateurs = ?", (IdUser,))
    Utilisateurs = cursor.fetchone()
    
    cursor.execute("SELECT IdProgrammes, Titre FROM Programmes")
    Programmes = cursor.fetchall()

    if request.method == "POST":
        NomEntreprise = request.form["NomEntreprise"]
        Adresse = request.form["Adresse"]
        Telephone = request.form["Telephone"]
        Email = request.form["Email"]
        TypeFinancement = request.form["TypeFinancement"]
        DetailsFinancement = request.form["DetailsFinancement"]
        MontantFinancement = request.form["MontantFinancement"]
        Nom_Contact = request.form["Nom_Contact"]
        Poste_Contact = request.form["Poste_Contact"]
        Telephone_Contact = request.form["Telephone_Contact"]
        Email_Contact = request.form["Email_Contact"]
        IdProgrammes = request.form["IdProgrammes"]

        cursor.execute("""
            INSERT INTO Bailleurs (NomEntreprise, Adresse, Telephone, Email, TypeFinancement, DetailsFinancement, MontantFinancement, Nom_Contact, Poste_Contact, Telephone_Contact, Email_Contact, IdProgrammes)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (NomEntreprise, Adresse, Telephone, Email, TypeFinancement, DetailsFinancement, MontantFinancement, Nom_Contact, Poste_Contact, Telephone_Contact, Email_Contact, IdProgrammes))
        
        connection.commit()
        cursor.close()
        connection.close()
        
        return redirect(url_for('listbailleurs'))

    return render_template("/Bailleurs/ajout-bailleurs.html", Utilisateurs=Utilisateurs, Programmes=Programmes)




@app.route('/modifiebailleurs/<int:IdBailleurs>', methods=['GET', 'POST'])
def modifiebailleurs(IdBailleurs):
    # Vérifier si l'utilisateur est connecté
    if 'IdUtilisateurs' not in session:
        return redirect(url_for('login'))

    IdUser = session.get('IdUtilisateurs')
    connection = pyodbc.connect(app.config['SQL_SERVER_CONNECTION_STRING'])
    cursor = connection.cursor()

    cursor.execute("SELECT * FROM Utilisateurs WHERE IdUtilisateurs = ?", (IdUser,))
    Utilisateurs = cursor.fetchone()
    
    # Récupérer le bailleur spécifique à modifier
    cursor.execute("SELECT * FROM Bailleurs WHERE IdBailleurs = ?", (IdBailleurs,))
    bailleur = cursor.fetchone()
    
    if request.method == 'POST':
        NomEntreprise = request.form['NomEntreprise']
        Adresse = request.form['Adresse']
        Email = request.form['Email']
        Telephone = request.form['Telephone']
        TypeFinancement = request.form['TypeFinancement']
        DetailsFinancement = request.form['DetailsFinancement']
        MontantFinancement = request.form['MontantFinancement']
        Nom_Contact = request.form['Nom_Contact']
        Poste_Contact = request.form['Poste_Contact']
        Telephone_Contact = request.form['Telephone_Contact']
        Email_Contact = request.form['Email_Contact']
        IdProgrammes = request.form['IdProgrammes']
        
        cursor.execute("""
            UPDATE Bailleurs 
            SET NomEntreprise = ?, Adresse = ?, Email = ?, Telephone = ?, TypeFinancement = ?, DetailsFinancement = ?, MontantFinancement = ?, Nom_Contact = ?, Poste_Contact = ?, Telephone_Contact = ?, Email_Contact = ?, IdProgrammes = ?
            WHERE IdBailleurs = ?""",
            (NomEntreprise, Adresse, Email, Telephone, TypeFinancement, DetailsFinancement, MontantFinancement, Nom_Contact, Poste_Contact, Telephone_Contact, Email_Contact, IdProgrammes, IdBailleurs))
        
        connection.commit()
        connection.close()
        return redirect(url_for('listbailleurs'))
    
    cursor.execute("SELECT IdProgrammes, Titre FROM Programmes")
    Programmes = cursor.fetchall()

    connection.close()
    return render_template('Bailleurs/modifie-bailleurs.html', bailleur=bailleur, Programmes=Programmes, Utilisateurs=Utilisateurs)



@app.route('/suprimebailleurs/<int:IdBailleurs>', methods=['GET', 'POST'])
def suprimebailleurs(IdBailleurs):
    # Vérifier si l'utilisateur est connecté
    if 'IdUtilisateurs' not in session:
        return redirect(url_for('login'))

    IdUser = session.get('IdUtilisateurs')
    connection = pyodbc.connect(app.config['SQL_SERVER_CONNECTION_STRING'])
    cursor = connection.cursor()
    
    try:
        # Vérifier d'abord si le bailleur existe
        cursor.execute("SELECT * FROM Bailleurs WHERE IdBailleurs = ?", (IdBailleurs,))
        bailleur = cursor.fetchone()
        
        if not bailleur:
            flash("Le bailleur que vous essayez de supprimer n'existe pas.", 'danger')
            return redirect(url_for('listbailleurs'))

        # Supprimer le bailleur
        cursor.execute("DELETE FROM Bailleurs WHERE IdBailleurs = ?", (IdBailleurs,))
        
        connection.commit()
        flash('Le bailleur a été supprimé avec succès', 'success')
        return redirect(url_for('listbailleurs'))
    
    except Exception as e:
        flash(f'Une erreur est survenue lors de la suppression du bailleur : {str(e)}', 'danger')
        return redirect(url_for('listbailleurs'))
    
    finally:
        cursor.close()
        connection.close()









@app.route("/profile-bailleurs/")
def profilebailleurs():
    # Vérifier si l'utilisateur est connecté
    if 'IdUtilisateurs' not in session:
        return redirect(url_for('login'))

    IdUser = session.get('IdUtilisateurs')
    connection = pyodbc.connect(app.config['SQL_SERVER_CONNECTION_STRING'])
    cursor = connection.cursor()
    
    cursor.execute("SELECT * FROM Utilisateurs WHERE IdUtilisateurs = ?", (IdUser))
    Utilisateur = cursor.fetchone()
    return render_template("/Bailleurs/profile-bailleurs.html" ,Utilisateurs=Utilisateur)




#*********************************fin-Bailleurs*******************************#






#*****************************Classification*******************************#


@app.route("/Classification/")
def Classification():
    # Vérifier si l'utilisateur est connecté
    if 'IdUtilisateurs' not in session:
        return redirect(url_for('login'))

    IdUser = session.get('IdUtilisateurs')
    connection = pyodbc.connect(app.config['SQL_SERVER_CONNECTION_STRING'])
    cursor = connection.cursor()
    
    cursor.execute("SELECT * FROM Utilisateurs WHERE IdUtilisateurs = ?", (IdUser))
    Utilisateur = cursor.fetchone()
    return render_template("/dashbord/Classification.html" ,Utilisateurs=Utilisateur)


@app.route("/index/")
def index():
    # Vérifier si l'utilisateur est connecté
    if 'IdUtilisateurs' not in session:
        return redirect(url_for('login'))

    IdUser = session.get('IdUtilisateurs')
    connection = pyodbc.connect(app.config['SQL_SERVER_CONNECTION_STRING'])
    cursor = connection.cursor()
    
    
    cursor.execute("SELECT * FROM Utilisateurs WHERE IdUtilisateurs = ?", (IdUser))
    Utilisateur = cursor.fetchone()
    return render_template("/dashbord/index.html" ,Utilisateurs=Utilisateur)





#*****************************Communications*******************************#


@app.route("/emailing/", methods=['GET', 'POST'])
def emailing():
    # Vérifier si l'utilisateur est connecté
    if 'IdUtilisateurs' not in session:
        return redirect(url_for('login'))

    IdUser = session.get('IdUtilisateurs')
    connection = pyodbc.connect(app.config['SQL_SERVER_CONNECTION_STRING'])
    cursor = connection.cursor()
    
    # Récupérer les programmes
    cursor.execute("SELECT IdProgrammes, Titre FROM Programmes")
    Programmes = cursor.fetchall()
    
    # Récupérer les informations de l'utilisateur connecté
    cursor.execute("SELECT * FROM Utilisateurs WHERE IdUtilisateurs = ?", IdUser)
    Utilisateurs = cursor.fetchone()
    
    if request.method == 'POST':
        IdProgrammes = request.form['IdProgrammes']
        destinataires = []
        
        send_to = request.form.get('send_to')
        
        if send_to == 'formateur':
            subject = request.form['subject_formateur']
            message = request.form['message_formateur']
            cursor.execute("""
                SELECT U.Email FROM Utilisateurs U
                INNER JOIN Formateurs F ON U.IdUtilisateurs = F.IdUtilisateurs
                WHERE F.IdProgrammes = ?
            """, IdProgrammes)
            formateurs = cursor.fetchall()
            for formateur in formateurs:
                destinataires.append(formateur.Email)
        
        elif send_to == 'apprenants':
            subject = request.form['subject_apprenants']
            message = request.form['message_apprenants']
            cursor.execute("""
                SELECT U.Email FROM Utilisateurs U
                INNER JOIN Apprenants A ON U.IdUtilisateurs = A.IdUtilisateurs
                WHERE A.IdProgrammes = ?
            """, IdProgrammes)
            apprenants = cursor.fetchall()
            for apprenant in apprenants:
                destinataires.append(apprenant.Email)
        
        # Récupérer l'email de l'utilisateur connecté pour l'expéditeur
        sender = Utilisateurs.Email
        
        # Envoyer l'email via une fonction API (à implémenter)
        # response = envoyer_email_api(subject, message, sender, destinataires)
        flash('Email envoyé avec succès!', 'success')
        return redirect(url_for('emailing'))
    
    return render_template("/Communications/emailing.html", Utilisateurs=Utilisateurs, Programmes=Programmes)







@app.route('/messagerie', methods=['GET', 'POST'])
def envoyersms():
    # Vérifier si l'utilisateur est connecté
    if 'IdUtilisateurs' not in session:
        return redirect(url_for('login'))
    
    IdUser = session.get('IdUtilisateurs')
    connection = pyodbc.connect(app.config['SQL_SERVER_CONNECTION_STRING'])
    cursor = connection.cursor()
    
    # Récupérer les informations de l'utilisateur connecté
    cursor.execute("SELECT * FROM Utilisateurs WHERE IdUtilisateurs = ?", IdUser)
    Utilisateurs = cursor.fetchone()

    # Récupérer les programmes
    cursor.execute("SELECT * FROM Programmes")
    programmes = cursor.fetchall()

    if request.method == 'POST':
        IdProgrammes = request.form['IdProgrammes']
        destinataires = []
        
        send_to = request.form.get('send_to')
        
        if send_to == 'formateur':
            message = request.form['message_formateur']
            cursor.execute("""
                SELECT U.Telephone FROM Utilisateurs U
                INNER JOIN Formateurs F ON U.IdUtilisateurs = F.IdUtilisateurs
                WHERE F.IdProgrammes = ?
            """, IdProgrammes)
            formateurs = cursor.fetchone()
            for formateur in formateurs:
                destinataires.append(formateur.Telephone)
        
        elif send_to == 'apprenants':
            message = request.form['message_apprenants']
            cursor.execute("""
                SELECT U.Telephone FROM Utilisateurs U
                INNER JOIN Apprenants A ON U.IdUtilisateurs = A.IdUtilisateurs
                WHERE A.IdProgrammes = ?
            """, IdProgrammes)
            apprenants = cursor.fetchall()
            for apprenant in apprenants:
                destinataires.append(apprenant.Telephone)
        
        # Récupérer le numéro de téléphone de l'utilisateur connecté
        sender = Utilisateurs.Telephone
        
        # Envoyer le SMS via l'API
        response = envoyer_sms_api(message, sender, destinataires)
        flash('SMS envoyé avec succès!', 'success')
        return redirect(url_for('envoyersms'))
    
    return render_template('/Communications/messagerie.html', Utilisateurs=Utilisateurs, Programmes=programmes)



@app.route("/sentiment/")
def sentiment():
    # Vérifier si l'utilisateur est connecté
    if 'IdUtilisateurs' not in session:
        return redirect(url_for('login'))

    IdUser = session.get('IdUtilisateurs')
    connection = pyodbc.connect(app.config['SQL_SERVER_CONNECTION_STRING'])
    cursor = connection.cursor()
    
    
    
    cursor.execute("SELECT * FROM Utilisateurs WHERE IdUtilisateurs = ?", (IdUser))
    utilisateurs = cursor.fetchone()
    
    return render_template("/Communications/sentiment.html" ,utilisateurs=utilisateurs)










if __name__ == '__main__':
    app.run(debug=True)
