import bcrypt
from flask import Flask, request, \
    render_template, redirect, url_for, g, send_from_directory, abort, Blueprint, current_app
from flask_sqlalchemy import SQLAlchemy
from flask_login import logout_user, login_required
from werkzeug.utils import secure_filename
from app.models import User, Post

from app import db

routes = Blueprint('routes', __name__)

# regular endpoints
@routes.route('/login', methods=['GET'])
def get_login():
    """ get login page """
    return render_template('login.html')


@routes.route('/logout')
def logout():
    logout_user()
    return redirect(url_for('routes.get_index'))


@routes.route('/', methods=['GET'])
@login_required
def get_index():
    """ main page """
    return render_template('index.html')


@routes.route('/users', methods=['GET'])
@login_required
def get_users():
    users = [x.serialize for x in User.query.all()]
    return render_template('users.html', users=users)


@routes.route('/posts', methods=['GET'])
@login_required
def get_own_posts():
    posts = [x.serialize for x in Post.query.filter_by(user_id=g.user.id).all()]
    return render_template('posts.html', posts=posts, create_post=True)

@routes.route('/feed', methods=['GET'])
@login_required
def get_feed():
    following = list(map(lambda x: x.id, g.user.follows))
    posts = Post.query.filter(Post.user_id.in_(following)).order_by(db.desc(Post.datetime)).all()
    return render_template('posts.html', posts=posts, create_post=False)

@routes.route('/post/<id>', methods=['GET'])
@login_required
def get_post(id):
    post = [Post.query.filter_by(id=id).first()]
    return render_template('posts.html', posts=post)


@routes.route('/createpost', methods=['GET'])
@login_required
def create_post_page():
    return render_template('createpost.html')


@routes.route('/user/<id>', methods=['GET'])
@login_required
def get_profile(id):
    user = User.query.filter_by(id=id).first()
    post = Post.query.filter_by(user_id=id).first()
    following = False
    for following_user in g.user.follows:
        if following_user.id == int(id):
            following = True

    if user is None:
        abort(404)
    return render_template('profile.html', user=user.serialize, post=post, following=following)

@routes.route('/user/<id>', methods=['POST'])
@login_required
def follow_user(id):
    user = User.query.filter_by(id=id).first()
    post = Post.query.filter_by(user_id=id).first()
    following = False

    if user is None:
        abort(404)

    me = User.query.filter_by(id=g.user.id).first()

    if user not in me.follows:
        me.follows.append(user)
        following=True

    db.session.commit()

    return render_template('profile.html', user=user.serialize, post=post, following=following)

@routes.route('/editprofile', methods=['GET'])
@login_required
def edit_profile():
    return render_template('editprofile.html')

@routes.route('/uploads/<filename>')
def uploaded_file(filename):
    return send_from_directory(current_app.config['UPLOAD_FOLDER'], filename)


@routes.route('/adduser', methods=['GET'])
@login_required
def add_user_page():
    return render_template('adduser.html')