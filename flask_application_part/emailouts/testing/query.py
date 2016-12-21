from accuconf.models import User


def query():
    return ((None, User.query.filter_by(email='russel@winder.org.uk').first()),)


def edit_template(text_file, proposal, user):
    with open(text_file) as tf:
        data = tf.read().strip()
        return data.format(user.first_name)
