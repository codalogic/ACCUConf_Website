from flask import Blueprint

proposals = Blueprint('proposals', __name__,
                      static_folder='../static',
                      template_folder='templates')
proposals.config = {}
proposals.logger = None
