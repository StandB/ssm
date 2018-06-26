import json
from flask import Flask, request, jsonify
from flask_sqlalchemy import SQLAlchemy

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///db.sqlite3'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SECRET_KEY'] = 'ye'

db = SQLAlchemy(app)


class User(db.Model):
    id = db.Column('id', db.Integer, primary_key=True)
    name = db.Column(db.String(100))

    def __init__(self, name):
        self.name = name

    @property
    def serialize(self):
        """ convert the object to JSON """
        return {'id': self.id, 'name': self.name}


@app.route('/user', methods=['GET'])
def show_all():
    """ get all users """
    return json.dumps([x.serialize for x in User.query.all()])


@app.route('/user', methods=['POST'])
def add_user():
    """ add a user """
    user_json = request.json
    user = User(user_json['name'])
    db.session.add(user)
    db.session.commit()
    return jsonify(user.serialize)

if __name__ == '__main__':
    db.create_all()
    app.run(debug=True)
