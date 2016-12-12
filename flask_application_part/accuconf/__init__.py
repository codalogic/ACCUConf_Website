from flask import Flask, redirect, url_for
from flask_bootstrap import Bootstrap
from flask_sqlalchemy import SQLAlchemy

try:
    from accuconf_config import Config
except ImportError:
    from .configuration import Config

app = Flask(__name__)
Bootstrap(app)
db = SQLAlchemy(app)

# NB Must have the db attribute in this package prior to importing the following.

from .nikola import nikola, views
from .proposals import proposals, views

app.config.from_object(Config)
app.secret_key = app.config['SECRET_KEY']
app.register_blueprint(nikola, url_prefix='/site')
app.register_blueprint(proposals, url_prefix='/proposals')
app.logger.info(app.url_map)


@app.route('/')
def index():
    return redirect(url_for('nikola.index'))
