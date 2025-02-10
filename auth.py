from flask import Blueprint, request, render_template, redirect, url_for, flash
from flask_login import login_user, logout_user, login_required
from werkzeug.security import generate_password_hash, check_password_hash
from models import User, db, log_access
from datetime import datetime

auth = Blueprint('auth', __name__)

@auth.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        
        user = User.query.filter_by(email=email).first()
        if user and check_password_hash(user.password_hash, password):
            login_user(user)
            user.last_login = datetime.utcnow()
            db.session.commit()
            log_access('login')
            return redirect(url_for('home'))
        
        flash('Please check your login details and try again.')
    return render_template('login.html')

@auth.route('/logout')
@login_required
def logout():
    log_access('logout')
    logout_user()
    return redirect(url_for('auth.login')) 