import re


def validate_email(email):
    email_pattern = re.compile("^([a-zA-Z0-9_.+-])+@(([a-zA-Z0-9-_])+\.)+([a-zA-Z0-9])+$")
    if email_pattern.search(email):
        from accuconf.models import User
        u = User.query.filter_by(email=email).first()
        if u:
            return False
        else:
            return True
    else:
        return False


def validate_password(password):
    return re.search("\\d", password) and re.search("[a-z]", password) and re.search("[A-Z]", password) and len(password) >= 8


def validate_proposal_data(proposal_data):
    mandatory_keys = ["title", "abstract", "session_type", "presenters"]
    for key in mandatory_keys:
        if key not in proposal_data:
            return False, "{} information is not present in proposal".format(key)

        if proposal_data[key] is None:
            return False, "{} information should not be empty".format(key)
    if type(proposal_data["presenters"]) != list:
        return False, "presenters data is malformed"

    if len(proposal_data["presenters"]) < 1:
        return False, "At least one presenter needed"

    if len(proposal_data.get("title")) < 5:
        return False, "Title is too short"

    if len(proposal_data.get("abstract")) < 50:
        return False, "Proposal too short"

    (result, message) = validate_presenters(proposal_data["presenters"])
    if not result:
        return result, message

    return True, "validated"


def validate_presenters(presenters):
    mandatory_keys = ["lead", "email", "fname", "lname", "country", "state"]
    lead_found = False
    lead_presenter = ""
    for presenter in presenters:
        for key in mandatory_keys:
            if key not in presenter:
                return False, "{} attribute is mandatory for Presenters".format(key)

            if presenter[key] is None:
                return False, "{} attribute should have valid data".format(key)

        if "lead" in presenter and "email" in presenter:
            if presenter["lead"] and lead_found:
                return False, "{} and {} are both marked as lead presenters".format(presenter["email"], lead_presenter)
            elif presenter["lead"] and not lead_found:
                lead_found = True
                lead_presenter = presenter["email"]

    return True, "validated"
