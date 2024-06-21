from flask import Flask, render_template, request
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.naive_bayes import MultinomialNB

app = Flask(__name__)

# Charger le modèle pré-entraîné
vectorizer = TfidfVectorizer(max_features=5000)
model = MultinomialNB()
# Charger les données d'entraînement et entraîner le modèle

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/analyze', methods=['POST'])
def analyze():
    comment = request.form['comment']
    # Vectoriser le commentaire
    comment_vector = vectorizer.transform([comment])
    # Prédire le sentiment
    sentiment = model.predict(comment_vector)[0]
    return render_template('result.html', comment=comment, sentiment=sentiment)






#*****************************envoi d'emails*******************************#

# @app.route('/send_emails', methods=['GET', 'POST'])
# def send_emails():
#     if request.method == 'POST':
#         program_id = request.form['program_id']
#         subject = request.form['subject']
#         message = request.form['message']

#         # Connexion à la base de données
#         conn = pyodbc.connect(conn_str)
#         cursor = conn.cursor()

#         # Récupération des emails des apprenants pour le programme sélectionné
#         cursor.execute("""
#             SELECT Email FROM Apprenants WHERE IdProgrammes = ?
#         """, program_id)
#         emails = [row[0] for row in cursor.fetchall()]

#         # Envoi des emails
#         for email in emails:
#             send_email(email, subject, message)
        
#         flash('Emails sent successfully!', 'success')
#         return redirect(url_for('send_emails'))

#     # Récupération des programmes pour le formulaire de sélection
#     conn = pyodbc.connect(conn_str)
#     cursor = conn.cursor()
#     cursor.execute("SELECT IdProgrammes, Titre FROM Programmes")
#     programs = cursor.fetchall()

#     return render_template('send_emails.html', programs=programs)

# def send_email(to_email, subject, message):
#     from_email = 'your_email@example.com'
#     password = 'your_password'

#     msg = MIMEMultipart()
#     msg['From'] = from_email
#     msg['To'] = to_email
#     msg['Subject'] = subject
#     msg.attach(MIMEText(message, 'plain'))

#     try:
#         server = smtplib.SMTP('smtp.example.com', 587)
#         server.starttls()
#         server.login(from_email, password)
#         text = msg.as_string()
#         server.sendmail(from_email, to_email, text)
#         server.quit()
#     except Exception as e:
#         print(f"Failed to send email to {to_email}: {e}")












if __name__ == '__main__':
    app.run(debug=True)
