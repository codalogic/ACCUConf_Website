import hashlib
from random import randint

from flask import render_template, jsonify, redirect, url_for, session, request
from flask import send_from_directory, g

from accuconf import db
from accuconf.models import MathPuzzle, User, ProposalPresenter, Proposal, Presenter, Score, Comment
from accuconf.proposals.utils.proposals import SessionType
from accuconf.proposals.utils.roles import Role
from accuconf.proposals.utils.validator import validate_email, validate_password, validate_proposal_data

from . import proposals

_proposal_static_path = None


@proposals.record
def init_blueprint(context):
    app = context.app
    proposals.config = app.config
    proposals.logger = app.logger
    global _proposal_static_path
    _proposal_static_path = proposals.config.get("NIKOLA_STATIC_PATH", None)
    if _proposal_static_path is None:
        message = 'NIKOLA_STATIC_PATH not set properly.'
        proposals.logger.info(message)
        raise ValueError(message)
    assert _proposal_static_path.is_dir()
    if proposals.config.get('ADMINISTERING'):
        import flask_admin
        from accuconf.models.admin import UserAdmin, ProposalsAdmin, PresentersAdmin
        proposals.admin = flask_admin.Admin(app, name='ACCUConf Admin', template_mode='bootstrap3')
        proposals.admin.add_view(UserAdmin(User, db.session))
        proposals.admin.add_view(ProposalsAdmin(Proposal, db.session))
        proposals.admin.add_view(PresentersAdmin(Presenter, db.session))


@proposals.route("/")
def index():
    if proposals.config.get("MAINTENANCE"):
        return redirect(url_for("proposals.maintenance"))
    return redirect(url_for('nikola.index'))


@proposals.route("/maintenance")
def maintenance():
    return render_template("maintenance.html", page={})


@proposals.route("/login", methods=['GET', 'POST'])
def login():
    if proposals.config.get("MAINTENANCE"):
        return redirect(url_for("proposals.maintenance"))
    if request.method == "POST":
        email = request.form['usermail']
        password = request.form['password']
        user = User.query.filter_by(email=email).first()
        if not user:
            return redirect(url_for('index'))
        password_hash = hashlib.sha256(password.encode("utf-8")).hexdigest()
        if user.password == password_hash:
            session['id'] = user.email
            proposals.logger.info("Auth successful")
            g.user = email
            return redirect(url_for("nikola.index"))
        else:
            proposals.logger.info("Auth failed")
            return redirect(url_for("proposals.login"))
    elif request.method == "GET":
        return render_template("login.html", page={"title": "Login Page"})


@proposals.route("/logout")
def logout():
    session.pop('id', None)
    return redirect(url_for('index'))


@proposals.route("/register", methods=["GET", "POST"])
def register():
    if proposals.config.get("MAINTENANCE"):
        return redirect(url_for("proposals.maintenance"))
    edit_mode = False
    user = None
    if session.get("id", False):
        user = User.query.filter_by(email=session["id"]).first()
        if user is not None:
            edit_mode = True
    if request.method == "POST":
        email = request.form["usermail"]
        # In case that no user pass was provided, we don't update the field
        password = None
        if len(request.form["password"].strip()) > 0:
            password = request.form["password"]
        # TODO Should cpassword be handled like password and failure happen if they are not the same?
        cpassword = request.form["cpassword"]
        first_name = request.form["firstname"]
        last_name = request.form["lastname"]
        town_and_city = request.form["towncity"]
        country = request.form["country"]
        state = request.form["state"]
        phone = request.form["phone"]
        postal_code = request.form["pincode"]
        town_city = request.form['towncity']
        street_address = request.form['streetaddress']
        encoded_pass = None
        if type(password) == str and len(password):
            encoded_pass = hashlib.sha256(password.encode('utf-8')).hexdigest()
        page = {}
        if edit_mode:
            user.email = email
            user.first_name = first_name
            user.last_name = last_name
            if encoded_pass:
                user.password = encoded_pass
            user.phone = phone
            user.country = country
            user.state = state
            user.postal_code = postal_code
            user.town_city = town_city
            user.street_address = street_address
            if encoded_pass:
                User.query.filter_by(email=user.email).update({'password': encoded_pass })
            User.query.filter_by(email=user.email).update({
                'email': email,
                'first_name': first_name,
                'last_name': last_name,
                'phone': phone,
                'country': country,
                'state': state,
                'postal_code': postal_code,
                'town_city': town_city,
                'street_address': street_address
            })
            page["title"] = "Account update successful"
            page["data"] = "Your account details were successful updated."
        else:
            if not validate_email(email):
                page["title"] = "Registration failed"
                page["data"] = "Registration failed: Invalid/Duplicate user email."
                page["data"] += "Please register again"
                return render_template("registration_failure.html", page=page)
            elif not validate_password(password):
                page["title"] = "Registration failed"
                page["data"] = "Registration failed: Password did not meet checks."
                page["data"] += "Please register again"
                return render_template("registration_failure.html", page=page)
            if not validate_email(email):
                page["title"] = "Registration failed"
                page["data"] = "Registration failed: Invalid/Duplicate user email."
                page["data"] += "Please register again"
                return render_template("registration_failure.html", page=page)
            elif not validate_password(password):
                page["title"] = "Registration failed"
                page["data"] = "Registration failed: Password did not meet checks."
                page["data"] += "Please register again"
                return render_template("registration_failure.html", page=page)
            errors = []
            for field, field_name in (
                    (email, 'email'),
                    (password, 'password'),
                    (cpassword, 'password confirmation'),
                    (first_name, 'first name'),
                    (last_name, 'last name'),
                    (town_and_city, 'town and city'),
                    (phone, 'phone number'),
                    (postal_code, 'pin code'),
                    (street_address, 'street address'),):
                if not field.strip():
                    errors.append("The {} field was not filled in.".format(field_name))
            if errors:
                errors.append('')
                errors.append("Please register again")
                page = {
                    "title": "Registration failed",
                    "data": ' '.join(errors),
                }
                return render_template("registration_failure.html", page=page)
            else:
                new_user = User(
                    email,
                    encoded_pass,
                    first_name,
                    last_name,
                    phone,
                    country,
                    state,
                    postal_code,
                    town_city,
                    street_address,
                )
                db.session.add(new_user)
            page["title"] = "Registration successful"
            page["data"] = "You have successfully registered for submitting "
            page["data"] += "proposals for the ACCU Conf. Please login and "
            page["data"] += "start preparing your proposal for the conference."
        db.session.commit()
        return render_template("registration_success.html", page=page)
    elif request.method == "GET":
        num_a = randint(10, 99)
        num_b = randint(10, 99)
        question = MathPuzzle(num_a + num_b)
        db.session.add(question)
        db.session.commit()
        page = {
            'mode': 'edit_mode' if edit_mode else 'register',
            'email': user.email if edit_mode else '',
            'first_name': user.first_name if edit_mode else '',
            'last_name': user.last_name if edit_mode else '',
            'phone': user.phone if edit_mode else '',
            'country': user.country if edit_mode else 'GBR', # UK shall be the default
            'state': user.state if edit_mode else 'GB-ENG',
            'postal_code': user.postal_code if edit_mode else '',
            'town_city': user.town_city if edit_mode else '',
            'street_address': user.street_address if edit_mode else '',
            'title': 'Account Information' if edit_mode else 'Register',
            'data': 'Here you can edit your account information' if edit_mode else 'Register here for submitting proposals to ACCU Conference',
            'question': question.id,
            'puzzle': '{} + {}'.format(num_a, num_b),
            'submit_button': 'Save' if edit_mode else 'Register',
        }
        return render_template("register.html", page=page)


@proposals.route("/show_proposals", methods=["GET"])
def show_proposals():
    if proposals.config.get("MAINTENANCE"):
        return redirect(url_for("proposals.maintenance"))
    if session.get("id", False):
        user = User.query.filter_by(email=session["id"]).first()
        if not user:
            return render_template("not_logged_in.html", page={"name": "Submit proposal"})
        page = {"subpages": []}
        for proposal in user.proposals:
            subpage = {
                "proposal": {
                    "title": proposal.title,
                    "abstract": proposal.text,
                    "session_type": proposal.session_type,
                    "presenters": proposal.presenters,
                }
            }
            page["subpages"].append(subpage)
        return render_template("view_proposal.html", page=page)
    else:
        return render_template("not_logged_in.html", page={"name": "Submit proposal"})


@proposals.route("/submit_proposal", methods=["GET"])
def submit_proposal():
    if proposals.config.get("MAINTENANCE"):
        return redirect(url_for("proposals.maintenance"))
    if session.get("id", False):
        user = User.query.filter_by(email=session["id"]).first()
        if not user:
            return render_template("not_logged_in.html", page={"name": "Submit proposal"})
        return render_template("submit_proposal.html", page={
            "title": "Submit a proposal for ACCU Conference",
            "user_name": "{} {}".format(user.first_name, user.last_name),
            "proposer": {
                "email": user.email,
                "first_name": user.first_name,
                "last_name": user.last_name,
                'bio': 'A human being.',
                "country": user.country,
                "state": user.state
            }
        })
    else:
        return render_template("not_logged_in.html", page={"name": "Submit proposal"})


@proposals.route("/upload_proposal", methods=["POST"])
def upload_proposal():
    if proposals.config.get("MAINTENANCE"):
        return redirect(url_for("proposals.maintenance"))
    if session.get("id", False):
        user = User.query.filter_by(email=session["id"]).first()
        if not user:
            return render_template("not_logged.html", page={"name": "Proposal Submission"})
        else:
            proposal_data = request.json
            proposals.logger.info(proposal_data)
            status, message = validate_proposal_data(proposal_data)
            response = {}
            if status:
                proposal = Proposal(user,
                                    proposal_data.get("title").strip(),
                                    SessionType(proposal_data.get('session_type')),
                                    proposal_data.get("abstract").strip())
                db.session.add(proposal)
                db.session.commit()
                presenters_data = proposal_data.get("presenters")
                for presenter_data in presenters_data:
                    presenter = Presenter(
                            presenter_data["email"],
                            presenter_data["fname"],
                            presenter_data["lname"],
                            'A human being.',
                            presenter_data["country"],
                            presenter_data["state"],
                        )
                    db.session.add(presenter)
                    db.session.commit()
                    proposal_presenter = ProposalPresenter(
                        proposal.id, presenter.id,
                        proposal, presenter,
                        presenter_data["lead"],
                    )
                    proposal.presenters.append(proposal_presenter)
                    presenter.proposals.append(proposal_presenter)
                    db.session.add(proposal_presenter)
                    db.session.commit()
                db.session.commit()
                response["success"] = True
                response["message"] = "Thank you very much!\nYou have successfully submitted a proposal for the next ACCU conference!\nYou can see it now under \"My Proposal\"."
                response["redirect"] = url_for('proposals.index')
            else:
                response["success"] = False
                response["message"] = message
            return jsonify(**response)
    else:
        return render_template("not_logged_in.html", page={"name": "Submit proposal"})


@proposals.route("/review_proposal", methods=["GET"])
def review_proposal():
    if proposals.config.get("MAINTENANCE"):
        return redirect(url_for("proposals.maintenance"))
    if session.get("id", False):
        user = User.query.filter_by(email=session["id"]).first()
        if not user:
            return render_template("not_logged_in.html", page={"name": "Submit proposal"})
        page = {"Title": "Review Proposal"}
        proposal_to_show_next = None
        all_proposals = Proposal.query.filter(Proposal.proposer != session["id"]).order_by(Proposal.id)
        all_proposals_reverse = Proposal.query.filter(Proposal.proposer != session["id"]).order_by(Proposal.id.desc())
        if session.get("review_button_pressed", False):
            if session["review_button_pressed"] == "next_proposal":
                proposal_to_show_next = find_next_element(all_proposals, session["review_id"])
            elif session["review_button_pressed"] == "previous_proposal":
                proposal_to_show_next = find_next_element(all_proposals_reverse, session["review_id"])
            elif session["review_button_pressed"] == "next_nr_proposal":
                proposal_to_show_next = find_next_not_reviewed_element(all_proposals, session["review_id"], user.email)
            elif session["review_button_pressed"] == "previous_nr_proposal":
                proposal_to_show_next = find_next_not_reviewed_element(all_proposals_reverse, session["review_id"], user.email)
            elif session["review_button_pressed"] == "save":
                proposal_to_show_next = find_element(all_proposals, session["review_id"])
        else:
            proposal_to_show_next = all_proposals.first()
        session["review_button_pressed"] = ""
        if not proposal_to_show_next:
            return render_template("review_success.html", page={
                "title": "All scores done",
                "data": "You have finished reviewing all proposals!",
            })
        next_available = False
        previous_available = False
        next_not_read_available = False
        previous_not_read_available = False
        if all_proposals.first().id != proposal_to_show_next.id:
            previous_available = True
        if all_proposals_reverse.first().id != proposal_to_show_next.id:
            next_available = True
        next_potential_not_read = find_next_not_reviewed_element(all_proposals, proposal_to_show_next.id, user.email)
        if next_potential_not_read is not None:
            next_not_read_available = True
        previous_potential_not_read = find_next_not_reviewed_element(all_proposals_reverse, proposal_to_show_next.id, user.email)
        if previous_potential_not_read is not None:
            previous_not_read_available = True
        proposal_review = Score.query.filter_by(proposal_id=proposal_to_show_next.id, reviewer=user.email).first()
        proposal_comment = Comment.query.filter_by(proposal_id=proposal_to_show_next.id, commenter=user.email).first()

        speakers_info = User.query.filter_by(email=proposal_to_show_next.proposer).first()
        speakers_bio = speakers_info.bio if speakers_info is not None else ""

        page["proposal"] = {
            "title": proposal_to_show_next.title,
            "abstract": proposal_to_show_next.text,
            "bio": speakers_bio,
            "session_type": proposal_to_show_next.session_type,
            "presenters": proposal_to_show_next.presenters,
            "score": 0,
            "comment": "",
            "next_enabled": next_available,
            "previous_enabled": previous_available,
            "next_nr_enabled": next_not_read_available,
            "previous_nr_enabled": previous_not_read_available,
        }
        if proposal_review:
            page["proposal"]["score"] = proposal_review.score
        if proposal_comment:
            page["proposal"]["comment"] = proposal_comment.comment
        session['review_id'] = proposal_to_show_next.id
        return render_template("review_proposal.html", page=page)
    else:
        return render_template("not_logged_in.html", page={"name": "Submit proposal"})


@proposals.route("/upload_review", methods=["POST"])
def upload_review():
    if proposals.config.get("MAINTENANCE"):
        return redirect(url_for("proposals.maintenance"))
    if session.get("id", False):
        user = User.query.filter_by(email=session["id"]).first()
        if not user:
            return render_template("not_logged_in.html", page={"name": "Submit proposal"})
        if session.get("review_id", False):
            proposal = Proposal.query.filter_by(id=session["review_id"]).first()
            if proposal is not None:
                review_data = request.json
                proposals.logger.info(review_data)
                proposal_review = Score.query.filter_by(proposal_id=proposal.id, reviewer=user.id).first()
                if proposal_review:
                    proposal_review.score = review_data["score"]
                    Score.query.filter_by(proposal_id=proposal.id, reviewer=user.id).update({'score': proposal_review.score})
                else:
                    proposal_review = Score(proposal.id, user.id, review_data["score"])
                    proposal.reviews.append(proposal_review)
                    db.session.add(proposal_review)
                proposal_comment = Comment.query.filter_by(proposal_id=proposal.id, commenter=user.id).first()
                if proposal_comment:
                    proposal_comment.comment = review_data["comment"].rstrip()
                    Comment.query.filter_by(
                        proposal_id=proposal.id,
                        commenter=user.id).update({'comment': proposal_comment.comment})
                else:
                    proposal_comment = Comment(proposal.id, user.id, review_data["comment"])
                    proposal.comments.append(proposal_comment)
                    db.session.add(proposal_comment)
                db.session.commit()
                session['review_button_pressed'] = review_data["button"]
                return jsonify(success=True, redirect=url_for('proposals.review_proposal'))
    else:
        return render_template("not_logged_in.html", page={"name": "Submit proposal"})


@proposals.route("/check/<user>", methods=["GET"])
def check_duplicate(user):
    if proposals.config.get("MAINTENANCE"):
        return redirect(url_for("proposals.maintenance"))
    u = User.query.filter_by(email=user).first()
    result = {}
    if u:
        result["duplicate"] = True
    else:
        result["duplicate"] = False
    return jsonify(**result)


@proposals.route("/captcha/validate", methods=["POST"])
def validate_captcha():
    captcha_info = request.json
    qid = captcha_info.get("question_id")
    ans = captcha_info.get("answer")
    q = MathPuzzle.query.filter_by(id=qid).first()
    result = {"valid": False}
    if q:
        if q.answer == ans:
            result["valid"] = True
    return jsonify(**result)


@proposals.route("/captcha/new", methods=["POST"])
def generate_captcha():
    captcha_info = request.json
    result = {"valid": True}
    qid = captcha_info.get("question_id")
    if not qid:
        result["valid"] = False
    else:
        question = MathPuzzle.query.filter_by(id=qid).first()
        if question:
            num_a = randint(10, 99)
            num_b = randint(10, 99)
            question.answer = num_a + num_b
            db.session.commit()
            result["valid"] = True
            result["question"] = "%d + %d" % (num_a, num_b)
        else:
            result["valid"] = False
    return jsonify(**result)


@proposals.route('/assets/<path:path>')
def asset(path):
    proposals.logger.info("assets accessed")
    proposals.logger.info("Requested for {}".format(path))
    source_path = _proposal_static_path / 'assets'
    proposals.logger.info("Sending from: {}".format(source_path))
    return send_from_directory(source_path.as_posix(), path)


@proposals.route('/navlinks', methods=["GET"])
def navlinks():
    logged_in = False
    can_review = False
    number_of_proposals = 0
    my_proposals_text = ""
    submissions_allowed = proposals.config.get('CALL_OPEN')
    reviewing_allowed = proposals.config.get('CALL_OPEN') or proposals.config.get('REVIEWING_ONLY')
    if session.get("id", False):
        logged_in = True
        user = User.query.filter_by(email=session["id"]).first() # email not primary key, may not be unique.
        number_of_proposals = len(user.proposals)
        can_review = user.role == Role.reviewer
        my_proposals_text = "My Proposal" if number_of_proposals == 1 else "My Proposals"
    links_data = (
        ("Keynotes", url_for("nikola.stories", path="2017/keynotes.html"), True),
        ("Full-day Workshops", url_for("nikola.stories", path="2017/fulldayworkshops.html"), True),
        ("Schedule", url_for("nikola.stories", path="2017/schedule.html"), True),
        ("Sessions", url_for("nikola.stories", path="2017/sessions.html"), True),
        ("Presenters", url_for("nikola.stories", path="2017/presenters.html"), True),
        ("Login", url_for("proposals.login"), not logged_in and (submissions_allowed or reviewing_allowed)),
        ("Register", url_for("proposals.register"), not logged_in and (submissions_allowed or reviewing_allowed)),
        ("Account", url_for("proposals.register"), logged_in),
        (my_proposals_text, url_for("proposals.show_proposals"), logged_in and number_of_proposals > 0),
        ("Submit Proposal", url_for("proposals.submit_proposal"), logged_in and submissions_allowed),
        ("Review Proposals", url_for("proposals.review_proposal"), logged_in and reviewing_allowed and can_review),
        ("Log out", url_for("proposals.logout"), logged_in),
        ('Administrate', '/admin/', proposals.config.get('ADMINISTERING')),
    )
    return jsonify(links_data)


@proposals.route('/current_user', methods=["GET"])
def current_user():
    user_info = {"id": ""}
    if session.get("id", False):
        user = User.query.filter_by(email=session["id"]).first()
        if user:
            user_info["id"] = user.email
            user_info["first_name"] = user.user_info.first_name
            user_info["last_name"] = user.user_info.last_name
    return jsonify(**user_info)


def find_element(data, identifier):
    for it in data:
        if it.id == identifier:
            return it
    return None


def find_next_element(data, identifier):
    """
    Return the next element after identifier.
    """
    found = False
    for it in data:
        if found:
            return it
        if it.id == identifier:
            found = True
    return None


def find_next_not_reviewed_element(data, identifier, user_id):
    found = False
    for it in data:
        if found:
            score = Score.query.filter_by(proposal_id=it.id, reviewer=user_id).first()
            if score is None or score.score == 0:
                return it
        if it.id == identifier:
            found = True
    return None


def neighborhood(iterable):
    iterator = iter(iterable)
    prev_item = None
    current_item = next(iterator)  # throws StopIteration if empty.
    for next_item in iterator:
        yield (prev_item, current_item, next_item)
        prev_item = current_item
        current_item = next_item
    yield (prev_item, current_item, None)
