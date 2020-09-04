from flask import render_template, redirect, request, send_from_directory
from flask_user import current_user, login_required, UserManager, UserMixin, SQLAlchemyAdapter, roles_required
import config.paths
import os
import datetime
import restrict
import utils
import wikify
import work.diff, work.transform
import config.constants as cons
import string
import start_db
from sqlalchemy.sql.expression import func as sql_func

app, db = start_db.app, start_db.db

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

    registered = db.Column(db.DateTime(), default = db.func.now())
    seen = db.Column(db.DateTime())

    # Relationships
    roles = db.relationship('Role', secondary = 'user_roles', backref = db.backref('users', lazy='dynamic'))
    news = db.relationship("NewsArticle", backref = "author")
    news_tags = db.relationship("NewsTag", backref = "author")
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

user_manager = UserManager(app, db, User, UserInvitationClass = UserInvitation)

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
    protection = db.Column(db.Integer) # can be 0 (default) or 1, or 2 for public wikis. hafta elaborate on this.
    created = db.Column(db.DateTime())  # unnecessary, can look at first diff to see this.
    creator_id = db.Column(db.Integer(), db.ForeignKey('user.id', ondelete = 'CASCADE'))    # same as above.
    wiki_id = db.Column(db.Integer(), db.ForeignKey('wikis.id', ondelete = 'CASCADE'))
    diffs = db.relationship("Diff", backref = "article")

    def readable_name(self):
        n = ""
        for i in self.name:
            if i == "_":
                n += " "
            else:
                n += i
        return n

class Diff(db.Model):
    __tablename__ = "diffs"
    id = db.Column(db.Integer, primary_key = True)
    created = db.Column(db.DateTime())
    action = db.Column(db.Integer)  # Regular edit (0), Initial Diff (1), Minor Edit (2), Name Change (3), Protection Change (4), more to come?
    description = db.Column(db.String(256), server_default = "")
    editor_id = db.Column(db.Integer(), db.ForeignKey('user.id', ondelete = 'CASCADE'))
    article_id = db.Column(db.Integer(), db.ForeignKey('articles.id', ondelete = 'CASCADE'))
    sub_diffs = db.relationship("SubDiff", backref = "diff")

class SubDiff(db.Model):
    __tablename__ = "subdiffs"
    id = db.Column(db.Integer, primary_key = True)
    diff_id = db.Column(db.Integer(), db.ForeignKey('diffs.id', ondelete = 'CASCADE'))
    operation = db.Column(db.Boolean(), nullable = False)   # Subtraction (0) or Addition (1).
    index = db.Column(db.Integer())
    content = db.Column(db.String(4096))

@app.route("/")
def home_page_handler():
    #return "Home Page, cool."
    return render_template("index.html", wikis = Wiki.query.all())

@app.route("/users/<username>/")
def user_page_handler(username):
    requested_user = User.query.filter(User.username == username).first()
    if requested_user == None:
        return "User not found."
    return render_template("user.html", uu = requested_user)

@app.route("/users/<username>/contributions/")
def user_contributions_pg_handle(username):
    reqd = User.query.filter(User.username == username).first()
    if reqd == None:
        return "User not found."
    diffs = Diff.query.filter(Diff.editor_id == reqd.id).order_by(Diff.created.desc()).limit(50).all()
    article_id_set = set(); diff_dict = {}
    for dif in diffs:
        article_id_set.add(dif.article_id)
        diff_dict[dif.id] = [0, 0]
    articles = Article.query.filter(Article.id.in_(article_id_set)).all(); article_dict = {}; wiki_id_set = set()
    for art in articles:
        article_dict[art.id] = art
        wiki_id_set.add(art.wiki_id)
    wiki_dict = {wiki.id : wiki for wiki in Wiki.query.filter(Wiki.id.in_(wiki_id_set)).all()}
    subdiffs = SubDiff.query.filter(SubDiff.diff_id.in_(diff_dict)).all()
    for subdif in subdiffs:
        diff_dict[subdif.diff_id][subdif.operation] += len(subdif.content)
    return render_template("contributions.html", diffs = diffs, article_dict = article_dict, diff_dict = diff_dict, wiki_dict = wiki_dict, uu = reqd)

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

@app.route("/news/")
def news_page_handler():
    articles = NewsArticle.query.all()
    users = User.query.all()
    articles = sorted(articles, key = lambda x : x.created, reverse = True)
    articles = articles[:cons.NEWS_PAGE_HOME_MAX_ARTICLES_DISPLAYED]
    user_dict = get_user_dict(users)
    article_lists = get_article_list_for_display(articles, user_dict)
    is_editor = user_has_role(current_user, cons.NEWS_EDITOR_ROLE_NAME)
    return render_template("news/home.html", article_lists = article_lists, est_date = get_presentable_date, is_editor = is_editor)

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
    assc = Member(clearance = 4)    # 4 = creator of wiki (founder)
    assc.user = creator
    assc.wiki = new_wiki
    db.session.add(assc)
    db.session.commit()
    #os.mkdir(wiki_dir_path)
    make_wiki_dirs(wiki_dir_path)
    return True

@app.route("/wikis/<requested>/")
def wiki_home_page_handler(requested):
    wiki = Wiki.query.filter(Wiki.name == requested).first()
    if wiki == None:
        return "Wiki not found!"
    if not user_can_read_article(current_user, wiki):
        return "Insufficient roles to read this article."
    creator = User.query.join(Member).join(Wiki).filter((Member.wiki_id == wiki.id) & (Member.clearance == 4)).first()
    articles = sorted(wiki.articles, key = lambda x : x.name)
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

@app.route("/wikis/<requested>/new/article/", methods = ["GET", "POST"])
@login_required
def add_article_pg_handler(requested):
    wiki = Wiki.query.filter(Wiki.name == requested).first()
    if wiki == None:
        return "Wiki not found!"

    if request.method == "POST":
        body = request.form["article"]
        desc = request.form["desc"]
        article_name = request.form["name"]
        body = body.replace("\r", "")
        html = wikify.simple_wikify(body, wiki)
        return render_template("create_article.html", wiki = wiki, article_text = body, article_html = html, preview = True, desc = desc, article_name = article_name)

    return render_template("create_article.html", wiki = wiki)

def user_clearance_level(user, wiki):
    if not user.is_authenticated:
        return -1
    member = Member.query.filter((Member.wiki_id == wiki.id) & (Member.user_id == user.id)).first()
    return member.clearance if member else -1

def user_can_create_article(user, wiki):
    return user_can_edit_article(user, wiki)  # for now.

def user_can_edit_article(user, wiki):
    clearance = user_clearance_level(user, wiki)
    if wiki.privacy == 1:
        return clearance >= 2
    elif wiki.privacy == 2:
        return clearance >= 3
    return clearance != 0

def user_can_read_article(user, wiki):
    clearance = user_clearance_level(user, wiki)
    if wiki.privacy == 2:
        return clearance >= 1
    return True

def create_article(wiki, name, body, desc, creator):
    if not user_can_create_article(creator, wiki):
        return "Insufficient roles to create an article on this wiki."
    name = name.replace(" ", "_")
    if not restrict.check_if_valid_wiki_article_name(name):
        return "Invalid article name."
    already = Article.query.filter((Article.wiki_id == wiki.id) & (Article.name == name)).first()
    if already:
        return "Article already in database."
    article_path = get_article_path(wiki.name, name)
    if os.path.isfile(article_path):
        return "Article not in database, but cannot be added as a file with the same name exists."
    body = body.replace("\r", "")
    if len(body) == 0:
        return "Article body cannot be blank."
    with open(article_path, "w") as file:
        file.write(body)
    created = datetime.datetime.now()
    new_article = Article()
    new_article.name = name
    new_article.protection = 0
    new_article.created = created
    new_article.creator_id = creator.id
    new_article.wiki_id = wiki.id
    db.session.add(new_article)
    db.session.commit()
    initial_diff = Diff()
    initial_diff.action = 1
    initial_diff.description = desc
    initial_diff.created = created
    initial_diff.editor_id = creator.id
    initial_diff.article_id = new_article.id
    db.session.add(initial_diff)
    db.session.commit()
    initial_subdiff = SubDiff()
    initial_subdiff.diff_id = initial_diff.id
    initial_subdiff.operation = 1
    initial_subdiff.index = 0
    initial_subdiff.content = body
    db.session.add(initial_subdiff)
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
    desc = request.form["desc"]
    return create_article(wiki, name, body, desc, current_user)

@app.route("/wikis/<reqd_w>/articles/<reqd_a>/")
def article_page_handle(reqd_w, reqd_a):
    wiki = Wiki.query.filter(Wiki.name == reqd_w).first()
    if wiki == None:
        return "Wiki not found!"
    if not user_can_read_article(current_user, wiki):
        return "Insufficient roles to read this article."
    article = Article.query.filter((Article.wiki_id == wiki.id) & (Article.name == reqd_a)).first()
    if article == None:
        return "Article not found!"
    article_path = article_in_files(wiki.name, article.name)
    if not article_path:
        return "Article not found in file system!"
    with open(article_path) as fi:
        text = fi.read()
    #html = wikify.wikify(text, wiki)
    html = wikify.simple_wikify(text, wiki)
    return render_template("article.html", article = article, wiki = wiki, article_html = html)

@app.route("/wikis/<reqd_w>/articles/<reqd_a>/edit/", methods = ["GET", "POST"])
@login_required
def article_edit_page_handle(reqd_w, reqd_a):
    wiki = Wiki.query.filter(Wiki.name == reqd_w).first()
    if wiki == None:
        return "Wiki not found!"
    article = Article.query.filter((Article.wiki_id == wiki.id) & (Article.name == reqd_a)).first()
    if article == None:
        return "Article not found!"
    if not user_can_edit_article(current_user, wiki):
        return "Insufficient roles to edit this article."
    article_path = article_in_files(wiki.name, article.name)
    if not article_path:
        return "Article not found in file system!"

    if request.method == "POST":
        body = request.form["article"]
        desc = request.form["desc"]
        minor = request.form.get("minor")
        body = body.replace("\r", "")
        html = wikify.simple_wikify(body, wiki)
        return render_template("edit_article.html", article = article, wiki = wiki, article_text = body, article_html = html, preview = True, desc = desc, minor = minor)

    with open(article_path) as fi:
        text = fi.read()
    return render_template("edit_article.html", article = article, wiki = wiki, article_text = text)

def get_article_path(wiki_name, article_name):
    return config.paths.WIKIS_DIR + wiki_name + "/articles/" + article_name + ".txt"

def article_in_files(wiki_name, article_name):
    article_path = get_article_path(wiki_name, article_name)
    if os.path.isfile(article_path):
        return article_path
    return False

@app.route("/wikis/<reqd_w>/forms/edit-article/<reqd_a>/", methods = ["POST"])
@login_required
def edit_article_form_handler(reqd_w, reqd_a):
    wiki = Wiki.query.filter(Wiki.name == reqd_w).first()
    if wiki == None:
        return "Wiki not found!"
    article = Article.query.filter((Article.wiki_id == wiki.id) & (Article.name == reqd_a)).first()
    if article == None:
        return "Article not found!"
    if not article_in_files(wiki.name, article.name):
        return "Article not found in file system!"
    body = request.form["article"]
    desc = request.form["desc"]
    minor = request.form.get("minor")
    edit_article(wiki, article, body, desc, minor, current_user)
    return redirect("/wikis/{}/articles/{}/".format(wiki.name, article.name))

def add_sub_diff(o, i, c, d):
    sub_diff = SubDiff()
    sub_diff.operation = o
    sub_diff.index = i
    sub_diff.content = c
    sub_diff.diff_id = d.id
    db.session.add(sub_diff)

def edit_article(wiki, article, body, desc, minor, editor):
    if not user_can_edit_article(editor, wiki):
        return "Insufficient roles to edit this article."
    article_path = get_article_path(wiki.name, article.name)
    with open(article_path) as file:
        original = file.read()
    body = body.replace("\r", "")
    subtractions, additions = work.diff.get_diff(original, body)
    diff = Diff()
    diff.editor_id = editor.id
    diff.article_id = article.id
    if minor:
        diff.action = 2
    else:
        diff.action = 0
    diff.description = desc
    db.session.add(diff)
    db.session.commit() # needed for diff to have an id.
    for subtraction in subtractions:
        add_sub_diff(0, subtraction[0], subtraction[1], diff)
    for addition in additions:
        add_sub_diff(1, addition[0], addition[1], diff)
    diff.created = datetime.datetime.now()
    db.session.commit()
    with open(article_path, "w") as file2:
        file2.write(body)

def make_news_author_role():
    author_role = Role(name = cons.NEWS_EDITOR_ROLE_NAME)
    db.session.add(author_role)
    db.session.commit()

@app.route("/news/editor/")
@roles_required(cons.NEWS_EDITOR_ROLE_NAME)
def news_editor_pg_handle():
    return render_template("news/editor.html")

@app.route("/news/editor/create-article/")
@roles_required(cons.NEWS_EDITOR_ROLE_NAME)
def news_editor_new_article_pg_handle():
    return render_template("news/editor_new_article.html")

@app.route("/news/editor/tags/")
@roles_required(cons.NEWS_EDITOR_ROLE_NAME)
def news_editor_tags_pg_handle():
    tags = NewsTag.query.all()
    users_dict = {t.author_id : t.author for t in tags}
    return render_template("news/tag_editor.html", tags = tags, users_dict = users_dict)

@app.route("/unauthorized/")
def unauthorized_handle():
    return "You are unauthorized to view that page!"

def user_has_role(user, role):
    if not user.is_authenticated:
        return False
    return role in [i.name for i in user.roles]

def url_for_article_name(name):
    s = ""
    for i in name:
        if i == " ":
            s += "-"
        elif i in string.ascii_letters or i in string.digits:
            s += i.lower()
    return s

@app.route("/news/forms/create-article/", methods = ["POST"])
@roles_required(cons.NEWS_EDITOR_ROLE_NAME)
def create_news_article_handler():
    name = request.form["name"].strip()
    body = request.form["article"]
    url_name = url_for_article_name(name)
    if not restrict.check_if_valid_news_article_name(url_name):
        return "Article name failed validation tests!"
    if NewsArticle.query.filter(NewsArticle.name == url_name).first() != None:
        return "Article already exists in database!"
    path = config.paths.NEWS_ARTICLES_DIR + url_name + ".txt"
    if os.path.isfile(path):
        return "Article already exists in file system (but not database)!"
    with open(path, "w") as fi:
        fi.write(name + "\n\n")
        fi.write(body)
    new_article = NewsArticle()
    new_article.name = url_name
    new_article.created = datetime.datetime.now()
    new_article.author_id = current_user.id
    db.session.add(new_article)
    db.session.commit()
    return redirect("/news/articles/{}/".format(url_name))

@app.route("/news/forms/edit-tag/", methods = ["POST"])
@roles_required(cons.NEWS_EDITOR_ROLE_NAME)
def edit_news_tag_handle():
    t_id = int(request.form["t_id"])
    desc = request.form["desc"]
    news_tag = NewsTag.query.get(t_id)
    if news_tag == None:
        return "Invalid tag ID."
    news_tag.description = desc
    db.session.commit()
    return redirect("/news/editor/tags/")

@app.route("/wikis/<reqd_w>/articles/<reqd_a>/history/")
def article_history_page_handle(reqd_w, reqd_a):
    wiki = Wiki.query.filter(Wiki.name == reqd_w).first()
    if wiki == None:
        return "Wiki not found!"
    article = Article.query.filter((Article.wiki_id == wiki.id) & (Article.name == reqd_a)).first()
    if article == None:
        return "Article not found!"
    if not user_can_read_article(current_user, wiki):
        return "Insufficient roles to read this article."
    diffs = Diff.query.filter(Diff.article_id == article.id).order_by(Diff.created.desc()).limit(50).all()
    diff_dict = {}; editor_set = set()
    for dif in diffs:
        diff_dict[dif.id] = [0, 0]
        editor_set.add(dif.editor_id)
    subdiffs = SubDiff.query.filter(SubDiff.diff_id.in_(diff_dict)).all()
    editors = User.query.filter(User.id.in_(editor_set)).all()
    for subdiff in subdiffs:
        diff_dict[subdiff.diff_id][subdiff.operation] += len(subdiff.content)
    editor_dict = {ed.id : ed for ed in editors}
    return render_template("article_history.html", wiki = wiki, article = article, diffs = diffs, diff_dict = diff_dict, editor_dict = editor_dict)

@app.route("/wikis/<reqd_w>/meta/random/")
def random_article_in_wiki_page_handle(reqd_w):
    wiki = Wiki.query.filter(Wiki.name == reqd_w).first()
    if wiki == None:
        return "Wiki not found!"
    if not user_can_read_article(current_user, wiki):
        return "Insufficient roles to read this article."
    random_query = Article.query.filter(Article.wiki_id == wiki.id).order_by(sql_func.rand()).limit(1).all()
    if random_query:
        article = random_query[0]
    else:
        return "No articles in wiki!"
    return redirect("/wikis/{}/articles/{}/".format(wiki.name, article.name))

@app.route("/wikis/<reqd_w>/articles/<reqd_a>/revisions/<reqd_d>/")
def article_revision_page(reqd_w, reqd_a, reqd_d):
    wiki = Wiki.query.filter(Wiki.name == reqd_w).first()
    if wiki == None:
        return "Wiki not found!"
    if not user_can_read_article(current_user, wiki):
        return "Insufficient roles to read this article."
    diff = Diff.query.get(reqd_d)
    if not diff or diff.article.name != reqd_a:
        return "Diff and/or article bad!"
    article = diff.article
    #diff_list = Diff.query.filter((Diff.article_id == article.id) & (Diff.created > diff.created)).order_by(Diff.created.desc()).all()
    full_diff_list = Diff.query.filter(Diff.article_id == article.id).order_by(Diff.created.desc()).all()
    next_diff = prev_diff = None
    for c, el in enumerate(full_diff_list):
        if el.id == diff.id:
            break
    diff_list = full_diff_list[:c]
    if c != 0:
        next_diff = full_diff_list[c - 1]
    if c != len(full_diff_list) - 1:
        prev_diff = full_diff_list[c + 1]
    diff_dict = {dif.id : [[], []] for dif in diff_list}
    subdiffs = SubDiff.query.filter(SubDiff.diff_id.in_(diff_dict)).order_by(SubDiff.id).all()    # hrmm..ordering by id..
    for subdiff in subdiffs:
        diff_dict[subdiff.diff_id][subdiff.operation].append([subdiff.index, subdiff.content])
    article_path = get_article_path(wiki.name, article.name)
    with open(article_path) as file:
        body = file.read()
    for dif in diff_list:
        body = work.transform.backwards_transform(body, diff_dict[dif.id][0], diff_dict[dif.id][1])
    html = wikify.simple_wikify(body, wiki)
    return render_template("article_revision.html", article = article, wiki = wiki, article_html = html, revision = diff.id, next_diff = next_diff, prev_diff = prev_diff)

@app.route("/wikis/<requested>/meta/settings/")
def wiki_settings_page_handler(requested):
    wiki = Wiki.query.filter(Wiki.name == requested).first()
    if wiki == None:
        return "Wiki not found!"
    if not user_can_read_article(current_user, wiki):
        return "Insufficient roles to read this article."
    return render_template("wiki_settings.html", wiki = wiki)

@app.route("/wikis/<reqd_w>/forms/edit-wiki-settings/", methods = ["POST"])
@login_required
def edit_wiki_settings_form_handler(reqd_w):
    wiki = Wiki.query.filter(Wiki.name == reqd_w).first()
    if wiki == None:
        return "Wiki not found!"
    if user_clearance_level(current_user, wiki) < 3:
        return "Insufficient roles to edit wiki settings."
    privacy = request.form["wiki_privacy"]
    wiki.privacy = privacy
    db.session.commit()
    return redirect("/wikis/{}/meta/settings/".format(wiki.name))

@app.route("/wikis/<requested>/meta/members/")
def wiki_members_page_handler(requested):
    wiki = Wiki.query.filter(Wiki.name == requested).first()
    if wiki == None:
        return "Wiki not found!"
    if not user_can_read_article(current_user, wiki):
        return "Insufficient roles to read this article."
    members = wiki.users
    users_dict = { member.user_id : None for member in members }
    users = User.query.filter(User.id.in_(users_dict)).all()
    for user in users:
        users_dict[user.id] = user
    members.sort(key = lambda x : [-x.clearance, users_dict[x.user_id].username])
    user_can_edit_clearances = user_clearance_level(current_user, wiki) >= 3
    return render_template("wiki_members.html", wiki = wiki, members = members, users_dict = users_dict, user_can_edit_clearances = user_can_edit_clearances)

@app.route("/wikis/<reqd_w>/forms/invite-member/", methods = ["POST"])
@login_required
def invite_member_to_wiki(reqd_w):
    wiki = Wiki.query.filter(Wiki.name == reqd_w).first()
    if wiki == None:
        return "Wiki not found!"
    if user_clearance_level(current_user, wiki) < 3:
        return "Insufficient roles to invite member."
    reqd_username = request.form["username"]
    user = User.query.filter(User.username == reqd_username).first()
    if not user:
        return "No user found with that name."
    clearance_level = user_clearance_level(user, wiki)
    if clearance_level != -1:
        return "User already has a clearance level for the wiki."
    member = Member(clearance = 1)
    member.user = user
    member.wiki = wiki
    db.session.add(member)
    db.session.commit()
    return redirect("/wikis/{}/meta/members/".format(wiki.name))

@app.route("/wikis/<reqd_w>/forms/edit-member-clearance/", methods = ["POST"])
@login_required
def edit_member_clearance_form(reqd_w):
    wiki = Wiki.query.filter(Wiki.name == reqd_w).first()
    if wiki == None:
        return "Wiki not found!"
    if user_clearance_level(current_user, wiki) < 3:
        return "Insufficient roles to edit member clearance."
    app.logger.error(request.form)
    reqd_username = request.form["username"]
    user = User.query.filter(User.username == reqd_username).first()
    if not user:
        return "No user found with that name."
    member = Member.query.filter((Member.user_id == user.id) & (Member.wiki_id == wiki.id)).first()
    if not member:
        member = Member(user_id = user.id, wiki_id = wiki.id)
        db.session.add(member)
        db.session.commit()
    elif member.clearance >= 3:
        return "Cannot demote that much yet."
    level = min(2, int(request.form["level"]))
    if level == -1 and member:
        db.session.delete(member)
    else:
        member.clearance = level
    db.session.commit()
    return redirect("/wikis/{}/meta/members/".format(wiki.name))

