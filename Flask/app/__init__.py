import os
import secrets

from flask import Flask
from flask_session import Session
from app.routes import main

def create_app():
    app = Flask(
        __name__,
        template_folder=os.path.join(os.path.dirname(os.path.abspath(__file__)), "templates"),
        static_folder=os.path.join(os.path.dirname(os.path.abspath(__file__)), "static"),
    )

    app.secret_key = secrets.token_hex(16)

    # Flask-Session config
    app.config["SESSION_TYPE"] = "filesystem"
    app.config["SESSION_PERMANENT"] = False

    Session(app)

    app.register_blueprint(main)
    return app
