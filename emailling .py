import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from flask import Flask, request, redirect, url_for, flash, render_template, session
import pyodbc



app = Flask(__name__)
app.secret_key = 'votre_cle_secrete'


# Configuration de la connexion à SQL Server
app.config["SQL_SERVER_CONNECTION_STRING"] = """
    Driver={SQL Server};
    Server=DESKTOP-VJVVU51\SQLEXPRESS;
    Database=BD_SOUTENANCE;
    Trusted_Connection=yes;
"""


def envoyer_email_api(subject, message, sender, destinataires):
    try:
        smtp_server = "smtp.example.com"
        smtp_port = 587
        smtp_user = "your_smtp_user"
        smtp_password = "your_smtp_password"

        msg = MIMEMultipart()
        msg['From'] = sender
        msg['Subject'] = subject
        msg.attach(MIMEText(message, 'plain'))

        server = smtplib.SMTP(smtp_server, smtp_port)
        server.starttls()
        server.login(smtp_user, smtp_password)

        for recipient in destinataires:
            msg['To'] = recipient
            server.sendmail(sender, recipient, msg.as_string())

        server.quit()
        return "Emails envoyés avec succès"
    except Exception as e:
        return str(e)


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
        response = envoyer_email_api(subject, message, sender, destinataires)
        flash('Email envoyé avec succès!', 'success')
        return redirect(url_for('emailing'))
    
    return render_template("/Communications/emailing.html", Utilisateurs=Utilisateurs, Programmes=Programmes)
