import os
from flask import Flask, request, jsonify, render_template, session
from dotenv import load_dotenv
from openai import OpenAI
import stripe
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

# Remove these debug print statements
print("Current working directory:", os.getcwd())
print("Checking if .env exists:", os.path.exists('.env'))

with open('.env', 'r') as f:
    print("Contents of .env file:")
    print(f.read())

load_dotenv()
print("After load_dotenv:")
print("OPENAI_API_KEY:", os.getenv('OPENAI_API_KEY'))
print("FLASK_ENV:", os.getenv('FLASK_ENV'))
print("FLASK_APP:", os.getenv('FLASK_APP'))

print(f"OpenAI API Key: {os.getenv('OPENAI_API_KEY')[:10]}...")  # Print first 10 chars for safety

client = OpenAI(api_key=os.getenv('OPENAI_API_KEY')) 