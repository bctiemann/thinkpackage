globals = {};

function nop() {}

function getCookie(name) {
    var cookieValue = null;
    if (document.cookie && document.cookie !== '') {
        var cookies = document.cookie.split(';');
        for (var i = 0; i < cookies.length; i++) {
            var cookie = jQuery.trim(cookies[i]);
            if (cookie.substring(0, name.length + 1) === (name + '=')) {
                cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                break;
            }
        }
    }
    return cookieValue;
}
var csrftoken = getCookie('csrftoken');

function csrfSafeMethod(method) {
    // these HTTP methods do not require CSRF protection
    return (/^(GET|HEAD|OPTIONS|TRACE)$/.test(method));
}
$.ajaxSetup({
    beforeSend: function(xhr, settings) {
        if (!csrfSafeMethod(settings.type) && !this.crossDomain) {
            xhr.setRequestHeader("X-CSRFToken", csrftoken);
        }
    }
});

function displayErrorDialog(data) {
    var errorList = $('<ul>', {
        class: 'error-list',
    });
    for (var error in data) {
        var errorLi = $('<li>', {
            class: 'error',
        });
        errorLi.append($('<span>', {
            class: 'error-label',
            text: error,
        }));
        var errorMessages = $('<ul>', {
            class: 'error-messages',
        });
        for (var message in data[error]) {
            errorMessages.append($('<li>', {
                text: data[error][message].message,
            }));
        }
        errorLi.append(errorMessages);
        errorList.append(errorLi);
    }
    $('#dialog_errors').empty().append(errorList).dialog('open');
};

var infiniteScrollTable = function(target, callback) {
    var targetTbody = $(`${target} tbody`);
    targetTbody.scroll(function(ev) {
        var lastRow = $('#list_shipments tbody tr').last();
        var elementTop = lastRow.position().top;
        var elementBottom = elementTop + lastRow.outerHeight();
        var viewportBottom = $(this).height();
        if (viewportBottom > elementTop && !globals['fetching']) {
            callback();
        }
    });
};

$(document).ready(function() {

    $('#dialog_errors').dialog({
        autoOpen: false,
        resizable: false,
        modal: true,
        minWidth: 400,
        position: { my: "top", at: "top+200", of: window },
        buttons: {
            OK: function() {
                $( this ).dialog( "close" );
            }
        }
    });

});
