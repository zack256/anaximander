from flask import Flask, render_template, redirect, request, send_from_directory
from flask_sqlalchemy import SQLAlchemy
from flask_user import current_user, login_required, UserManager, UserMixin, SQLAlchemyAdapter, roles_required
import config.config as config_app
import config.paths
import os
import datetime
import constants
import restrict

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
    #wikis = db.relationship("Wiki", backref = "creator")
    wikis = db.relationship("Member", backref = "user_m")
    articles = db.relationship("Article", backref = "creator")
    diffs = db.relationship("Diff", backref = "editor")

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

class Wiki(db.Model):
    __tablename__ = "wikis"
    id = db.Column(db.Integer, primary_key = True)
    name = db.Column(db.String(80), nullable = False, unique = True)    # short name.
    full = db.Column(db.String(80), nullable = False, unique = True)    # long name.
    description = db.Column(db.String(200))
    privacy = db.Column(db.Integer) # can be 0 (public), 1 (semi-public), or 2 (private).
    created = db.Column(db.DateTime())
    #creator_id = db.Column(db.Integer(), db.ForeignKey('user.id', ondelete = 'CASCADE'))
    users = db.relationship("Member", backref = "wiki_m")
    articles = db.relationship("Article", backref = "wiki")

class Member(db.Model):
    __tablename__ = "members"
    id = db.Column(db.Integer, primary_key = True, autoincrement = True)
    user_id = db.Column(db.Integer(), db.ForeignKey('user.id'), primary_key = True, autoincrement = False)  # autoincrement is needed.
    wiki_id = db.Column(db.Integer(), db.ForeignKey('wikis.id'), primary_key = True, autoincrement = False) # " " "
    clearance = db.Column(db.Integer()) # 0-4. more on that later.
    user = db.relationship(User, backref = "wikis_m")
    wiki = db.relationship(Wiki, backref = "users_m")

class Article(db.Model):
    __tablename__ = "articles"
    id = db.Column(db.Integer, primary_key = True)
    name = db.Column(db.String(80), nullable = False)
    created = db.Column(db.DateTime())
    creator_id = db.Column(db.Integer(), db.ForeignKey('user.id', ondelete = 'CASCADE'))
    wiki_id = db.Column(db.Integer(), db.ForeignKey('wikis.id', ondelete = 'CASCADE'))
    diffs = db.relationship("Diff", backref = "article")

class Diff(db.Model):
    __tablename__ = "diffs"
    id = db.Column(db.Integer, primary_key = True)
    created = db.Column(db.DateTime())
    editor_id = db.Column(db.Integer(), db.ForeignKey('user.id', ondelete = 'CASCADE'))
    article_id = db.Column(db.Integer(), db.ForeignKey('articles.id', ondelete = 'CASCADE'))
    convert_version_id = db.Column(db.Integer(), db.ForeignKey('wiki_convert_versions.id', ondelete = 'CASCADE'))
    sub_diffs = db.relationship("SubDiff", backref = "diff")

class SubDiff(db.Model):
    __tablename__ = "subdiffs"
    id = db.Column(db.Integer, primary_key = True)
    diff_id = db.Column(db.Integer(), db.ForeignKey('diffs.id', ondelete = 'CASCADE'))
    operation = db.Column(db.Boolean(), nullable = False)   # Subtraction (0) or Addition (1).
    index = db.Column(db.Integer())
    content = db.Column(db.String(4096))

class WikiConvertVersion(db.Model):
    __tablename__ = "wiki_convert_versions"
    id = db.Column(db.Integer, primary_key = True)
    released = db.Column(db.DateTime)
    version = db.Column(db.Float)
    diffs = db.relationship("Diff", backref = "convert_version")

user_manager = UserManager(app, db, User, UserInvitationClass = UserInvitation)

@app.route("/")
def home_page_handler():
    #return "Home Page, cool."
    return render_template("index.html", wikis = Wiki.query.all())

@app.route("/users/<username>")
@app.route("/users/<username>/")
def user_page_handler(username):
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

def add_article_to_db(article_name, author):
    # adds article in file sys to db.
    if not restrict.check_if_valid_news_article_name(article_name):
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
    if not restrict.check_if_valid_news_tag_name(name):
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

def get_article_list_for_display(articles, user_dict = None):
    article_lists = []
    for article in articles:
        path = config.paths.NEWS_ARTICLES_DIR + article.name + ".txt"
        with open(path) as file:
            title = file.readline()
        article_list = [title, article.created, article.name]
        if user_dict:
            author = user_dict[article.author_id]
            article_list.append(author)
        article_lists.append(article_list)
    return article_lists

def get_user_dict(users):
    d = {}
    for user in users:
        d[user.id] = user
    return d

@app.route("/news/tags/<requested>")
@app.route("/news/tags/<requested>/")
def news_tag_handler(requested):
    tag = NewsTag.query.filter(NewsTag.name == requested).first()
    if tag == None:
        return "Tag not found!"
    users = User.query.all()
    articles = tag.articles
    user_dict = get_user_dict(users)
    author = user_dict[tag.author_id]
    article_lists = get_article_list_for_display(articles, user_dict)
    article_lists = sorted(article_lists, key = lambda x : x[1], reverse = True)
    return render_template("news/tag.html", article_lists = article_lists, tag = tag, author = author, est_date = get_presentable_date)

@app.route("/news")
@app.route("/news/")
def news_page_handler():
    articles = NewsArticle.query.all()
    users = User.query.all()
    articles = sorted(articles, key = lambda x : x.created, reverse = True)
    articles = articles[:constants.NEWS_PAGE_HOME_MAX_ARTICLES_DISPLAYED]
    user_dict = get_user_dict(users)
    article_lists = get_article_list_for_display(articles, user_dict)
    return render_template("news/home.html", article_lists = article_lists, est_date = get_presentable_date)

@app.route("/news/authors/<requested>")
@app.route("/news/authors/<requested>/")
def news_author_handler(requested):
    user = User.query.filter(User.username == requested).first()
    articles = user.news
    articles = sorted(articles, key = lambda x : x.created, reverse = True)
    article_lists = get_article_list_for_display(articles)
    return render_template("news/author.html", article_lists = article_lists, est_date = get_presentable_date, author = user)

def make_wiki_dirs(wiki_path):
    os.mkdir(wiki_path)
    os.mkdir(wiki_path + "/articles")

def add_wiki(name, full, description, creator):
    if not restrict.check_if_valid_wiki_name(name):
        app.logger.error("Invalid wiki name.")
        return False
    if Wiki.query.filter(Wiki.name == name).first():
        app.logger.error("Wiki already exists!")
        return False
    wiki_dir_path = config.paths.WIKIS_DIR + name
    if os.path.isdir(wiki_dir_path):
        app.logger.error("Wiki already has a directory that possibly contains files.")
        return False
    created = datetime.datetime.now()
    new_wiki = Wiki()
    new_wiki.name = name
    new_wiki.full = full
    new_wiki.description = description
    new_wiki.privacy = 0    # initially public.
    new_wiki.created = created
    db.session.add(new_wiki)
    assc = Member(clearance = 4)
    assc.user = creator
    assc.wiki = new_wiki
    db.session.add(assc)
    db.session.commit()
    #os.mkdir(wiki_dir_path)
    make_wiki_dirs(wiki_dir_path)
    return True

@app.route("/wikis/<requested>")
@app.route("/wikis/<requested>/")
def wiki_home_page_handler(requested):
    wiki = Wiki.query.filter(Wiki.name == requested).first()
    if wiki == None:
        return "Wiki not found!"
    creator = User.query.join(Member).join(Wiki).filter((Member.wiki_id == wiki.id) & (Member.clearance == 4)).first()
    articles = wiki.articles
    return render_template("wiki.html", wiki = wiki, creator = creator, articles = articles)

@app.route("/forms/add-wiki/", methods = ["POST"])
@login_required
def add_wiki_handler():
    name = request.form["name"]
    full = request.form["full"]
    desc = request.form["desc"]
    if not add_wiki(name, full, desc, current_user):
        return "Something went wrong!"
    return redirect("/wikis/{}/".format(name))

@app.route("/wikis/<requested>/new/article")
@app.route("/wikis/<requested>/new/article/")
@login_required
def add_article_pg_handler(requested):
    wiki = Wiki.query.filter(Wiki.name == requested).first()
    if wiki == None:
        return "Wiki not found!"
    return render_template("create_article.html", wiki = wiki)

def user_clearance_level(user, wiki):
    member = Member.query.filter((Member.wiki_id == wiki.id) & (Member.user_id == user.id)).first()
    return member.clearance if member else -1

def user_can_create_article(user, wiki):
    clearance = user_clearance_level(user, wiki)
    if wiki.privacy >= 1:
        return clearance >= 2
    return clearance != 0

def create_article(wiki, name, body, creator):
    if not user_can_create_article(creator, wiki):
        return "Insufficient roles to create an article on this wiki."
    if not restrict.check_if_valid_wiki_article_name(name):
        return "Invalid article name."
    already = Article.query.filter((Article.wiki_id == wiki.id) & (Article.name == name)).first()
    if already:
        return "Article already in database."
    article_path = config.paths.WIKIS_DIR + wiki.name + "/articles/" + name + ".txt"
    if os.path.isdir(article_path):
        return "Article not in database, but cannot be added as a file with the same name exists."
    with open(article_path, "w") as file:
        file.write(body)
    created = datetime.datetime.now()
    new_article = Article()
    new_article.name = name
    new_article.created = created
    new_article.user_id = creator.id
    new_article.wiki_id = wiki.id
    db.session.add(new_article)
    db.session.commit()
    return redirect("/wikis/{}/articles/{}/".format(wiki.name, name))

@app.route("/wikis/<requested>/forms/create-article/", methods = ["POST"])
@login_required
def create_article_handler(requested):
    wiki = Wiki.query.filter(Wiki.name == requested).first()
    if wiki == None:
        return "Wiki not found!"
    name = request.form["name"]
    body = request.form["article"]
    return create_article(wiki, name, body, current_user)










