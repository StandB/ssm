# Import flask and template operators
from flask import Flask, render_template, g

# Import SQLAlchemy
from flask_sqlalchemy import SQLAlchemy

from flask_login import login_user, logout_user, current_user, \
    login_required, LoginManager

# Define the WSGI application object
app = Flask(__name__)

# Configurations
app.config.from_object('config')

# Define the database object which is imported
# by modules and controllers
db = SQLAlchemy(app)

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'routes.get_login'

@app.before_first_request
def setup():
   # Recreate database each time for demo
    from .models import User
    user = db.session.query(User).filter_by(username='root').first()
    if user is not None:
        return
    me = User('root', 'root', 'default.jpg')
    notme = User('root1', 'root1', 'default1.png')
    db.session.add(me)
    db.session.add(notme)
    db.session.commit()


# Sample HTTP error handling
@app.errorhandler(404)
def not_found(error):
    return render_template('404.html'), 404

@login_manager.user_loader
def load_user(id):
    from .models import User
    return User.query.get(int(id))

@app.before_request
def before_request():
    g.user = current_user

# Import a module / component using its blueprint handler variable (mod_auth)
from app.blueprints.api import api
from app.blueprints.routes import routes

# Register blueprint(s)
app.register_blueprint(api)
app.register_blueprint(routes)
# app.register_blueprint(xyz_module)
# ..

# Build the database:
# This will create the database file using SQLAlchemy
db.create_all()