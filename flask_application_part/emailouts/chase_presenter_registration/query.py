from accuconf.models import User


def query():
    users = User.query.all()
    names = (
        ('Alfred', 'Bratterud'),
        ('James', 'Turner'),
        ('Sergey', 'Ignatchenko'),
        ('Peter', 'Hilton'),
        ('Mathias', 'Gaunard'),
    )

    def is_a_name(u):
        for n in names:
            if u.first_name == n[0] and u.last_name == n[1]:
                return True
        return False

    selected = tuple(u for u in users if is_a_name(u))
    return ((None, u) for u in selected)


def edit_template(text_file, proposal, user):
    with open(text_file) as tf:
        data = tf.read().strip()
        return data.format(user.first_name)
