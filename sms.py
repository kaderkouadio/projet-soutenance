import os
import http.client
import json
from dotenv import load_dotenv
from flask import Flask, request, redirect, url_for, flash, render_template, session
import pyodbc

# Charger les variables d'environnement depuis le fichier .env
load_dotenv()

API_KEY = os.getenv('INFOBIP_API_KEY')
API_URL = os.getenv('INFOBIP_API_URL')

app = Flask(__name__)
app.secret_key = 'votre_cle_secrete'


# Configuration de la connexion à SQL Server
app.config["SQL_SERVER_CONNECTION_STRING"] = """
    Driver={SQL Server};
    Server=DESKTOP-VJVVU51\SQLEXPRESS;
    Database=BD_SOUTENANCE;
    Trusted_Connection=yes;
"""

def envoyer_sms_api(message, sender, destinataires):
    conn = http.client.HTTPSConnection(API_URL)
    destinations = [{"to": dest} for dest in destinataires]
    payload = json.dumps({
        "messages": [
            {
                "destinations": destinations,
                "from": sender,
                "text": message
            }
        ]
    })
    headers = {
        'Authorization': f'App {API_KEY}',
        'Content-Type': 'application/json',
        'Accept': 'application/json'
    }
    conn.request("POST", "/sms/2/text/advanced", payload, headers)
    res = conn.getresponse()
    data = res.read()
    return data.decode("utf-8")


# @app.route('/messagerie', methods=['GET', 'POST'])
# def envoyersms():
#     # Vérifier si l'utilisateur est connecté
#     if 'IdUtilisateurs' not in session:
#         return redirect(url_for('login'))
    
#     IdUser = session.get('IdUtilisateurs')
#     connection = pyodbc.connect(app.config['SQL_SERVER_CONNECTION_STRING'])
#     cursor = connection.cursor()
    
#     cursor.execute("SELECT * FROM Utilisateurs WHERE IdUtilisateurs = ?", IdUser)
#     Utilisateurs = cursor.fetchone()

#     cursor.execute("SELECT * FROM Programmes")
#     programmes = cursor.fetchall()

#     if request.method == 'POST':
#         message = request.form['message']
#         IdProgrammes = request.form['IdProgrammes']
#         destinataires = []
        
#         # Récupérer les numéros de téléphone des formateurs ou des apprenants en fonction du programme sélectionné
#         cursor.execute("SELECT Telephone FROM Formateurs WHERE IdProgrammes = ?", IdProgrammes)
#         formateurs = cursor.fetchall()
#         for formateur in formateurs:
#             destinataires.append(formateur.Telephone)
        
#         cursor.execute("SELECT Telephone FROM Apprenants WHERE IdProgrammes = ?", IdProgrammes)
#         apprenants = cursor.fetchall()
#         for apprenant in apprenants:
#             destinataires.append(apprenant.Telephone)

#         # Récupérer le numéro de téléphone de l'utilisateur connecté
#         sender = Utilisateurs.Telephone
        
#         # Envoyer le SMS via l'API
#         response = envoyer_sms_api(message, sender, destinataires)
#         flash('SMS envoyé avec succès!', 'success')
#         return redirect(url_for('envoyersms'))
    
#     return render_template('/Communications/messagerie.html', Utilisateurs=Utilisateurs, Programmes=programmes)



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
            formateurs = cursor.fetchall()
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
