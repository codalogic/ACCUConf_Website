from flask import send_from_directory

from . import nikola

_nikola_static_path = None


@nikola.record
def init_blueprint(ctxt):
    app = ctxt.app
    nikola.config = app.config
    nikola.logger = app.logger
    global _nikola_static_path
    _nikola_static_path = nikola.config.get("NIKOLA_STATIC_PATH", None)
    if _nikola_static_path is None:
        message = 'NIKOLA_STATIC_PATH not set properly.'
        nikola.logger.info(message)
        raise ValueError(message)
    assert _nikola_static_path.is_dir(), "{} is not a directory".format(_nikola_static_path)


@nikola.route('/')
@nikola.route('/index.html')
def index():
    nikola.logger.info("Index accessed")
    return send_from_directory(_nikola_static_path.as_posix(), 'index.html')


@nikola.route('/rss.xml')
def rss():
    nikola.logger.info("RSS accessed")
    return send_from_directory(_nikola_static_path.as_posix(), 'rss.xml')


@nikola.route('/posts/<path:path>')
def posts(path):
    nikola.logger.info("posts accessed: {}".format(path))
    source_path = _nikola_static_path / 'posts'
    return send_from_directory(source_path.as_posix(), path)


@nikola.route('/stories/<path:path>')
def stories(path):
    nikola.logger.info("stories accessed: {}".format(path))
    source_path = _nikola_static_path / 'stories'
    return send_from_directory(source_path.as_posix(), path)


@nikola.route('/assets/<path:path>')
def assets(path):
    nikola.logger.info("assets accessed: {}".format(path))
    source_path = _nikola_static_path / 'assets'
    return send_from_directory(source_path.as_posix(), path)


@nikola.route('/images/<path:path>')
def images(path):
    nikola.logger.info("images accessed: {}".format(path))
    source_path = _nikola_static_path / 'images'
    return send_from_directory(source_path.as_posix(), path)
