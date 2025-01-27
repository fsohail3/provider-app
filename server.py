import os
from flask import Flask, request, jsonify, render_template, session
from dotenv import load_dotenv
from openai import OpenAI
import stripe
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

load_dotenv()  # This will work locally but skip if file not found

client = OpenAI(api_key=os.getenv('OPENAI_API_KEY'))
MODEL_NAME = os.getenv("MODEL_NAME", "gpt-4-turbo-preview")
stripe.api_key = os.getenv('STRIPE_SECRET_KEY')

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///healthcare.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SECRET_KEY'] = os.urandom(24)
db = SQLAlchemy(app)

@app.route('/')
def home():
    return render_template('index.html') 