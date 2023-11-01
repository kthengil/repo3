from flask import Flask, render_template, request, redirect, url_for, flash
from flask_sqlalchemy import SQLAlchemy
from flask_httpauth import HTTPBasicAuth
from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField
from wtforms.validators import DataRequired
from cryptography.fernet import Fernet
import secrets
from decouple import config

app = Flask(__name__)
app.config['SECRET_KEY'] = secrets.token_hex(16)

db_uri = config('SQLALCHEMY_DATABASE_URI')
secret_key = secrets.token_hex(16)
app.config['SQLALCHEMY_DATABASE_URI'] = db_uri
db = SQLAlchemy(app)
auth = HTTPBasicAuth()


key_file_path = 'encryption_key.key'

with open(key_file_path, 'rb') as key_file:
    encryption_key = key_file.read()
cipher = Fernet(encryption_key)



# Create a User model for the database
class User(db.Model):
    userid = db.Column(db.String(80), primary_key=True)
    displayname = db.Column(db.String(80), nullable=False)
    password = db.Column(db.String(255), nullable=False)

# Create the database and tables
with app.app_context():
    db.create_all()

# Registration and login forms
class RegistrationForm(FlaskForm):
    userid = StringField('UserID', validators=[DataRequired()])
    displayname = StringField('Display Name', validators=[DataRequired()])
    password = PasswordField('Password', validators=[DataRequired()])
    submit = SubmitField('Register')

class LoginForm(FlaskForm):
    userid = StringField('User ID', validators=[DataRequired()])
    password = PasswordField('Password', validators=[DataRequired()])
    submit = SubmitField('Login')

# Handle CSRF errors
@app.errorhandler(400)
def handle_csrf_error(e):
    return 'CSRF token missing or incorrect. Please try again.', 400

# Authenticate users with Flask-HTTPAuth
@auth.verify_password
def verify_password(username, password):
    user = User.query.filter_by(userid=username).first()
    if user:
        decrypted_password = cipher.decrypt(user.password.encode()).decode()
        if decrypted_password == password:
            return user

# Registration route
@app.route('/register', methods=['GET', 'POST'])
def register():
    form = RegistrationForm()
    reg_status=""
    reg_message=""

    if form.validate_on_submit():
        
        user = User.query.filter_by(userid=form.userid.data).first()

        if user is None:
            encrypted_password = cipher.encrypt(form.password.data.encode()).decode()

            new_user = User(userid=form.userid.data, displayname=form.displayname.data, password=encrypted_password)
            db.session.add(new_user)
            db.session.commit()
            reg_status='success_message'
            reg_message='Registration successful. You can now log in.'
        else:
            reg_status='failed_message'
            reg_message='Registration successful. You can now log in.'
    return render_template('register.html', form=form, reg_status=reg_status)

# Protected route
@app.route('/protected')
@auth.login_required
def protected():
    return f'Hello, {auth.current_user().displayname}! This route is protected.'

if __name__ == '__main__':
    app.run()
