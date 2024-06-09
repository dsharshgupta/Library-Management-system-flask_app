from flask_sqlalchemy import SQLAlchemy
from flask import Flask
from flask_login import LoginManager
from os import path


db = SQLAlchemy()

def create_all():
    app = Flask(__name__)
    app.config['SECRET_KEY'] = "abcdefg"
    app.config['SQLALCHEMY_DATABASE_URI'] = "sqlite:///library.db"

    db.init_app(app)


    from .database import User
    from .routes import route

    app.register_blueprint(route, url_prefix='/')

    create_database(app)


    login_manager = LoginManager()
    login_manager.init_app(app)
    login_manager.login_view = 'route.login'

    @login_manager.user_loader
    def load_user(id):
        return User.query.get(int(id))
    
    return app
    


def create_database(app):
    if not path.exists("app/library"):
        with app.app_context():
            db.create_all()
