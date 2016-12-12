from flask import Blueprint

nikola = Blueprint('nikola', __name__,
                   static_folder='static',
                   url_prefix='/site')
nikola.config = {}
nikola.logger = None
