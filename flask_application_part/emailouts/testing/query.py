from accuconf.models import User


def query():
    test_user = User('russel@itzinteractive.com', '', 'Russel', 'Winder', '', '', '', '', '', '')
    return (
        (None, User.query.filter_by(email='russel@winder.org.uk').first()),
        (None, test_user),
    )


def edit_template(text_file, proposal, user):
    with open(text_file) as tf:
        data = tf.read().strip()
        return data.format(user.first_name)
