import os
from ril import app

app.secret_key = 'omsVT1zPKmBhPMEVNlVQvgryp'
SQLALCHEMY_DATABASE_URI=os.environ.get(
    'DATABASE_URL',
    'sqlite:////' + os.path.join(app.root_path, 'ril.db'))
SECRET_KEY='development key'
