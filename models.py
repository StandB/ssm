from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()

class Post(db.Model):
    id = db.Column('id', db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    title = db.Column(db.String(50), nullable=False)
    content = db.Column(db.String(500), nullable=False)
    datetime = db.Column(db.DateTime, nullable=False)
    user = db.relationship("User", back_populates="posts")

    def __init__(self, title, content):
        self.title = title
        self.content = content
        self.datetime = datetime.datetime.now()

    @property
    def serialize(self):
        """ convert the object to JSON """
        return {'id': self.id, 'user_id': self.user_id,
                'title': self.title, 'content': self.content, 
                'datetime': self.datetime, 'user': self.user}

follows = db.Table('follows',
    db.Column('user_id', db.Integer, db.ForeignKey('user.id'), primary_key=True),
    db.Column('follows_id', db.Integer, db.ForeignKey('user.id'), primary_key=True)
)

class User(db.Model):
    id = db.Column('id', db.Integer, primary_key=True)
    username = db.Column(db.String(100), nullable=False)
    password = db.Column(db.String(100), nullable=False)
    avatar = db.Column(db.String(100), nullable=False)
    description = db.Column(db.String(300), nullable=False)
    follows = db.relationship('User', secondary=follows, primaryjoin=id==follows.c.user_id,secondaryjoin=id==follows.c.follows_id)
    posts = db.relationship('Post', back_populates="user", lazy='dynamic')

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
        return {'id': self.id, 'username': self.username, 'avatar': self.avatar, 'description': self.description, 'follows': self.follows}

