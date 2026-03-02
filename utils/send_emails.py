import os
import smtplib
import ssl
from email.message import EmailMessage
from typing import List, Dict, Tuple
import re
from dotenv import load_dotenv
import logging
import argparse
import sys

def send_welcome(cn,mail,user,userpass):
    avatar_name = "no-reply-isdm-calcul@umontpellier.fr"
    
    if not all([smtp_server, user_name, password]):
        raise ValueError("Les variables SMTP_SERVER, USER_NAME et PASSWORD doivent être définies dans le fichier .env")
    else:
        print(f'All good ! \n Sending \n FROM {avatar_name} \n TO {args.mail}')
    
    context = ssl.create_default_context()
    
    with smtplib.SMTP(smtp_server, smtp_port, timeout=10) as server:
        server.starttls(context=context)
        server.login(user_name, password)
        
        body = f"""
    <!DOCTYPE html>
    <html lang="fr">
    <head>
      <meta charset="UTF-8">
      <title>Email - Connexion Cluster IO</title>
    </head>
    <body style="margin:0; padding:0; font-family:Arial, sans-serif; background-color:#f5f7f9;">
      <table align="center" width="800" cellpadding="0" cellspacing="0" style="background-color:#ffffff; overflow:hidden; box-shadow:0 4px 12px rgba(0,0,0,0.1);">
        
        <!-- Header avec logo -->
        <tr>
          <td align="center" style="background-color:#000000; padding:4px;">
            <img src="https://isdm.umontpellier.fr/wp-content/uploads/2025/10/Logo-ISDM-IO-blanc.png
     " 
                 alt="Logo Entreprise" 
                 style="max-width:350px; height:auto;">
          </td>
        </tr>
    
        <!-- Bande turquoise sous header -->
        <tr>
          <td style="background-color:#009dab; height:10px;"></td>
        </tr>
    
        <!-- Titre -->
        <tr>
          <td style="padding:35px 30px 20px 30px; text-align:center; color:#000000;">
            <h2 style="margin:0; font-size:26px; font-weight:bold;">Informations de connexion – Cluster IO</h2>
          </td>
        </tr>
    
        <!-- Contenu -->
        <tr>
          <td style="padding:0 40px 40px 40px; color:#333333; font-size:16px; line-height:1.7;">
            <p>Bonjour <strong>{args.cn}</strong>,</p>
            <p>Veuillez trouver ci-dessous vos informations de connexion et les ressources associées :</p>
    
            <!-- Identifiants -->
            <div style="border:1px solid #009dab; border-radius:10px; padding:20px; margin-bottom:25px;">
              <h3 style="margin-top:0; color:#009dab;"> Identifiants de connexion</h3>
              <p><strong>URL :</strong> ssh {args.user}@io-login.meso.umontpellier.fr</p>
              <p><strong>Nom d’utilisateur :</strong> {args.user}</p>
              <p><strong>Mot de passe :</strong> {args.password}</p>
            </div>
    
            <!-- Documentation -->
            <div style="border:1px solid #009dab; border-radius:10px; padding:20px; margin-bottom:25px;">
              <h3 style="margin-top:0; color:#009dab;"> Documentation</h3>
              <p><a href="https://docs.meso.umontpellier.fr/" style="color:#009dab; text-decoration:none;">Consulter le guide utilisateur pour vous initier au cluster IO.</a></p>
            </div>
    
            <!-- Support -->
            <div style="border:1px solid #009dab; border-radius:10px; padding:20px; margin-bottom:25px;">
              <h3 style="margin-top:0; color:#009dab;"> Support </h3>
              <p><a href="https://isdm-tickets.meso.umontpellier.fr/#login" style="color:#009dab; text-decoration:none;">Ouvrir ou répondre à un ticket via la plateforme de support</a></p>
              <p>Pour toute autre demande, vous pouvez également écrire un mail à la liste :<br><center><strong>isdm-calcul@umontpellier.fr</strong></center> </p>
            </div>
    
            <!-- Liste collaborative -->
            <div style="border:1px solid #009dab; border-radius:10px; padding:20px; margin-bottom:25px;">
              <h3 style="margin-top:0; color:#009dab;"> Liste collaborative</h3>
              <p>Avec cette ouverture de compte, vous êtes automatiquement inscrit à la liste :<br> <center><strong>meso-help@umontpellier.fr</strong></center></p>
              <p>Celle-ci permet de participer aux échanges de la communauté locale, suivre certains sujets, poser vos questions ou répondre aux interrogations des autres utilisateurs.</p>
              <!-- Mention désinscription -->
              <p>Vous pouvez vous désinscrire à tout moment <a href="https://listes.umontpellier.fr/sympa/signoff/meso-help" style="color:#009dab; text-decoration:none;">ici</a><br>
              </p>
            </div>
    
            <!-- Liste utilisateur -->
            <div style="border:1px solid #009dab; border-radius:10px; padding:20px; margin-bottom:25px;">
              <h3 style="margin-top:0; color:#009dab;"> Liste utilisateur</h3>
              <p>Avec cette ouverture de compte, vous êtes automatiquement inscrit à la liste :<br> <center> <strong>isdm-meso-utils@umontpellier.fr</strong></center></p>
              <p>Celle-ci permet des informations concernant le cluster IO (mises à jour, maintenances, nouveautés...).</p>
              <!-- Mention désinscription -->
              <p>Vous pouvez vous désinscrire à tout moment <a href="https://listes.umontpellier.fr/sympa/signoff/isdm-meso-utils" style="color:#009dab; text-decoration:none;">ici</a><br>
              </p>
            </div>
    
            <!-- FAQ -->
            <div style="border:1px solid #009dab; border-radius:10px; padding:20px; margin-bottom:25px;">
              <h3 style="margin-top:0; color:#009dab;"> Plus d’informations</h3>
              <p>Consultez notre FAQ : <a href="https://docs.meso.umontpellier.fr/fr/HPC/HPC-FAQ" style="color:#009dab; text-decoration:none;">https://docs.meso.umontpellier.fr/fr/HPC/HPC-FAQ</a></p>
            </div>
    
            <!-- Recommandations -->
            <p style="margin-top:40px; color:#000000;"><strong> Recommandations :</strong></p>
            <ul style="padding-left:20px; margin-bottom:30px; color:#333333;">
              <li><a href="https://docs.meso.umontpellier.fr/fr/HPC/NOTIONS/command#_passwd_changer_le_mot_de_passe_dun_utilisateur" style="color:#009dab; text-decoration:none;">Changez votre mot de passe dès la première connexion</a></li>
              <li>Attendez demain avant votre première connexion.</li>
              <li>Conservez ces informations en lieu sûr.</li>
              <li>Ne partagez pas vos identifiants.</li>
            </ul>
    
            <p style="margin-top:35px;">Cordialement,<br>L’équipe support IO</p>
          </td>
        </tr>
    
        <!-- Bande turquoise au-dessus du footer -->
        <tr>
          <td style="background-color:#009dab; height:6px;"></td>
        </tr>
    
        <!-- Footer -->
        <tr>
          <td style="background-color:#000000; color:#ffffff; text-align:center; padding:20px; font-size:14px;">
            <p style="margin:0;">Institut de Science des Données de Montpellier
                <br>Bât. 4 et 15 Case courrier 13004 <br> Place Eugène Bataillon 34095 Montpellier Cedex 5
                <br>04.67.14.47.89 | isdm@umontpellier.fr</p>
          </td>
        </tr>
      </table>
    </body>
    </html>""" #.format(prenom=args.prenom,nom=args.nom,user=args.user,passw=args.password)
        
        msg = EmailMessage()
        msg["From"] = avatar_name 
        msg["To"] = args.mail
        sujet_type = "Bienvenue sur Cluster IO"
        msg["Subject"] = sujet_type
        msg.set_content("")
        msg.add_alternative(body, subtype='html')
        server.send_message(msg)

def subscribe_mailing_lists(mail,user): 
    avatar_name = "isdm-clinique@umontpellier.fr"
    sympa_name = 'sympa@umontpellier.fr'
    
    if not all([smtp_server, user_name, password]):
        raise ValueError("Les variables SMTP_SERVER, USER_NAME et PASSWORD doivent être définies dans le fichier .env")
    else:
        print(f'All good !')
    
    context = ssl.create_default_context()
    
    maillists = ['isdm-meso-utils@umontpellier.fr','meso-help@umontpellier.fr']
    for maillist in maillists:
        print('Subscribing to ',maillist)
        with smtplib.SMTP(smtp_server, smtp_port, timeout=10) as server:
            server.starttls(context=context)
            server.login(user_name, password)
            body = ""
            msg = EmailMessage()
            msg["From"] = avatar_name 
            msg["To"] = sympa_name # args.mail
            sujet_type = f"ADD {maillist} {args.mail} {args.user}"
            msg["Subject"] = sujet_type
            msg.set_content("")
            server.send_message(msg)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(
                    prog='Create HTML Introduction to Cluter IO',
                    formatter_class=argparse.RawDescriptionHelpFormatter,
                    description='''
                    Take the name of someone and their password and voila ! 
                    Creates email.txt which you can cat email.txt or copy anyhow to your email HTML body
                    Prints out commands for SYMPA that you put into Sujet of the email''',
                    epilog='Great job :)')
    parser.add_argument("--cn", metavar="Amelia Meyer",required=True)
    parser.add_argument("--mail", metavar="amalia.meyer@uni.fr",required=True)
    parser.add_argument("--user", metavar="meyera",required=True)
    parser.add_argument("-s","--password", metavar="password",required=True)
    parser.add_argument("-t","--test", action="store_true", help="test compte ou non")
    args = parser.parse_args()

    load_dotenv() # needs .env file with smtp configuration - I didn't manage to make it work without it
    smtp_server = os.getenv("SMTP_SERVER")
    smtp_port = 587
    user_name = os.getenv("USER_NAME")
    password = os.getenv("PASSWORD")

    send_welcome(args.cn,args.mail,args.user,args.password)
    print('Welcome email sent')
    if args.test:
        print('Test account - doing nothing')
    else:
        subscribe_mailing_lists(args.mail,args.user)

    print('Done !')
