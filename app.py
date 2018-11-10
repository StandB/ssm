import json, bcrypt, uuid, os, time
from flask import Flask, request, jsonify, \
    render_template, redirect, url_for, g, send_from_directory, abort
from flask_sqlalchemy import SQLAlchemy
from flask_login import login_user, logout_user, current_user, \
    login_required, LoginManager
from werkzeug import secure_filename

upload_folder = 'avatars'
upload_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), upload_folder)

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///db.sqlite3'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['UPLOAD_FOLDER'] = upload_path
app.config['SECRET_KEY'] = 'ye'

db = SQLAlchemy(app)

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'get_login'


@app.errorhandler(404)
def page_not_found(error):
    return render_template('404.html'), 404


@login_manager.user_loader
def load_user(id):
    return User.query.get(int(id))


class User(db.Model):
    id = db.Column('id', db.Integer, primary_key=True)
    username = db.Column(db.String(100), nullable=False)
    password = db.Column(db.String(100), nullable=False)
    avatar = db.Column(db.String(100), nullable=False)
    description = db.Column(db.String(300), nullable=False)
    posts = db.relationship('Post', backref='user', lazy='dynamic')

    def __init__(self, username, password, avatar):
        self.username = username
        self.password = bcrypt.hashpw(
            password.encode('utf-8'),
            bcrypt.gensalt()
        ).decode('utf8')
        self.description = 'Nothing here yet :/'
        self.avatar = avatar

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
        return {'id': self.id, 'username': self.username, 'avatar': self.avatar, 'description': self.description}



class Post(db.Model):
    id = db.Column('id', db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    title = db.Column(db.String(50), nullable=False)
    content = db.Column(db.String(500), nullable=False)
    date = db.Column(db.String(500), nullable=False)

    def __init__(self, title, content):
        self.title = title
        self.content = content
        self.date = time.strftime("%d/%m/%Y")

    @property
    def serialize(self):
        """ convert the object to JSON """
        return {'id': self.id, 'user_id': self.user_id,
                'title': self.title, 'content': self.content}


@app.route('/api/users', methods=['POST'])
@login_required
def add_user():
    """ add a user """
    username = request.form.get('username')
    password = request.form.get('password')
    if password is "" or username is "":
        return redirect(url_for('add_user_page'))

    avatar = 'default.jpg'
    f = request.files.get('file')
    if f is not None:
        avatar = uuid.uuid4().hex + ".jpg"  
        f.save(os.path.join(app.config['UPLOAD_FOLDER'], avatar))

    user = User(username, password, avatar)
    db.session.add(user)
    db.session.commit()
    return redirect(url_for('get_users'))


# native forms doesn't support PUT so used different endpoint :/
@app.route('/api/users/update', methods=['POST'])
@login_required
def update_user():
    """ update a user """
    id = request.form.get('id')
    username = request.form.get('username')
    password = request.form.get('password')
    description = request.form.get('description')

    # get existing user
    user = db.session.query(User).filter_by(id=id).first()
    # auth check
    if user is None or g.user.password is not user.password:
        return redirect(url_for('get_login'))

    #update description
    user.description = description

    # update avatar of user
    f = request.files.get('file')
    if f is not None:
        user.avatar = uuid.uuid4().hex + ".jpg"  
        f.save(os.path.join(app.config['UPLOAD_FOLDER'], user.avatar))

    # username always has value so update right away
    user.username = username
    # if the password isn't set it means we don't want to update it. So update if set
    if password is not "" and password is not None:
        # encrypt
        user.password = bcrypt.hashpw(
            password.encode('utf-8'),
            bcrypt.gensalt()
        ).decode('utf8')

    db.session.commit()
    return redirect(url_for('get_profile', id=user.id))


@login_required
@app.route('/api/posts', methods=['POST'])
def create_post():
    """ create post """
    title = request.form.get('title')
    content = request.form.get('content')
    
    if title is '' or content is '':
        return redirect(url_for('create_post_page'))
    
    post = Post(title, content)
    post.user = g.user
    db.session.add(post)
    db.session.commit()
    return redirect(url_for('get_own_posts'))


@app.route('/api/login', methods=['POST'])
def submit_login():
    """ submit login page """
    username = request.form['username']
    password = request.form['password'].encode("utf-8")

    user = db.session.query(User).filter_by(username=username).first()

    if user is None:
        return redirect(url_for('get_login'))

    if bcrypt.checkpw(password, user.password.encode("utf-8")):
        login_user(user)
        return redirect(request.args.get('next') or url_for('get_index'))
    else:
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


@app.route('/createpost', methods=['GET'])
@login_required
def create_post_page():
    return render_template('createpost.html')


@app.route('/users/<id>', methods=['GET'])
@login_required
def get_profile(id):
    user = User.query.filter_by(id=id).first()
    post = Post.query.filter_by(user_id=id).first()
    if user is None:
        abort(404)
    return render_template('profile.html', user=user.serialize, post=post)

@app.route('/editprofile', methods=['GET'])
@login_required
def edit_profile():
    return render_template('editprofile.html')

@app.route('/uploads/<filename>')
def uploaded_file(filename):
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)


@app.route('/adduser', methods=['GET'])
@login_required
def add_user_page():
    return render_template('adduser.html')


def create_root_user():
    user = db.session.query(User).filter_by(username='root').first()
    if user is not None:
        return
    me = User('root', 'root', 'default.jpg')
    db.session.add(me)
    db.session.commit()


if __name__ == '__main__':
    db.create_all()
    create_root_user()
    app.run(debug=True)
