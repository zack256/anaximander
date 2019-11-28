from flask import Flask, render_template, redirect, request
from flask_sqlalchemy import SQLAlchemy
from flask_user import current_user, login_required, UserManager, UserMixin, SQLAlchemyAdapter, roles_required
import config

app = Flask(__name__)

def config_attribute(attr):
    '''
    Configs the app with the more sensitive data found in config.py.
    '''
    app.config[attr] = config.app_configs[attr]

config_attribute("SQLALCHEMY_DATABASE_URI")
config_attribute("SQLALCHEMY_POOL_RECYCLE")
config_attribute("SQLALCHEMY_TRACK_MODIFICATIONS")
config_attribute("MAIL_SERVER")
config_attribute("MAIL_USERNAME")
config_attribute("MAIL_PASSWORD")
config_attribute("MAIL_DEFAULT_SENDER")
config_attribute("MAIL_PORT")
config_attribute("MAIL_USE_SSL")
config_attribute("MAIL_USE_TLS")
config_attribute("SECRET_KEY")

db = SQLAlchemy(app)

app.config['CSRF_ENABLED'] = True
app.config['USER_ENABLE_EMAIL'] = True
app.config['USER_APP_NAME'] = 'Anaximander'
app.config['USER_ENABLE_INVITATION'] = True
app.config['USER_REQUIRE_INVITATION'] = True

app.config['USER_CHANGE_PASSWORD_URL'] = '/settings/change-password/'
app.config['USER_ENABLE_CHANGE_USERNAME'] = True
app.config['USER_CHANGE_USERNAME_URL'] = '/settings/change-username/'
app.config['USER_CONFIRM_EMAIL_URL'] = '/auth/confirm-email/<token>/'
app.config['USER_FORGOT_PASSWORD_URL'] = '/auth/forgot-password/'
app.config['USER_LOGIN_URL'] = '/auth/login/'
app.config['USER_LOGOUT_URL'] = '/auth/logout/'
app.config['USER_REGISTER_URL'] = '/auth/register/'
app.config['USER_RESEND_CONFIRM_EMAIL_URL'] = '/auth/resend-confirmation-email/'
app.config['USER_RESET_PASSWORD_URL'] = '/auth/reset-password/<token>/'
app.config['USER_PROFILE_URL'] = '/error'   # tbd...
app.config['USER_INVITE_URL'] = '/invite'   # might change
app.config['USER_INVITE_ENDPOINT'] = 'user.login'
app.config['USER_PROFILE_TEMPLATE'] = 'error.html'  # tbd...
app.config['USER_UNAUTHENTICATED_ENDPOINT'] = "home_page"
app.config['USER_UNAUTHORIZED_ENDPOINT'] = "home_page"

class User(db.Model, UserMixin):
    __tablename__ = 'user'
    id = db.Column(db.Integer, primary_key = True)

    username = db.Column(db.String(50), nullable = True, unique = True)
    password = db.Column(db.String(255), nullable = False, server_default = '')
    active = db.Column(db.Boolean(), nullable = False, server_default = '0')
    email = db.Column(db.String(255), nullable = False, unique = True)
    confirmed_at = db.Column(db.DateTime())

    first_name = db.Column(db.String(100), nullable = False, server_default = '')
    last_name = db.Column(db.String(100), nullable = False, server_default = '')
    avatar = db.Column(db.String(50), nullable = False, server_default = '')

    seen = db.Column(db.DateTime())

    # Relationships
    roles = db.relationship('Role', secondary='user_roles', backref=db.backref('users', lazy='dynamic'))

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

user_manager = UserManager(app, db, User)

@app.route('/')
def home_page_view():
    return "Home Page, cool."

def make_initial_user(username, password, email):
    users = User.query.all()
    if len(users) != 0:
        return
    new_user = User()
    new_user.username = username
    new_user.password = user_manager.hash_password(password)
    new_user.email = email
    db.session.add(new_user)
    db.session.commit()





