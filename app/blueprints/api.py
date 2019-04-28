import json, uuid, os, time, datetime, bcrypt
from flask import Flask, request, jsonify, \
    render_template, redirect, url_for, g, send_from_directory, abort, Blueprint, current_app
from flask_sqlalchemy import SQLAlchemy
from flask_login import login_user, logout_user, current_user, \
    login_required, LoginManager
from werkzeug import secure_filename
from app.models import User, Post

from app import db

api = Blueprint('api', __name__)

@api.route('/api/user', methods=['POST'])
@login_required
def add_user():
    """ add a user """
    username = request.form.get('username')
    password = request.form.get('password')
    if password is "" or username is "":
        return redirect(url_for('routes.add_user_page'))

    avatar = 'default.jpg'
    f = request.files.get('file')
    if f is not None:
        avatar = uuid.uuid4().hex + ".jpg"  
        f.save(os.path.join(current_app.config['UPLOAD_FOLDER'], avatar))

    user = User(username, password, avatar)
    db.session.add(user)
    db.session.commit()
    return redirect(url_for('routes.get_users'))


# native forms doesn't support PUT so used different endpoint :/
@api.route('/api/user/update', methods=['POST'])
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
        return redirect(url_for('routes.get_login'))

    #update description
    user.description = description

    # update avatar of user
    f = request.files.get('file', None)
    if f:
        user.avatar = uuid.uuid4().hex + ".jpg"  
        f.save(os.path.join(current_app.config['UPLOAD_FOLDER'], user.avatar))

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
    return redirect(url_for('routes.get_profile', id=user.id))


@login_required
@api.route('/api/post', methods=['POST'])
def create_post():
    """ create post """
    title = request.form.get('title')
    content = request.form.get('content')
    
    if title is '' or content is '':
        return redirect(url_for('routes.create_post_page'))
    
    post = Post(title, content)
    post.user = g.user
    db.session.add(post)
    db.session.commit()
    return redirect(url_for('routes.get_own_posts'))


@api.route('/api/login', methods=['POST'])
def submit_login():
    """ submit login page """
    username = request.form['username']
    password = request.form['password'].encode("utf-8")

    user = db.session.query(User).filter_by(username=username).first()

    if user is None:
        return redirect(url_for('routes.get_login'))

    if bcrypt.checkpw(password, user.password.encode("utf-8")):
        login_user(user)
        return redirect(request.args.get('next') or url_for('routes.get_index'))
    else:
        return redirect(url_for('routes.get_login'))
