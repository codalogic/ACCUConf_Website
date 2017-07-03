function registerUser() {
    if (validateRegistrationData()) {
        //alert ("Valid");
        //$('#registrationForm').submit();
        /* $.ajax({
         *     method: "POST",
         *     url: "/proposals/register",
         *     data: $('#registrationForm').serialize(),
         *     contentType: "application/json"
         * });*/
        var captcha = $("#captcha").val();
        var solved = $("#puzzle").val();
        $.ajax({
            method: "POST",
            url: "/proposals/captcha/validate",
            data: {"question_id": captcha, "answer": solved},
            contentType: "application/json",
            success: function(data) {
                alert(data.valid);
            }
        });
        return true;
    } else {
        alert ("Invalid");
        return false;
    }
}

function validateRegistrationData() {
    var email = $('#email').val();
    var password = $('#password').val();
    var salutation = $('#salutation').val();
    var firstName = $('#firstname').val();
    var lastName = $('#lastname').val();
    var suffix = $('#suffix').val();
    var phone = $('#phone').val();
    var country = $('#country').val();
    var state = $('#state').val();
    var states = $('#states').val();
    var pincode = $('#pincode').val();
    var question = $('#question').val();
    var captcha = $('#captcha').val();
    var submit = $('#submit');
    if (!isEmail(email)) {
        $('#emailalert').text("Email should be of the format user@example.com");
        return false;
    } else {
        $('#emailalert').text();
    }
    if (!passwordValid(password)) {
        return false;
    }
    if (!nameValid(firstName) || !nameValid(lastName)) {
        return false;
    }
    if (!phoneValid(phone)) {
        return false;
    }
    if (!stateValid(state)) {
        return false;
    }
    if (!postalCodeValid(pincode)) {
        return false;
    }
    if (!captchaValid(captcha)) {
        return false;
    }

    submit.disabled = false;
    return true;
}

function isEmail(email) {
  var regex = /^([a-zA-Z0-9_.+-])+\@(([a-zA-Z0-9-_])+\.)+([a-zA-Z0-9])+$/;
  console.log("Email is: " + email);
  return regex.test(email);
}

function passwordValid(password) {
    if (password.length < 8) {
        return false;
    }
    if (!/\d/.test(password)) {
        return false;
    }
    if (!/[a-z]/.test(password)) {
        return false;
    }
    if (!/[A-Z]/.test(password)) {
        return false;
    }
    if (/[^0-9a-zA-Z!@#$%^&*\(\)<>?\|\/\\]/.test(password)) {
        return false;
    }
    return true;
}

function nameValid(name) {
    if (name.length < 1) {
        return false;
    }
}

function phoneValid(phone) {
    if (/[^0-9\-\+]+/.test(phone)) {
        return false;
    }
    return true;
}

function stateValid(state) {
    return true;
}

function postalCodeValid(code) {
    if (/[^0-9a-zA-Z\s]/.test(code)) {
        return false;
    }
    return true;
}

function captchaValid(captcha) {
    if (/\d+/.test(captcha)) {
        return true;
    }
    return false;
}

function checkDuplicate() {
    var email = $('#email').val();
    if (!isEmail(email)) {
        $('#emailalert').text("Please provide a valid email address");
        $('#submit').attr("disabled", true);
    } else {
        $('#emailalert').text();
        $('#submit').removeAttr("disabled");
    }
    var url = "/proposals/check/" + email;
    $.ajax({
        type: "GET",
        url: url,
        dataType: "json",
        success: function(data) {
            if (data.duplicate === true) {
                $('#emailalert').text("User id already exists!!!");
                $('#submit').attr("disabled", true);
            } else {
                $('#emailalert').text("");
                $('#submit').removeAttr("disabled");
            }
        }
    });

}

function notify(message) {
    $("#helpmessage").text(message);
    $("#helpmessage").fadeIn(100);
    //$("#helpmessage").fadeOut(3000);
}

function hidehelp() {
    $("#helpmessage").fadeOut(100);
}

function loadState(ctry_id, state_sel, state_txt, hideParent) {
    var ctry_loc = '#' + ctry_id;
    var state_sel_loc = '#' + state_sel;
    var state_txt_loc = '#' + state_txt;
    var $sel = $(ctry_loc);
    var cVal = $(ctry_loc).val();
    var cName = $("option:selected", $sel).text()
    hideParent = typeof hideParent !== 'undefined' ? hideParent : false;
    $(state_sel_loc).empty();
    $.each(countryData, function(index) {
        if (countryData[index].alpha3 === cVal) {
            if (countryData[index].hasOwnProperty("regions")) {
                var regions = countryData[index].regions;
                regions.sort(function(a, b) {
                    var aUpper = a.name.toUpperCase();
                    var bUpper = b.name.toUpperCase();
                    if (aUpper < bUpper) {
                        return -1;
                    }
                    if (aUpper > bUpper) {
                        return 1;
                    }
                    return 0;
                });
                if (hideParent) {
                    $(state_txt_loc).parent().hide();
                    $(state_sel_loc).parent().show();
                    $(state_txt_loc).hide();
                    $(state_sel_loc).show();
                } else {
                    $(state_txt_loc).hide();
                    $(state_sel_loc).show();
                }
                $.each(regions, function(name, value) {
                    $(state_sel_loc).append('<option value="' + value.code + '">' + value.name + '</option>');
                });
            } else {
                if (hideParent) {
                    $(state_sel_loc).parent().hide();
                    $(state_txt_loc).parent().show();
                    $(state_sel_loc).hide();
                    $(state_txt_loc).show();
                } else {
                    $(state_sel_loc).hide();
                    $(state_txt_loc).show();
                }
            }

        }
    });
}

function updateState() {
    var state = $('#states').val();
    var state_tb = $('#state');
    if (!$('#state').is(":visible")) {
        $('#state').val(state);
    }
}

function addPresenterOld() {
    var presenter = $('#presenter').val();
    if (!isEmail(presenter)) {
        return false;
    }
    var presenters_sel = $('#presenters');
    var allPresenters = [];
    $('#presenters option').each(function() {
        console.log($(this).val());
        allPresenters.push($(this).val());
    });
    if (!allPresenters.length) {
        $('#presenters').append('<option value="' + presenter + '">' + presenter + '</option>');
        allPresenters.push(presenter);
    }
    $.each(allPresenters, function(idx) {
        if (presenter === allPresenters[idx]) {
            console.log("Entry already present");
        } else {
            presenters_sel.append('<option value="' + presenter + '">' + presenter + '</option>');
        }
    });

}

function addPresenter(tableId) {
    var presenter_tbl_loc = '#' + tableId;
    var presenter_loc = presenter_tbl_loc + '> tbody > tr';
    var count = $(presenter_loc).length;
    var onChangeString = "javascript:loadState('p_ctry_" + count + "', 'p_states_" + count + "', 'p_state_" + count + "', true);";

    var htmlString = "<tr> <td class=\"narrow\"> <input type=\"radio\" name=\"lead\" id=\"lead\" value=\"" + count +  "\"> </td> <td> <input type=\"text\" name=\"p_email_" + count + "\" id=\"p_email_" + count + "\" placeholder=\"Email Address\"> </td>  <td> <input type=\"text\" name=\"p_fname_" + count + "\" id=\"p_fname_" + count + "\" placeholder=\"First Name\"> </td> <td> <input type=\"text\" name=\"p_lname_" + count + "\" id=\"p_lname_" + count + "\" placeholder=\"Last Name\"> </td>  <td> <select class=\"widetable\" name=\"p_ctry_" + count + "\" id=\"p_ctry_" + count + "\" onchange=\"" + onChangeString + "\" onkeyup=\"this.onchange();\" onmouseup=\"this.onchange();\"> </td> <td> <input type=\"text\" name=\"p_state_" + count + "\" id=\"p_state_" + count + "\" placeholder=\"State\"> </td> <td style=\"display: none;\"> <select class=\"widetable\" name=\"p_states_" + count + "\" id=\"p_states_" + count + "\"> </td> <td> <button type=\"button\" class=\"adder\" onclick=\"javascript:addPresenter('presenterstable');\">+</button> </td> </tr>";

    $(presenter_tbl_loc).find('tbody')
        .append(htmlString);
    var options = $('#p_ctry_1 > option').clone();
    var new_loc = '#p_ctry_' + count;
    $(new_loc).append(options);
}

function uploadProposal() {
    var proposalTitle = $('#title').val();
    var proposal = $('#proposal').val();
    var proposalType = $('#proposaltype').val();
    var presenterRows = $("#presenters-body tr");
    var proposer = $("#def_email").text();
    var presenters = [];
    var leadId = $('input[name=lead]:checked', '#proposalform').val();
    if (leadId === undefined) {
        leadId = 1;
    }
    $("#presenters-body > tr").each(function(idx) {
        var cells = $(this).find('td');
        var presenter = {
            "lead": (leadId == (idx + 1)) ? 1 : 0,
            "email" : cells[2].innerText,
            "fname" : cells[3].innerText,
            "lname" : cells[4].innerText,
            "country" : cells[5].innerText,
            "state" : cells[6].innerText
        };
        presenters.push(presenter);
    });
    var proposalData = {
        "title": proposalTitle,
        "abstract": proposal,
        "proposer": proposer,
        "proposalType": proposalType,
        "presenters": presenters
    };
    $.ajax({
        url: "/proposals/upload_proposal",
        data: JSON.stringify(proposalData),
        type: "POST",
        method: "POST",
        dataType: "json",
        contentType: "application/json",
        success: function(data) {
            console.log(data);
            if (data.success) {
                alert(data.message);
                window.location = data.redirect;
            } else {
                $('#alert').text(data.message);
            }
        },
        error: function(data) {
            console.log("Error in proposal submission: " + data);
        }
    });
    return true;
}

function validatePresenter(details) {
    return true;
}

function addNewPresenter() {
    var email = $("#add-presenter-email").val();
    var fname = $("#add-presenter-fname").val();
    var lname = $("#add-presenter-lname").val();
    var ctry = $("#add-presenter-country").val();
    var state_sel = $("#add-presenter-states").val();
    var state_txt = $("#add-presenter-state").val();
    var state;
    if (state_txt.length) {
        state = state_txt;
    } else {
        state = state_sel;
    }
    var presenters = $("#presenters-body");
    var trCnt = $("#presenters-body tr").length;
    var sno = trCnt + 1;
    var presenterRow = _.template($("#presenters-row-template").html());
    presenters.append(presenterRow({"sno": sno, "email": email, "fname": fname, "lname": lname, "ctry": ctry, "state": state}));
    resetModal();
    $("#add-presenter-modal").modal('hide');
    return true;
}

function resetModal() {
    $('.modal').on('hidden.bs.modal', function(){
        $("#add-presenter-modal").find('form')[0].reset();
    });
}

function deleteRow(rowIdx) {
    var presenters = $("#presenters-body");
    var msg = $("#presenters-body tr:eq(1)").text();
    alert(msg);
}

function showPointer(element) {
    element.css("cursor", "pointer");
}

function showDefaultPointer(element) {
    element.css("cursor", "default");
}


function uploadReview(button) {
    var button = button.value;
    var score = $("#score").val();
    var comment = $("#comment").val();
    var reviewData = {
        "button" : button,
        "score" : score,
        "comment" : comment
    };
    $.ajax({
        method: "POST",
        url: "/proposals/upload_review",
        data: JSON.stringify(reviewData),
        contentType: "application/json",
        success: function(data) {
            console.log(data);
            if (data.success) {
                window.location = data.redirect;
            } else {
                $('#alert').text(data.message);
            }
        }
    });

    return true;
}
