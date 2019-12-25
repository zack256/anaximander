import config.config2 as config2

def config_attribute(app, configs, attr):
    '''
    Configs the app with the more sensitive data found in config2.py.
    '''
    app.config[attr] = configs[attr]

def config_app(app):

    config2_configs = config2.app_configs
    attrs = ["SQLALCHEMY_DATABASE_URI", "SQLALCHEMY_POOL_RECYCLE", "SQLALCHEMY_TRACK_MODIFICATIONS", "MAIL_SERVER", "MAIL_USERNAME", "MAIL_PASSWORD", "MAIL_DEFAULT_SENDER", "MAIL_PORT", "MAIL_USE_SSL", "MAIL_USE_TLS", "SECRET_KEY"]
    for attr in attrs:
        config_attribute(app, config2_configs, attr)

    app.config['CSRF_ENABLED'] = True
    app.config['USER_ENABLE_EMAIL'] = True
    app.config['USER_APP_NAME'] = 'Anaximander'
    app.config['USER_ENABLE_INVITATION'] = True
    app.config['USER_REQUIRE_INVITATION'] = True
    app.config['USER_ENABLE_INVITE_USER'] = True

    app.config['USER_CHANGE_PASSWORD_URL'] = '/settings/change-password/'
    app.config['USER_ENABLE_CHANGE_USERNAME'] = True
    app.config['USER_CHANGE_USERNAME_URL'] = '/settings/change-username/'
    app.config['USER_CONFIRM_EMAIL_URL'] = '/auth/confirm-email/<token>/'
    app.config['USER_FORGOT_PASSWORD_URL'] = '/auth/forgot-password/'
    app.config['USER_LOGIN_URL'] = '/auth/login/'
    app.config['USER_LOGOUT_URL'] = '/auth/logout/'
    app.config['USER_REGISTER_URL'] = '/auth/register/'
    #app.config['USER_RESEND_CONFIRM_EMAIL_URL'] = '/auth/resend-confirmation-email/'
    app.config['USER_RESEND_EMAIL_CONFIRMATION_URL'] = '/auth/resend-confirmation-email/'
    app.config['USER_RESET_PASSWORD_URL'] = '/auth/reset-password/<token>/'
    app.config['USER_PROFILE_URL'] = '/error'   # tbd...
    app.config['USER_INVITE_USER_URL'] = '/invite'   # might change
    app.config['USER_INVITE_ENDPOINT'] = 'user.login'
    app.config['USER_PROFILE_TEMPLATE'] = 'error.html'  # tbd...