from flask import render_template, jsonify, redirect, url_for, session, request
from flask import send_from_directory, g
from datetime import datetime
from accuconf import db
from accuconf.models import MathPuzzle, Proposal, ProposalComment, ProposalPresenter, ProposalReview, User
from accuconf.proposals.utils.proposals import SessionType
from accuconf.proposals.utils.validator import validate_email, validate_password, validate_proposal_data
import hashlib
from random import randint
from . import proposals

_proposal_static_path = None
_end_of_call_for_session = datetime(2016,12,2,23,58,00)


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


@proposals.route("/")
def index():
    if proposals.config.get("MAINTENANCE"):
        return redirect(url_for("proposals.maintenance"))

    # when_where = {}
    # committee = {}
    # venuefile = proposals.config.get('VENUE')
    # committeefile = proposals.config.get('COMMITTEE')
    # if venuefile.exists():
    #     when_where = json.loads(venuefile.open().read())
    #
    # if committeefile.exists():
    #     committee = json.loads(committeefile.open().read())
    #
    # frontpage = {
    #     "title": "ACCU Conference 2017",
    #     "data": "Welcome to ACCU Conf 2017",
    #     "when_where": when_where,
    #     "committee": committee.get("members", [])
    # }
    # if 'id' in session:
    #     user = User.query.filter_by(id=session["id"]).first()
    #     if not user:
    #         proposals.logger.error("id key present in session, but no user")
    #         return redirect(url_for('proposals.logout'))
    #     else:
    #         frontpage["user_name"] = "%s %s" % (user.user_info.first_name,
    #                                             user.user_info.last_name)
    # return render_template("proposals/index.html", page=frontpage)
    return redirect(url_for('nikola.index'))


@proposals.route("/maintenance")
def maintenance():
    return render_template("maintenance.html", page={})


@proposals.route("/login", methods = ['GET', 'POST'])
def login():
    if proposals.config.get("MAINTENANCE"):
        return redirect(url_for("proposals.maintenance"))
    if request.method == "POST":
        user_id = request.form['usermail']
        password = request.form['password']
        user = User.query.filter_by(user_id=user_id).first()
        if not user:
            return redirect(url_for('index'))
        password_hash = hashlib.sha256(password.encode("utf-8")).hexdigest()
        if user.password == password_hash:
            session['id'] = user.user_id
            proposals.logger.info("Auth successful")
            g.user = user_id
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
        user = User.query.filter_by(user_id=session["id"]).first()
        if user is not None:
            edit_mode = True

    if request.method == "POST":
        # Process registration data
        if not edit_mode: # it is not allowed to change the email address at the moment, because this is used as key
            user_email = request.form["usermail"]

        # In case that no user pass was provided, we don't update the field
        user_pass = None
        if len(request.form["password"].strip()) > 0:
            user_pass = request.form["password"]

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
        bio = request.form['bio']

        encoded_pass = None
        if type(user_pass) == str and len(user_pass):
            encoded_pass = hashlib.sha256(user_pass.encode('utf-8')).hexdigest()

        page = {}
        if edit_mode:
            user.first_name = first_name
            user.last_name = last_name
            if encoded_pass:
                user.password = encoded_pass
            user.phone = phone
            user.bio = bio

            user.country = country
            user.state = state
            user.postal_code = postal_code
            user.town_city = town_city
            user.street_address = street_address

            if encoded_pass:
                User.query.filter_by(user_id=user.user_id).update({ 'password': encoded_pass })

            UserInfo.query.filter_by(user_id=user.user_id).update({
                    'first_name': first_name,
                    'last_name': last_name,
                    'phone': phone,
                    'bio': bio
                })
            UserLocation.query.filter_by(
                user_id=user.user_id).update({
                    'country': country,
                    'state': state,
                    'postal_code': postal_code,
                    'town_city': town_city,
                    'street_address': street_address
                })
            page["title"] = "Account update successful"
            page["data"] = "Your account details were successful updated."

        else:
            if not validate_email(user_email):
                page["title"] = "Registration failed"
                page["data"] = "Registration failed: Invalid/Duplicate user id."
                page["data"] += "Please register again"
                return render_template("registration_failure.html", page=page)
            elif not validate_password(user_pass):
                page["title"] = "Registration failed"
                page["data"] = "Registration failed: Password did not meet checks."
                page["data"] += "Please register again"
                return render_template("registration_failure.html", page=page)

            if not validate_email(user_email):
                page["title"] = "Registration failed"
                page["data"] = "Registration failed: Invalid/Duplicate user id."
                page["data"] += "Please register again"
                return render_template("registration_failure.html", page=page)
            elif not validate_password(user_pass):
                page["title"] = "Registration failed"
                page["data"] = "Registration failed: Password did not meet checks."
                page["data"] += "Please register again"
                return render_template("registration_failure.html", page=page)

            errors = []
            for field, field_name in (
                    (bio, 'biography'),
                    (user_email, 'email'),
                    (user_pass, 'password'),
                    (cpassword, 'password confirmation'),
                    (first_name, 'first name'),
                    (last_name, 'last name'),
                    (town_and_city, 'town and city'),
                    (phone, 'phone number'),
                    (postal_code, 'pin code'),
                    (street_address, 'street address'),):
                if not field.strip():
                    errors.append("The %s field was not filled in." % field_name)

            if errors:
                errors.append('')
                errors.append("Please register again")
                page = {}
                page["title"] = "Registration failed"
                page["data"] = ' '.join(errors)
                return render_template("registration_failure.html", page=page)

            else:
                new_user = User(
                    user_email,
                    encoded_pass,
                    first_name,
                    last_name,
                    phone,
                    bio,
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
        page = {}
        page["mode"] = "edit_mode" if edit_mode else "register"

        page["email"] = user.user_id if edit_mode else ""
        page["first_name"] = user.first_name if edit_mode else ""
        page["last_name"] = user.last_name if edit_mode else ""
        page["phone"] = user.phone if edit_mode else ""
        page["bio"] = user.bio if edit_mode else ""

        page["country"] = user.country if edit_mode else "GBR" # UK shall be the default
        page["state"] = user.state if edit_mode else "GB-ENG"
        page["postal_code"] = user.postal_code if edit_mode else ""
        page["town_city"] = user.town_city if edit_mode else ""
        page["street_address"] = user.street_address if edit_mode else ""

        num_a = randint(10, 99)
        num_b = randint(10, 99)
        sum = num_a + num_b
        question = MathPuzzle(sum)
        db.session.add(question)
        db.session.commit()

        page["title"] = "Account Information" if edit_mode else "Register"
        page["data"] = "Here you can edit your account information" if edit_mode else "Register here for submitting proposals to ACCU Conference"
        page["question"] = question.id
        page["puzzle"] = "%d + %d" % (num_a, num_b)
        page["submit_button"] = "Save" if edit_mode else "Register"
        return render_template("register.html", page=page)


@proposals.route("/show_proposals", methods=["GET"])
def show_proposals():
    if proposals.config.get("MAINTENANCE"):
        return redirect(url_for("proposals.maintenance"))
    if session.get("id", False):
        user = User.query.filter_by(user_id=session["id"]).first()
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
        user = User.query.filter_by(user_id=session["id"]).first()
        if not user:
            return render_template("not_logged_in.html", page={"name": "Submit proposal"})
        return render_template("submit_proposal.html", page={
            "title": "Submit a proposal for ACCU Conference",
            "user_name": "%s %s".format(user.first_name, user.last_name),
            "proposer": {
                "email": user.user_id,
                "first_name": user.first_name,
                "last_name": user.last_name,
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
        user = User.query.filter_by(user_id=session["id"]).first()
        if not user:
            return render_template("not_logged.html", page={"name": "Proposal Submission"})
        else:
            proposal_data = request.json
            proposals.logger.info(proposal_data)
            status, message = validate_proposal_data(proposal_data)
            response = {}
            if status:
                proposal = Proposal(proposal_data.get("proposer"),
                                    proposal_data.get("title").rstrip(),
                                    SessionType(proposal_data.get('session_type')),
                                    proposal_data.get("abstract").rstrip())
                user.proposals.append(proposal)
                db.session.add(proposal)
                presenters = proposal_data.get("presenters")
                for presenter in presenters:
                    proposal_presenter = ProposalPresenter(proposal.id,
                                                           presenter["email"],
                                                           presenter["lead"],
                                                           presenter["fname"],
                                                           presenter["lname"],
                                                           presenter["country"],
                                                           presenter["state"])
                    proposal.presenters.append(proposal_presenter)
                    db.session.add(proposal_presenter)
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
        user = User.query.filter_by(user_id=session["id"]).first()
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
                proposal_to_show_next = find_next_not_reviewed_element(all_proposals, session["review_id"], user.user_id)
            elif session["review_button_pressed"] == "previous_nr_proposal":
                proposal_to_show_next = find_next_not_reviewed_element(all_proposals_reverse, session["review_id"], user.user_id)
            elif session["review_button_pressed"] == "save":
                proposal_to_show_next = find_element(all_proposals, session["review_id"])
        else:
            proposal_to_show_next = all_proposals.first()
        session["review_button_pressed"] = ""
        if not proposal_to_show_next:
            return render_template("review_success.html", page={
                "title": "All reviews done",
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
        next_potential_not_read = find_next_not_reviewed_element(all_proposals, proposal_to_show_next.id, user.user_id)
        if next_potential_not_read is not None:
            next_not_read_available = True
        previous_potential_not_read = find_next_not_reviewed_element(all_proposals_reverse, proposal_to_show_next.id, user.user_id)
        if previous_potential_not_read is not None:
            previous_not_read_available = True
        proposal_review = ProposalReview.query.filter_by(proposal_id=proposal_to_show_next.id, reviewer=user.user_id).first()
        proposal_comment = ProposalComment.query.filter_by(proposal_id=proposal_to_show_next.id, commenter=user.user_id).first()

        speakers_info = UserInfo.query.filter_by(user_id=proposal_to_show_next.proposer).first()
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
        user = User.query.filter_by(user_id=session["id"]).first()
        if not user:
            return render_template("not_logged_in.html", page={"name": "Submit proposal"})
        if session.get("review_id", False):
            proposal = Proposal.query.filter_by(id=session["review_id"]).first()
            if proposal is not None:
                review_data = request.json
                proposals.logger.info(review_data)
                proposal_review = ProposalReview.query.filter_by(proposal_id=proposal.id, reviewer=user.user_id).first()
                if proposal_review:
                    proposal_review.score = review_data["score"]
                    ProposalReview.query.filter_by(proposal_id=proposal.id, reviewer=user.user_id).update({'score': proposal_review.score})
                else:
                    proposal_review = ProposalReview(proposal.id, user.user_id, review_data["score"])
                    proposal.reviews.append(proposal_review)
                    db.session.add(proposal_review)
                proposal_comment = ProposalComment.query.filter_by(proposal_id=proposal.id, commenter=user.user_id).first()
                if proposal_comment:
                    proposal_comment.comment = review_data["comment"].rstrip()
                    ProposalComment.query.filter_by(
                        proposal_id=proposal.id,
                        commenter=user.user_id).update({'comment': proposal_comment.comment})
                else:
                    proposal_comment = ProposalComment(proposal.id, user.user_id, review_data["comment"])
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
    u = User.query.filter_by(user_id=user).first()
    result = {}
    if u:
        result["duplicate"] = True
    else:
        result["duplicate"] = False
    return jsonify(**result)


@proposals.route("/captcha/validate", methods=["POST"])
def validate_captcha():
    captcha_info = request.json
    qid= captcha_info.get("question_id")
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
    logged_out = True
    number_of_proposals = 0
    my_proposals_text = ""
    call_for_session_is_over = _end_of_call_for_session < datetime.now()
    if session.get("id", False):
        logged_in = True
        logged_out = False
        user = User.query.filter_by(user_id=session["id"]).first()
        number_of_proposals = len(user.proposals)
        can_review = user.user_info.role == "reviewer"
        my_proposals_text = "My Proposal" if number_of_proposals == 1 else "My Proposals"
    links = {
        "0": ("Home", url_for("nikola.index"), True),
        "1": ("Login", url_for("proposals.login"), logged_out),
        "2": ("Register", url_for("proposals.register"), logged_out),
        "3": ("Account", url_for("proposals.register"), logged_in),
        "4": (my_proposals_text, url_for("proposals.show_proposals"), logged_in and number_of_proposals>0),
        "5": ("Submit Proposal", url_for("proposals.submit_proposal"), logged_in and not call_for_session_is_over),
        "6": ("Review Proposals", url_for("proposals.review_proposal"), logged_in and can_review),
        "7": ("RSS", "/site/rss.xml", True),
        "8": ("Log out", url_for("proposals.logout"), logged_in)
    }
    return jsonify(**links)


@proposals.route('/current_user', methods=["GET"])
def current_user():
    user_info = {"id": ""}
    if session.get("id", False):
        user = User.query.filter_by(user_id=session["id"]).first()
        if user:
            user_info["id"] = user.user_id
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
            review = ProposalReview.query.filter_by(proposal_id=it.id, reviewer=user_id).first()
            if review is None or review.score == 0:
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

