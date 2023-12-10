from flask import Flask, render_template, request, redirect, url_for, session

from flask_wtf import FlaskForm
from wtforms import StringField, TextAreaField, SubmitField, IntegerField
from wtforms.validators import DataRequired
import json


app = Flask(__name__)
app.config['SECRET_KEY'] = 'f9539c7803b9c1619a88b7132c7297b3507142c4972446b7'

class SearchForm(FlaskForm):
    search_query = StringField('Search', validators=[DataRequired()])
    submit = SubmitField('Go')

class SubmitForm(FlaskForm):
    serialno = IntegerField('SerialNo', validators=[DataRequired()])
    category = StringField('Category', validators=[DataRequired()])
    scenario = StringField('Scenario', validators=[DataRequired()])
    command = StringField('Command', validators=[DataRequired()])
    description = TextAreaField('Description', validators=[DataRequired()])
    contributor = StringField('Contributor', validators=[DataRequired()])
    submit = SubmitField('Submit')

# Load data from cmddb.json
def load_data():
    try:
        with open('cmddb.json', 'r') as file:
            data = json.load(file)
    except (FileNotFoundError, json.JSONDecodeError):
        data = []
    return data

# Save data to cmddb.json
def save_data(data):
    with open('cmddb.json', 'w') as file:
        json.dump(data, file, indent=2)

@app.route('/')
def index():
    session.pop('search_results', None)
    search_form = SearchForm()
    return render_template('search.html', search_form=search_form)


@app.route('/search', methods=['POST'])
def search():
    search_form = SearchForm(request.form)
    if search_form.validate_on_submit():
        search_query = search_form.search_query.data.lower().strip()
        data = load_data()
        search_form.search_query.data = ""

        results = [
        cmd for cmd in data
            if any(
                search_query in str(value).lower().strip()
                for key, value in cmd.items()
                if key in ['Category', 'Scenario', 'Command', 'Description']
            ) and cmd.get('published', False)
        ]

        print("Search Query:", search_query)
        print("Results:", results)


        return render_template('search.html', search_form=search_form, results=results)

    return render_template('search.html', search_form=search_form, results=False)






@app.route('/view/<int:serial_number>')
def view(serial_number):
    data = load_data()

    # Find the command with the specified SerialNo
    cmd = next((cmd for cmd in data if cmd.get('SerialNo') == serial_number), None)

    if cmd and cmd.get('published', False):
        return render_template('view.html', cmd=cmd, serial_number=serial_number)
    else:
        return "This command is not published or does not exist."
    

@app.route('/submit', methods=['GET', 'POST'])
def submit():
    submit_form = SubmitForm()
    data = load_data()
    last_serial_number = data[-1]['SerialNo'] if data else 1000
    submit_form.serialno.data=len(data)+ 1
    if submit_form.validate_on_submit():
        new_cmd = {
            'SerialNo': submit_form.serialno.data,
            'Category': submit_form.category.data,
            'Scenario': submit_form.scenario.data,
            'Command': submit_form.command.data,
            'Description': submit_form.description.data,
            'Contributor': submit_form.contributor.data,  
            'published': False
        }

        data.append(new_cmd)
        save_data(data)
        print("Submitted Data")
        return redirect(url_for('index'))
    else:
        print("Submit Validation Failed")
        for field, errors in submit_form.errors.items():
            print(f"Field: {field}, Errors: {', '.join(errors)}")
    return render_template('submit.html', submit_form=submit_form)

@app.route('/admin')
def admin():
    data = load_data()
    
    published_commands = [cmd for cmd in data if cmd.get('published', False)]
    pending_approval_commands = [cmd for cmd in data if not cmd.get('published', False)]
    
    return render_template('admin.html', published_commands=published_commands, pending_approval_commands=pending_approval_commands)


from flask import redirect, url_for

@app.route('/approve/<int:serial_number>')
def approve(serial_number):
    data = load_data()
    published_commands = [cmd for cmd in data if cmd.get('published', False)]
    pending_approval_commands = [cmd for cmd in data if not cmd.get('published', False)]

    # Check if the serial_number is valid for pending_approval_commands
    if any(cmd.get('SerialNo') == serial_number for cmd in pending_approval_commands):
        # Find the original index in the data
        original_index = next((i for i, cmd in enumerate(data) if cmd.get('SerialNo') == serial_number), None)

        print(f"Approving command with SerialNo {serial_number}, published status: {data[original_index].get('published')}")

        # Check if the command is not already published
        if not data[original_index].get('published', False):
            data[original_index]['published'] = True
            save_data(data)
            return redirect(url_for('admin'))
        else:
            return "This command is already published."
    else:
        print(f"Invalid SerialNo for approval: {serial_number}")

    return "Invalid SerialNo for approval."





@app.route('/reject/<int:serial_number>')
def reject(serial_number):
    data = load_data()
    pending_approval_commands = [cmd for cmd in data if not cmd.get('published', False)]

    # Check if the serial_number is valid for pending_approval_commands
    if any(cmd.get('SerialNo') == serial_number for cmd in pending_approval_commands):
        # Find the original index in the data
        original_index = next((i for i, cmd in enumerate(data) if cmd.get('SerialNo') == serial_number), None)

        print(f"Rejecting command with SerialNo {serial_number}")

        # Remove the command from the data
        del data[original_index]
        save_data(data)

        return redirect(url_for('admin'))
    else:
        print(f"Invalid SerialNo for rejection: {serial_number}")

    return "Invalid SerialNo for rejection."


if __name__ == '__main__':
    app.run(debug=True)
