var cgiroot = '/warehouse_app/';
var scanInput = '';
var scanMode = null;
//var onPallet = {};
var pallet_selected = null;
var removeScanResult = null;
var idleTime = 0;
var mins_timeout = 540; // Auto-logout after 9 hours
var product_tapped = false;
//var globals = {};

$.ajax({async:false})

//function nop() {}


function doSend() {
	var objAid = document.getElementById('aid');
	var aid = objAid.value;
$.get("tkt.cfm", { aid: +aid} );

}



function processScancode() {
    console.log(scanInput);
    if (scanInput.match(/^1TP:/)) {
        var url = cgiroot+'ajax_barcode.cfm?m='+scanMode+'&c='+scanInput;
        if (scanMode == 'pallet') {
            var PRID = scanInput.substring(4);
            var cases_scanned = parseInt($('#cases_'+pallet_selected+'_'+PRID).html()) + 1;
            var cases_req = parseInt($('#cases_req_'+pallet_selected+'_'+PRID).html());
            $('#cases_'+pallet_selected+'_'+PRID).html(cases_scanned);
            if (pallet_selected != 'new') {
                if (cases_scanned == cases_req) {
                    $('#cases_'+pallet_selected+'_'+PRID).removeClass('cases_incomplete');
                    $('#cases_'+pallet_selected+'_'+PRID).addClass('cases_complete');
                } else {
                    $('#cases_'+pallet_selected+'_'+PRID).addClass('cases_incomplete');
                    $('#cases_'+pallet_selected+'_'+PRID).removeClass('cases_complete');
                }
            }
            $.getJSON(url,function(data) {

                if (pallet_selected == 'new') {

                    if (data.PRID) {
                        if (!$('#product_new_'+PRID).length) {
                            var tr = $('<tr>',{
                                id: 'product_new_'+data.PRID,
                                PRID: data.PRID,
                                productid: data.PRODUCTID
                            });
                            var td_product = $('<td>',{ class: 'product_name' });
                            td_product.append($('<p>',{ text: data.CONAME, class: 'co_name' }));
                            td_product.append($('<p>',{ text: data.PNAME }));
                            tr.append(td_product);
                            tr.append($('<td>',{ id: 'cases_new_'+PRID, class: 'numeric', text: 1 }));
                            $('#pallet_contents_new').append(tr);
                        }
                    }

                }

                if (cases_scanned > cases_req) {

                    $('#cases_'+pallet_selected+'_'+PRID).html(cases_req);
                    $('#cases_'+pallet_selected+'_'+PRID).removeClass('cases_incomplete');
                    $('#cases_'+pallet_selected+'_'+PRID).addClass('cases_complete');
                    $('#dialog_count_exceeded').dialog("open");

                } else {

                    $('p#scanned_pname').html(data.PNAME);
                    var dialog_timeout = 1000;
                    if ($('#cases_'+pallet_selected+'_'+PRID).length) {
                        $('p#scan_validity').html('');
                        $('#scan_result').removeClass('wrong_scan');
                        var dialog_timeout = 2000;
                        $('#item_count').attr('PRID',PRID);
                        if (!product_tapped) {
                            $('#enter_count').show();
                        }
                    } else if (!pallet_selected) {
                        $('#item_count_wrap').hide();
                        $('p#scan_validity').html('NO PALLET SELECTED');
                        $('#scan_result').addClass('wrong_scan');
                        var dialog_timeout = 2000;
                        product_tapped = false;
                    } else {
                        $('#item_count_wrap').hide();
                        $('p#scan_validity').html('INVALID SCAN');
                        $('#scan_result').addClass('wrong_scan');
                        var dialog_timeout = 2000;
                        if (!data.PRODUCTID) {
                            $('p#scanned_pname').html(PRID+' - unrecognized code');
                        }
                        product_tapped = false;
                    }
                    $('#scan_result').show();
                    if (!product_tapped) {
                        removeScanResult = setTimeout('hideScanResult()',dialog_timeout);
                    }
                    product_tapped = false;

                }

            });
        } else {
            $('#barcode_info').load(url,function(html) {
            });
        }
    }
}

function hideScanResult() {
    $('#scan_result').fadeOut(200);
    $('#item_count').val('');
    $('#enter_count').hide();
    $('#item_count_wrap').hide();
}

function enableEnterCount() {
    clearTimeout(removeScanResult);
    $('#enter_count').hide();
    $('#item_count_wrap').show();
}

function enterCount() {
    var ic = $('#item_count');
    $('#barcode').focus();
    ic.val(ic.val() > 0 ? ic.val() : 0);
    if (ic.val() > parseInt($('#cases_req_'+pallet_selected+'_'+ic.attr('PRID')).html())) {
        $('#dialog_count_exceeded').dialog("open");
        ic.val(parseInt($('#cases_req_'+pallet_selected+'_'+ic.attr('PRID')).html()));
    }
    $('#cases_'+pallet_selected+'_'+ic.attr('PRID')).html(ic.val());
    hideScanResult();
}

function showToggleInfo() {
    $('.above_login').hide();
    $('#toggle_info').show();
}

function selectReceivable() {
//    var url = cgiroot+'ajax_receivable.cfm?r='+$('#receivableid').val();
    var url = cgiroot + 'receive/' + $('#receivableid').val() + '/form/';
console.log(url);
    $('#receivable_details').load(url,function() {
    });
}

function selectShipment() {
    $('#barcode').focus();
    var url = cgiroot+'ajax_pallet.cfm?s='+$('#shipmentid').val();
    $('#pallet_contents').load(url,function() {
    });
}

function selectPallet(shipmentid) {
    $('.pallet').removeClass('selected');
    $('.pallet button.completepallet').prop('disabled',true);
    $('#pallet_'+shipmentid).addClass('selected');
    $('#pallet_'+shipmentid+' button.completepallet').prop('disabled',false);
    pallet_selected = shipmentid;
//    $('#barcode').css({top: $('body').scrollTop(),left: -1000});
    $('#barcode').focus();
}

function submitReceivable(receivableid) {
    var receivable = {
        receivableid: receivableid,
        cases: $('#cases').val()
    };
//    var url = cgiroot+'ajax_receivable.cfm'
    var url = cgiroot + '/receive/' + receivableid + '/confirm/';
    $.post(url,receivable,function(data) {
console.log(data);
        if (data.success) {
            $('#dialog_success_receivable').dialog("open");
//            setTimeout("openActionPage('menu')",5000);
        } else {
            displayErrorDialog(data);
        }
/*
        } else if ('ERROR' in data) {
            $('#dialog_error_receivable').html(data.ERROR);
            $('#dialog_error_receivable').dialog("open");
//            $('#error').html(data.ERROR);
//            setTimeout("$('#error').html('')",5000);
        } else if ('WARNING' in data) {
            $('#dialog_warning_receivable').html(data.WARNING);
            $('#dialog_warning_receivable').dialog("open");
//            $('#error').html(data.WARNING);
//            setTimeout("openActionPage('menu')",5000);
        }
*/
    },'json');
}

function completePallet(shipmentid,force) {
    var pallet = {
        products: '',
        shipmentid: shipmentid == 'new' ? 0 : shipmentid
    };
    var products = [];

    var required_match = true;
    $('#pallet_contents_'+shipmentid).find('tr').each(function() {
        var num_scanned = parseInt($('#cases_'+shipmentid+'_'+$(this).attr('PRID')).html());
        if (shipmentid != 'new') {
            var num_required = parseInt($('#cases_req_'+shipmentid+'_'+$(this).attr('PRID')).html());
            if (num_scanned != num_required) required_match = false;
        }
        products.push($(this).attr('productid')+':'+num_scanned);
    });


    if (required_match || force) {
        $('#modal_overlay').show();
        pallet['products'] = products.join(',');
console.log(pallet);
        var url = cgiroot+'ajax_pallet.cfm'
        $.post(url,pallet,function(data) {
console.log(data);
            $('#modal_overlay').hide();
            if ('ERROR' in data) {
                $('#dialog_error_pallet').html(data.ERROR);
                $('#dialog_error_pallet').dialog("open");
//                setTimeout("$('#error').html('')",5000);
            } else if ('WARNING' in data) {
                $('#dialog_warning_pallet').html(data.WARNING);
                $('#dialog_warning_pallet').dialog("open");
//                setTimeout("openActionPage('pallet')",5000);
            } else {
                if (!required_match && !force) {
                    $('#dialog_mismatch_warning').dialog("open");
                    openActionPage('pallet');
                } else {
                    $('#dialog_success_pallet').dialog("open");
                }
//                setTimeout("openActionPage('pallet')",5000);
            }
        },'json');
    } else {
        globals['shipmentid'] = shipmentid;
        $('#dialog_mismatch_warning').dialog("open");
    }
}

function openActionPage(page) {
    pallet_selected = null;
    $('#modal_overlay').show();
//    var url = cgiroot+page+'.cfm';
    var url = cgiroot + '/' + page + '/';
    $('#content').load(url,function() {
        $('#modal_overlay').hide();
        $('#barcode').focus();
        scanMode = page;

        $('.cases_incomplete').click(function() {
            scanInput = '1TP:'+$(this).parent().attr('prid');
            enableEnterCount();
            product_tapped = true;
            processScancode();
        });
    });
//    window.location = page+'.cfm';
}

function doLogout() {
    window.location = cgiroot + 'sign_out/';
}

function timerIncrement() {
    idleTime = idleTime + 1;
    if (idleTime > mins_timeout) {
        doLogout();
    }
}

$(document).ready(function() {

    $(document).keypress(function(e) {
        if (scanMode) {
            if (e.which == 13) {
                processScancode();
                scanInput = '';
            } else {
                var char = String.fromCharCode(e.which);
                var snip = scanInput.slice(-4);
                if (snip == '1TP:') {
                    scanInput = snip;
                    $('#barcode').val(snip);
                }
                if (e.which >= 32)
                    scanInput += char;
//                $('#status').html(scanInput);
            }
        }
    });
    $('#barcode').focus();

    $('#dialog_mismatch_warning').dialog({
        autoOpen: false,
        resizable: false,
        modal: true,
        width: 400,
        dialogClass: "no-close",
        position: { my: "top", at: "top+200", of: window },
        buttons: {
            'Complete pallet': function() {
                $( this ).dialog( "close" );
                completePallet(globals['shipmentid'],true);
            },
            Cancel: function() {
                $( this ).dialog( "close" );
            }
        }
    });

    $('#dialog_error_pallet').dialog({
        autoOpen: false,
        resizable: false,
        modal: true,
        dialogClass: "no-close",
        position: { my: "top", at: "top+200", of: window },
        buttons: {
            OK: function() {
                $( this ).dialog( "close" );
            }
        }
    });

    $('#dialog_warning_pallet').dialog({
        autoOpen: false,
        resizable: false,
        modal: true,
        dialogClass: "no-close",
        position: { my: "top", at: "top+200", of: window },
        buttons: {
            OK: function() {
                openActionPage('pallet');
                $( this ).dialog( "close" );
            }
        }
    });

    $('#dialog_success_pallet').dialog({
        autoOpen: false,
        resizable: false,
        modal: true,
        dialogClass: "no-close",
        position: { my: "top", at: "top+200", of: window },
        buttons: {
            OK: function() {
                openActionPage('pallet');
                $( this ).dialog( "close" );
            }
        }
    });

    $('#dialog_error_receivable').dialog({
        autoOpen: false,
        resizable: false,
        modal: true,
        dialogClass: "no-close",
        position: { my: "top", at: "top+200", of: window },
        buttons: {
            OK: function() {
                $( this ).dialog( "close" );
            }
        }
    });

    $('#dialog_warning_receivable').dialog({
        autoOpen: false,
        resizable: false,
        modal: true,
        dialogClass: "no-close",
        position: { my: "top", at: "top+200", of: window },
        buttons: {
            OK: function() {
                openActionPage('menu');
                $( this ).dialog( "close" );
            }
        }
    });

    $('#dialog_success_receivable').dialog({
        autoOpen: false,
        resizable: false,
        modal: true,
        dialogClass: "no-close",
        position: { my: "top", at: "top+200", of: window },
        buttons: {
            OK: function() {
                openActionPage('menu');
                $( this ).dialog( "close" );
            }
        }
    });

    $('#dialog_count_exceeded').dialog({
        autoOpen: false,
        resizable: false,
        modal: true,
        dialogClass: "no-close",
        position: { my: "top", at: "top+200", of: window },
        buttons: {
            OK: function() {
                $( this ).dialog( "close" );
            }
        }
    });

    var idleInterval = setInterval(timerIncrement, 60000); // 1 minute

    $(this).click(function (e) {
        idleTime = 0;
    });

});

