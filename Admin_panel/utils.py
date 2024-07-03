import os
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

import jwt
import secrets
from datetime import datetime, timedelta
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials, OAuth2PasswordBearer
from fastapi import Depends, HTTPException
from dotenv import load_dotenv

load_dotenv()
secret_key = os.environ.get('SECRET')
algorithm = 'HS256'
security = HTTPBearer()





def generate_token_stuff(stuff_id: int,role_name:str):
    jti_access = str(secrets.token_urlsafe(32))
    jti_refresh = str(secrets.token_urlsafe(32))
    data_access_token = {
        'token_type': 'access',
        'exp': datetime.utcnow() + timedelta(minutes=30),
        'stuff_id': stuff_id,
        'role_name': role_name,
        'jti':jti_access
    }
    data_refresh_token = {
        'token_type':'refresh',
        'exp': datetime.utcnow() + timedelta(minutes=30),
        'stuff_id':stuff_id,
        'role_name':role_name,
        'jti':jti_refresh
    }
    access_token = jwt.encode(data_access_token,secret_key,algorithm)
    refresh_token = jwt.encode(data_refresh_token,secret_key,algorithm)

    return {
     'access_token': access_token,
     'refresh_token': refresh_token
    }



def verify_stuff_token(credentials: HTTPAuthorizationCredentials = Depends(security)):
    try:
        token = credentials.credentials
        secret_key = os.environ.get('SECRET')

        payload =jwt.decode(token, secret_key,algorithms=['HS256'])
        try:
            if payload['stuff_id']:
                return payload
            else:
                raise HTTPException(status_code=401, detail='Not allowed')
        except KeyError:
            raise HTTPException(status_code=401, detail='Not allowed')
    except jwt.ExpiredSignatureError:
        return HTTPException(status_code=401, detail="Token has expired")
    except jwt.InvalidTokenError:
        return HTTPException(status_code=401, detail="Invalid token")


def send_mail(receiver_email, phone,password):
    # Email configuration
    sender_email = os.getenv('SENDER_EMAIL')
    message = (f"Hello Dear,  Your Login Info:\n 📞Phone = {phone} \n 🔐Password = {password}. \n"
               f" \n We will suggest after login change your password")


    # SMTP server configuration for gmail
    smtp_server = 'smtp.gmail.com'
    smtp_port = 587
    smtp_username = os.environ.get('SENDER_EMAIL')
    smtp_password = os.environ.get('SMTP_CODE')

    # Create a multipart message and set headers
    email_message = MIMEMultipart()
    email_message['From'] = sender_email
    email_message['To'] = receiver_email
    email_message['Subject'] = receiver_email

    email_message.attach(MIMEText(message, 'plain'))

    with smtplib.SMTP(smtp_server, smtp_port) as server:
        server.starttls()
        server.login(smtp_username, smtp_password)

        server.send_message(email_message)
