from flask import Flask, render_template, redirect, request, send_from_directory
from flask_sqlalchemy import SQLAlchemy
from flask_user import current_user, login_required, UserManager, UserMixin, SQLAlchemyAdapter, roles_required
import config.config as config_app
import config.paths
import os
import datetime
import re

app = Flask(__name__)
config_app.config_app(app)
db = SQLAlchemy(app)

class User(db.Model, UserMixin):
    __tablename__ = 'user'
    id = db.Column(db.Integer, primary_key = True)

    username = db.Column(db.String(50), nullable = True, unique = True)
    password = db.Column(db.String(255), nullable = False, server_default = '')
    active = db.Column(db.Boolean(), nullable = False, server_default = '0')
    email = db.Column(db.String(255), nullable = False, unique = True)
    email_confirmed_at = db.Column(db.DateTime())

    first_name = db.Column(db.String(100), nullable = False, server_default = '')
    last_name = db.Column(db.String(100), nullable = False, server_default = '')
    avatar = db.Column(db.String(50), nullable = False, server_default = '')

    seen = db.Column(db.DateTime())

    # Relationships
    roles = db.relationship('Role', secondary = 'user_roles', backref = db.backref('users', lazy='dynamic'))
    news = db.relationship("NewsArticle", backref = "author")
    news_tags = db.relationship("NewsTag", backref = "author")

class Role(db.Model):
    id = db.Column(db.Integer(), primary_key = True)
    name = db.Column(db.String(80), unique = True)

class UserRoles(db.Model):
    id = db.Column(db.Integer(), primary_key=True)
    user_id = db.Column(db.Integer(), db.ForeignKey('user.id', ondelete='CASCADE'))
    role_id = db.Column(db.Integer(), db.ForeignKey('role.id', ondelete='CASCADE'))

class UserInvitation(db.Model):
    __tablename__ = 'user_invite'
    id = db.Column(db.Integer, primary_key = True)
    email = db.Column(db.String(255), nullable = False)
    invited_by_user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    token = db.Column(db.String(100), nullable = False, server_default = '')

article_tags = db.Table("article_tags", db.Column("article_id", db.Integer, db.ForeignKey("news.id")), db.Column("tag_id", db.Integer, db.ForeignKey("newstags.id")))

class NewsArticle(db.Model):
    __tablename__ = "news"
    id = db.Column(db.Integer, primary_key = True)
    name = db.Column(db.String(255), nullable = False, unique = True)
    created = db.Column(db.DateTime())
    author_id = db.Column(db.Integer(), db.ForeignKey('user.id', ondelete = 'CASCADE'))
    tags = db.relationship("NewsTag", secondary = article_tags)

class NewsTag(db.Model):
    __tablename__ = "newstags"
    id = db.Column(db.Integer, primary_key = True)
    name = db.Column(db.String(40), nullable = False, unique = True)
    description = db.Column(db.String(400), nullable = False)
    created = db.Column(db.DateTime())
    author_id = db.Column(db.Integer(), db.ForeignKey('user.id', ondelete = 'CASCADE'))
    articles = db.relationship("NewsArticle", secondary = article_tags)

user_manager = UserManager(app, db, User)

@app.route("/")
def home_page_view():
    return "Home Page, cool."

@app.route("/users/<username>")
@app.route("/users/<username>/")
def user_page_view(username):
    requested_user = User.query.filter(User.username == username).first()
    if requested_user == None:
        return "User not found."
    return requested_user.username + " has been a member since " + str(requested_user.email_confirmed_at) + "."

def make_initial_user(username, password, email):
    users = User.query.all()
    if len(users) != 0:
        return
    new_user = User()
    new_user.username = username
    new_user.password = user_manager.hash_password(password)
    new_user.email = email
    new_user.active = True
    db.session.add(new_user)
    db.session.commit()

def get_est_date():
    return datetime.datetime.now() - datetime.timedelta(hours = 4)

def check_if_valid_article_name(name):
    return len(name) <= 255 and re.search(r"^[a-zA-Z0-9-]+$", name)

def check_if_valid_tag_name(name):
    return len(name) <= 40 and re.search(r"^[a-z0-9-]+$", name)

def add_article_to_db(article_name, author):
    # adds article in file sys to db.
    if not check_if_valid_article_name(article_name):
        app.logger.error("Invalid article name.")
        return False
    if not os.path.isfile(config.paths.NEWS_ARTICLES_DIR + article_name + ".txt"):
        app.logger.error("File path does not exist.")
        return False
    new_article = NewsArticle()
    new_article.name = article_name
    new_article.created = datetime.datetime.now()   # stored in db as utc.
    new_article.author_id = author.id
    db.session.add(new_article)
    db.session.commit()
    return True

def add_news_tag_to_db(name, description, author):
    if not check_if_valid_tag_name(name):
        app.logger.error("Invalid tag name.")
        return False
    new_tag = NewsTag()
    new_tag.name = name
    new_tag.description = description
    new_tag.created = datetime.datetime.now()
    new_tag.author_id = author.id
    db.session.add(new_tag)
    db.session.commit()
    return True

@app.route("/assets/<path:file_path>")
def get_asset_file(file_path):
    path = config.paths.WORKING_DIR + "assets/"
    return send_from_directory(path, file_path, as_attachment = True)

def get_presentable_date(utc_date):
    est_date = utc_date - datetime.timedelta(hours = 4)
    return str(est_date.month) + "/" + str(est_date.day) + "/" + str(est_date.year)

@app.route("/news/articles/<requested>")
@app.route("/news/articles/<requested>/")
def news_article_handler(requested):
    article = NewsArticle.query.filter(NewsArticle.name == requested).first()
    if article == None:
        return "Article not found!"
    article_file_path = config.paths.NEWS_ARTICLES_DIR + article.name + ".txt"
    if not os.path.isfile(article_file_path):
        return "Error - Article in database but not in file system."
    author = article.author
    tags = article.tags
    with open(article_file_path) as article_file:
        lines = article_file.readlines()
    title = lines.pop(0)
    blank = lines.pop(0)
    paragraphs = lines
    date_made = get_presentable_date(article.created)
    return render_template("news/article.html", paragraphs = paragraphs, title = title, author = author, date_made = date_made, tags = tags)

@app.route("/news/tags/<requested>")
@app.route("/news/tags/<requested>/")
def news_tag_handler(requested):
    tag = NewsTag.query.filter(NewsTag.name == requested).first()
    if tag == None:
        return "Tag not found!"
    author = tag.author
    articles = tag.articles
    article_lists = []
    for article in articles:
        path = config.paths.NEWS_ARTICLES_DIR + article.name + ".txt"
        with open(path) as file:
            title = file.readline()
        article_lists.append([title, article.created, article.name])
    article_lists = sorted(article_lists, key = lambda x : x[1], reverse = True)
    return render_template("news/tag.html", article_lists = article_lists, tag = tag, author = author, est_date = get_presentable_date)




















