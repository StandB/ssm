import json
from flask import Flask, request, jsonify, render_template, redirect, url_for
from flask_sqlalchemy import SQLAlchemy
import bcrypt

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///db.sqlite3'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SECRET_KEY'] = 'ye'

db = SQLAlchemy(app)


class User(db.Model):
    id = db.Column('id', db.Integer, primary_key=True)
    username = db.Column(db.String(100), nullable=False)
    password = db.Column(db.String(100), nullable=False)

    def __init__(self, username, password):
        self.username = username
        self.password = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf8')

    @property
    def serialize(self):
        """ convert the object to JSON """
        return {'id': self.id, 'username': self.username}


# API endpoints
@app.route('/api/user', methods=['GET'])
def show_all():
    """ get all users """
    return json.dumps([x.serialize for x in User.query.all()])


@app.route('/api/user', methods=['POST'])
def add_user():
    """ add a user """
    user_json = request.json
    user = User(user_json['username'], user_json['password'])
    db.session.add(user)
    db.session.commit()
    return jsonify(user.serialize)


@app.route('/api/login', methods=['POST'])
def submit_login():
    """ submit login page """
    username = request.form['username']
    password = request.form['password'].encode("utf-8")

    user = db.session.query(User).filter_by(username=username).first()

    # todo: should result in error
    if user is None:
        return render_template('login.html')

    if bcrypt.checkpw(password, user.password.encode("utf-8")):
        return redirect(url_for('get_index'))
    else:
        # todo: should result in error
        return render_template('login.html')


# regular endpoins
@app.route('/login', methods=['GET'])
def get_login():
    """ get login page """
    return render_template('login.html')


@app.route('/', methods=['GET'])
def get_index():
    """ main page """
    return render_template('index.html')

if __name__ == '__main__':
    db.create_all()
    app.run(debug=True)
