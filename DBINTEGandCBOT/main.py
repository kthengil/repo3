from flask import Flask, render_template, redirect, url_for
from flask_wtf import FlaskForm
from wtforms import StringField, TextAreaField, SubmitField, RadioField, SelectField
from wtforms.validators import DataRequired, Email
from decouple import config
from flask_sqlalchemy import SQLAlchemy
import secrets


app = Flask(__name__)
app.config['SECRET_KEY'] = secrets.token_hex(16)
db_uri = config('SQLALCHEMY_DATABASE_URI')
secret_key = secrets.token_hex(16)
app.config['SQLALCHEMY_DATABASE_URI'] = db_uri
db = SQLAlchemy(app)


class Feedback(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(80), nullable=False)
    email = db.Column(db.String(120), nullable=False)
    message = db.Column(db.Text, nullable=False)

class TrainingRegistration(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(80), nullable=False)
    email = db.Column(db.String(120), nullable=False)
    preferred_timing = db.Column(db.String(20), nullable=False)
    training_title = db.Column(db.String(100), default='Training125')


with app.app_context():
    db.create_all()


class FeedbackForm(FlaskForm):
    name = StringField('Name', validators=[DataRequired()])
    email = StringField('Email', validators=[DataRequired(), Email()])
    message = TextAreaField('Feedback', validators=[DataRequired()])
    submit = SubmitField('Submit Feedback')

class TrainingRegistrationForm(FlaskForm):
    name = StringField('Full Name', validators=[DataRequired()])
    email = StringField('Email', validators=[DataRequired(), Email()])
    preferred_timing = RadioField('Preferred Timing', choices=[('TUE', '2023 NOV 7'), ('THU', '023 NOV 9')])
    submit = SubmitField('Submit')

@app.route('/feedback', methods=['GET', 'POST'])
def feedback():
    form = FeedbackForm()
    feedbackstatus="Failed"
    if form.validate_on_submit():
        name = form.name.data
        email = form.email.data
        message = form.message.data

        # Save the feedback to the database
        feedback = Feedback(name=name, email=email, message=message)
        db.session.add(feedback)
        db.session.commit()

        ffeedbackstatus="Success"

        return redirect(url_for('feedback'))

    return render_template('feedback.html', form=form, feedbackstatus=feedbackstatus)
   
@app.route('/feedbackview')
def feedbackview():
    feedback_entries = Feedback.query.all()
    return render_template('feedbackview.html', feedback_entries=feedback_entries)

@app.route('/training_registration', methods=['GET', 'POST'])
def training_registration():
    form = TrainingRegistrationForm()
    if form.validate_on_submit():
        name = form.name.data
        email = form.email.data
        preferred_timing = form.preferred_timing.data
        training_title = 'Training125'  # Set the training title

        # Validate email domain
        allowed_domains = ['company.com', 'company2.com']
        domain = email.split('@')[1]
        if domain not in allowed_domains:
            return "Invalid email domain. Please use 'company.com' or 'company2.com'."


        existing_registration = TrainingRegistration.query.filter_by(email=email, training_title=training_title).first()

        if existing_registration:

            return "This email is already registered for Training125."
        else:
            # Store the registration details in the database
            registration = TrainingRegistration(name=name, email=email, preferred_timing=preferred_timing, training_title=training_title)
            db.session.add(registration)
            db.session.commit()
            return "Registration successful"

    registered_users = TrainingRegistration.query.filter_by(training_title='Training125').all()
    return render_template('training_registration.html', form=form, registered_users=registered_users)


if __name__ == '__main__':
    app.run(debug=True)