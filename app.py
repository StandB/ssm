import json
import bcrypt
from flask import Flask, request, jsonify, \
    render_template, redirect, url_for, g
from flask_sqlalchemy import SQLAlchemy
from flask_login import login_user, logout_user, current_user, \
    login_required, LoginManager

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///db.sqlite3'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SECRET_KEY'] = 'ye'

db = SQLAlchemy(app)

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'get_login'


@login_manager.user_loader
def load_user(id):
    return User.query.get(int(id))


class User(db.Model):
    id = db.Column('id', db.Integer, primary_key=True)
    username = db.Column(db.String(100), nullable=False)
    password = db.Column(db.String(100), nullable=False)
    posts = db.relationship('Post', backref='user', lazy='dynamic')

    def __init__(self, username, password):
        self.username = username
        self.password = bcrypt.hashpw(
            password.encode('utf-8'),
            bcrypt.gensalt()
        ).decode('utf8')

    def is_authenticated(self):
        return True

    def is_active(self):
        return True

    def is_anonymous(self):
        return False

    def get_id(self):
        return str(self.id).encode("utf-8").decode("utf-8")

    @property
    def serialize(self):
        """ convert the object to JSON """
        return {'id': self.id, 'username': self.username}


class Post(db.Model):
    id = db.Column('id', db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    title = db.Column(db.String(50), nullable=False)
    content = db.Column(db.String(500), nullable=False)

    def __init__(self, title, content):
        self.title = title
        self.content = content

    @property
    def serialize(self):
        """ convert the object to JSON """
        return {'id': self.id, 'user_id': self.user_id,
                'title': self.title, 'content': self.content}


@app.route('/api/users', methods=['POST'])
def add_user():
    """ add a user """
    user_json = request.json
    user = User(user_json['username'], user_json['password'])
    db.session.add(user)
    db.session.commit()
    return jsonify(user.serialize)


@login_required
@app.route('/api/posts', methods=['POST'])
def create_post():
    """ create post """
    title = request.form['title']
    content = request.form['content']
    post = Post(title, content)
    post.user = g.user
    db.session.add(post)
    db.session.commit()
    return redirect(url_for('get_index'))


@app.route('/api/login', methods=['POST'])
def submit_login():
    """ submit login page """
    username = request.form['username']
    password = request.form['password'].encode("utf-8")

    user = db.session.query(User).filter_by(username=username).first()

    # todo: should result in error
    if user is None:
        return redirect(url_for('get_login'))

    if bcrypt.checkpw(password, user.password.encode("utf-8")):
        login_user(user)
        return redirect(request.args.get('next') or url_for('get_index'))
    else:
        # todo: should result in error
        return redirect(url_for('get_login'))


@app.before_request
def before_request():
    g.user = current_user


# regular endpoints
@app.route('/login', methods=['GET'])
def get_login():
    """ get login page """
    return render_template('login.html')


@app.route('/logout')
def logout():
    logout_user()
    return redirect(url_for('get_index'))


@app.route('/', methods=['GET'])
@login_required
def get_index():
    """ main page """
    return render_template('index.html')


@app.route('/users', methods=['GET'])
@login_required
def get_users():
    users = [x.serialize for x in User.query.all()]
    return render_template('users.html', users=users)


@app.route('/posts', methods=['GET'])
@login_required
def get_own_posts():
    posts = [x.serialize for x in Post.query.filter_by(user_id=g.user.id).all()]
    return render_template('posts.html', posts=posts)

if __name__ == '__main__':
    db.create_all()
    app.run(debug=True)
