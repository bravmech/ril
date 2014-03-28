# basically it's config
app.secret_key = 'omsVT1zPKmBhPMEVNlVQvgryp'
app.config.update(dict(
    SQLALCHEMY_DATABASE_URI=os.environ.get(
        'DATABASE_URL',
        'sqlite:////%s/ril.db' % app.root_path),
    DEBUG=True,
    SECRET_KEY='development key',
))
app.jinja_env.globals.update(isurl=isurl)
