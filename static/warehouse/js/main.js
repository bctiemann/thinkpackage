var cgiroot = '/warehouse/';

function showShipped(show_shipped) {
    globals['shipped_filter'] = show_shipped ? 0 : 1;
    $('#shipment_details').html('');
    refreshShipments();
}

function showReceived(show_received) {
    globals['received_filter'] = show_received ? 0 : 1;
    refreshReceivables();
}

function refreshShipments(shipmentid) {
    if (!('shipped_filter' in globals)) {
        globals['shipped_filter'] = 1;
    }
    globals['startFrom'] = 0;
//    var url = cgiroot+'ajax_shipments_list.cfm?shipped_filter='+globals['shipped_filter'];
    var url = `${cgiroot}shipments/list/?shipped_filter=${globals['shipped_filter']}`;
    $('#list_shipments').load(url,function(data) {
        $('.shipment_detail').html('');
        fetchShipments(shipmentid);
    });
}

function fetchShipments(shipmentid='') {
    globals['fetching'] = true;
    var url = `${cgiroot}shipments/fetch/?shipped_filter=${globals['shipped_filter']}&start=${globals['startFrom']}&shipment_id=${shipmentid}`;
    $.get(url, function(html) {
        globals['fetching'] = false;
        $('#list_shipments tbody').append(html);
        refreshUI();
        if (shipmentid) {
            if ($('tr#shipment_' + shipmentid).length) {
                selectShipment(shipmentid);
                var rowpos = $('tr#shipment_' + shipmentid).position().top - $('table.shipments tbody').position().top;
                $('table.shipments tbody').animate({ scrollTop: rowpos});
            }
            $('.search').val(shipmentid);
        }
        globals['startFrom'] = $('tr.shipment').length;
        console.log(globals);
    })
}

function refreshReceivables(receivableid) {
    if (!('received_filter' in globals)) {
        globals['received_filter'] = 1;
    }
    globals['startFrom'] = 0;
//    var url = cgiroot+'ajax_receivables_list.cfm?received_filter='+globals['received_filter'];
    // var url = cgiroot + 'receivables/list/?received_filter=' + globals['received_filter'];
    var url = `${cgiroot}receivables/list/?received_filter=${globals['received_filter']}`;
    $('#list_receivables').load(url,function(data) {
        // refreshUI();
        fetchReceivables(receivableid);
    });
}

function fetchReceivables(receivableid='') {
    globals['fetching'] = true;
    var url = `${cgiroot}receivables/fetch/?received_filter=${globals['received_filter']}&start=${globals['startFrom']}&receivable_id=${receivableid}`;
    $.get(url, function(html) {
        globals['fetching'] = false;
        $('#list_receivables tbody').append(html);
        refreshUI();
        globals['startFrom'] = $('tr.shipment').length;
        console.log(globals);
    })
}

function selectShipment(shipmentid) {
    if (!$('#shipment_'+shipmentid).hasClass('selected')) {
        try {
            $('#dialog_shipping_info').dialog("destroy");
        } catch(err) {
            console.log(err.message);
        }
        $('.shipment_detail').html('');
        $('tr.shipment').removeClass('selected');
        $('#shipment_'+shipmentid).addClass('selected');
//        var url = cgiroot+'ajax_shipment_details.cfm?shipmentid='+shipmentid;
        var url = cgiroot + 'shipment/' + shipmentid + '/';
        $('#shipment_details').load(url,function() {
//            $('tr.product input').prop('disabled',true);
//            $('#product_'+productid+' input').prop('disabled',false);
//            $('#productdetail_'+productid+' input').prop('disabled',false);
//            $('#shipdate_'+shipmentid).datepicker();

            $('#id_date_shipped').datepicker();

            $('#dialog_shipping_info').dialog({
                autoOpen: false,
                resizable: false,
                modal: true,
                maxHeight: 680,
                width: 600,
                position: { my: "top", at: "top+50", of: window },
                buttons: {
                    Save: function() {
                        $( this ).dialog( "close" );
                        execute_saveShipment();
                    },
                    Cancel: function() {
                        $( this ).dialog( "close" );
                    }
                }
            });
            refreshUI();

        });
    }
}

function selectPallet(palletid) {
    if (!$('#pallett_'+palletid).hasClass('selected')) {
        $('.pallet_detail').html('');
        $('tr.pallet').removeClass('selected');
        $('#pallet_'+palletid).addClass('selected');
//        var url = cgiroot+'ajax_pallet_details.cfm?palletid='+palletid;
        var url = cgiroot + 'pallet/' + palletid + '/';
        $('#pallet_details').load(url,function() {
        });
    }
}

function updateShipment(shipmentid) {
    var product = {
        fnc: 'updateshipment',
        shipmentid: shipmentid,
        carrier: $('#carrier_'+shipmentid).val(),
//        tracking: $('#tracking_'+shipmentid).val(),
        shipdate: new Date($('#shipdate_'+shipmentid).val())
    };
    var url = cgiroot+'ajax_shipments_action.cfm';
    $.post(url,product,function(data) {
console.log(data);
    });
}

function uploadShipmentDoc(shipmentid) {
    globals['shipmentid'] = shipmentid; 
    $('#shipment_upfile').val('');
    $('#shipment_upload_form').dialog("open");
}

var execute_uploadShipmentDoc = function(shipmentid) {
    var data = new FormData();
    $.each($('#shipment_upfile')[0].files, function(i, file) {
        data.append('file', file);
    });
    data.append('fnc', 'upload_doc');
    data.append('shipment', globals['shipmentid']);

    $('.spinner-upload').show();

    var url = cgiroot + 'shipment/' + globals['shipmentid'] + '/docs/';
    $.ajax({
//        url: 'ajax_shipment_action.cfm',
        url: url,
        data: data,
        cache: false,
        contentType: false,
        dataType: 'json',
        processData: false,
        type: 'POST',
        success: function(data) {
console.log(data);
            $('.spinner-upload').hide();
            $('#shipment_upload_form').dialog('close');
            if (data.success) {
                var successUrl = url;
                $('#shipment_details').load(successUrl,function() {
                    refreshUI();
                });
                refreshShipments(globals['shipmentid']);
                showShipmentDocs(globals['shipmentid']);
                $('#shipment_upfile').val('');
            } else {
                displayErrorDialog(data);
            }
        },
    });
};

var deleteShipmentDoc = function(docid) {
    if (confirm('Are you sure you want to delete this document?')) {
//        var url = 'ajax_shipment_action.cfm';
        var url = cgiroot + 'shipment/doc/' + docid + '/delete/';
        var params = {
            docid: docid,
            fnc: 'delete_doc',
        };
        $.post(url, params, function(data) {
console.log(data);
            if (data.success) {
                $('#shipment_'+data.shipment_id).removeClass('selected');
                var successUrl = cgiroot + 'shipment/' + data.shipment_id + '/docs/';
                $('#shipment_details').load(successUrl,function() {
                    refreshUI();
                });
                refreshShipments(data.shipment_id);
                showShipmentDocs(data.shipment_id);
                $('#shipment_upfile').val('');
            } else {
                alert(data.message);
            }
        }, 'json');
    }
};

var resendPOEmail = function(e, shipmentid) {
    e.stopPropagation();

    if (confirm('PO email for this shipment will be resent. Continue?')) {

        var url = `${cgiroot}shipment/${shipmentid}/send_purchase_order/`;
        var params = {
            // shipment_id: shipmentid,
        };
        $.post(url, params, function(data) {
            if (data.success) {
            }
        });
    }
};

function showShippingInfo(shipmentid) {
    $('#dialog_shipping_info').dialog("open");
    globals['shipmentid'] = shipmentid;
}

function shipShipment(shipmentid) {
    $('#dialog_ship_shipment').dialog("open");
    globals['shipmentid'] = shipmentid;
}

function deletePallet(palletid) {
    $('#dialog_delete_pallet').dialog("open");
    globals['palletid'] = palletid;
}

function execute_saveShipment() {
    var dateShipped = isNaN(new Date($('#id_date_shipped').val())) ? null : $('#id_date_shipped').val();
    var shipment = {
        fnc: 'updateshipment',
        shipmentid: globals['shipmentid'],
        carrier: $('#id_carrier').val(),
        shipper_address: $('#id_shipper_address').val(),
        pro_number: $('#id_pro_number').val(),
        purchase_order_number: $('#id_purchase_order_number').val(),
        third_party: $('#id_third_party').val(),
        shipment_class: $('#id_shipment_class').val(),
        pallet_count: $('#id_pallet_count').val(),
        date_shipped: dateShipped,
        shipper_instructions: $('#id_shipper_instructions').val(),
        consignee_instructions: $('#id_consignee_instructions').val(),
        inside_delivery: $('#id_inside_delivery').prop('checked'),
        liftgate_required: $('#id_liftgate_required').prop('checked'),
        appointment_required: $('#id_appointment_required').prop('checked'),
        sort_segregation: $('#id_sort_segregation').prop('checked'),
    }
console.log(shipment);
//    var url = cgiroot+'ajax_shipments_action.cfm';
    var url = cgiroot + 'shipment/' + globals['shipmentid'] + '/';
    $.post(url,shipment,function(data) {
console.log(data);
        $('#shipment_'+globals['shipmentid']).removeClass('selected');
        selectShipment(globals['shipmentid']);
    },'json');
}

function execute_shipShipment() {
    var shipment = {
        fnc: 'ship',
        shipmentid: globals['shipmentid'],
        delivery_charge: $('#delivery_charge').val(),
    }
console.log(shipment);
//    var url = cgiroot+'ajax_shipments_action.cfm';
    var url = cgiroot + 'shipment/' + globals['shipmentid'] + '/ship/';
    $.post(url,shipment,function(data) {
console.log(data);
        window.location.reload();
    },'json');
}

function execute_deletePallet() {
    var pallet = {
        fnc: 'delete',
        palletid: globals['palletid'],
    }
//    var url = cgiroot+'ajax_pallets_action.cfm';
    var url = cgiroot + 'pallet/' + globals['palletid'] + '/delete/';
    $.post(url,pallet,function(data) {
console.log(data);
        window.location.reload();
    },'json');
}

function showShipmentDocs(shipmentid) {
    globals['shipmentid'] = shipmentid;
//    var url = 'ajax_shipment_docs.cfm?shipmentid=' + shipmentid;
    var url = cgiroot + 'shipment/' + shipmentid + '/docs/';
    $('#documents_list').load(url, function() {
        $('#documents_list button').button({
            icons: {
                primary: "ui-icon-trash"
            },
            text: false
        });
        $('#dialog_documents').dialog('open');
    });
}

function refreshUI() {
    $('.editable .product input').keyup(function(e) {
        if (e.keyCode == 13) {
            saveProduct($(this).attr('productid'));
        }
    }).click(function() {
        $(this).select();
    });

    $('table.shipments tr.shipment td.clickable').click(function() {
        selectShipment($(this).attr('shipmentid'));
    });

    $('table.pallets tr.pallet td.clickable').click(function() {
        selectPallet($(this).attr('palletid'));
    });

    $('table.history tr.product td.clickable').click(function() {
        showProductHistory($(this).attr('productid'));
        $(this).find('input').blur();
    });

    $('button.show-shipment-docs').button({
        icons: {
            primary: "ui-icon-document"
        },
        text: true
    });
}

function validatePrice(input) {
    if (!input) return false;
    return /^(\d{1,3})?(,?\d{3})*(\.\d{2})?$/.test(input);
}

/*
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
*/

$(document).ready(function() {
    refreshUI();

    $('#dialog_ship_shipment').dialog({
        autoOpen: false,
        resizable: false,
        modal: true,
        position: { my: "top", at: "top+200", of: window },
        buttons: [
            {
                id: 'ship_button_ship',
                text: 'Ship',
                click: function() {
                    $( this ).dialog( "close" );
                    execute_shipShipment();
                }
            },
            {
                id: 'ship_button_cancel',
                text: 'Cancel',
                click: function() {
                    $( this ).dialog( "close" );
                }
            },
        ]
    });

    $('#dialog_delete_pallet').dialog({
        autoOpen: false,
        resizable: false,
        modal: true,
        position: { my: "top", at: "top+200", of: window },
        buttons: {
            Delete: function() {
                $( this ).dialog( "close" );
                execute_deletePallet();
            },
            Cancel: function() {
                $( this ).dialog( "close" );
            }
        }
    });

    $('#bol_upload_form').dialog({
        autoOpen: false,
        resizable: false,
        modal: true,
        width: 600,
        position: { my: "top", at: "top+200", of: window },
        buttons: {
            Cancel: function() {
                $( this ).dialog( "close" );
            }
        }
    });

    $('#dialog_documents').dialog({
        autoOpen: false,
        resizable: false,
        modal: true,
        width: 600,
        position: { my: "top", at: "top+200", of: window },
    });

    $('#delivery_charge_yes').button().click(function() {
        $(this).addClass('ui-state-active');
        $('#delivery_charge_no').removeClass('ui-state-active');
        $('.delivery_charge_input').css('visibility', 'visible');
        $('#ship_button_ship').button('disable');
    });
    $('#delivery_charge_no').button().click(function() {
        $(this).addClass('ui-state-active');
        $('#delivery_charge_yes').removeClass('ui-state-active');
        $('.delivery_charge_input').css('visibility', 'hidden');
        $('#ship_button_ship').button('enable');
    });
    $('#delivery_charge').keyup(function(e) {
        if (validatePrice($(this).val())) {
            $('#ship_button_ship').button('enable');
        } else {
            $('#ship_button_ship').button('disable');
        }
    });
    $('#ship_button_ship').button('disable');

});

