from flask import Flask
from flask_sqlalchemy import SQLAlchemy
import config.config as config_app

app = Flask(__name__)
config_app.config_app(app)
db = SQLAlchemy(app)