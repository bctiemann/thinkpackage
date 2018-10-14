var cgiroot = '/accounting/';

function showStatus(show_status) {
    globals['status_filter'] = show_status;
    $('#shipment_details').html('');
    refreshShipments();
}

function showCompleted(show_completed) {
    globals['completed_filter'] = show_completed ? 1 : 0;
    refreshReconciliation();
}

function refreshShipments(shipmentid) {
    if (!('status_filter' in globals)) {
        globals['status_filter'] = 0;
    }
//    var url = cgiroot+'ajax_shipments_list.cfm?status_filter='+globals['status_filter'];
    var url = cgiroot + 'shipments/list/?status_filter=' + globals['status_filter'];
    $('#list_shipments').load(url,function(data) {
        refreshUI();
        if (shipmentid && parseInt(globals['status_filter']) == 0) {
            selectShipment(shipmentid);
            var rowpos = $('tr#shipment_' + shipmentid).position().top - $('table.shipments tbody').position().top;
            $('table.shipments tbody').animate({ scrollTop: rowpos});
        }
    });
}

function refreshReconciliation() {
    if (!('completed_filter' in globals)) {
        globals['completed_filter'] = 0;
    }
//    var url = cgiroot+'ajax_reconciliation_list.cfm?completed_filter='+globals['completed_filter'];
    var url = cgiroot + 'reconciliation/list/?completed_filter=' + globals['completed_filter'];
    $('#list_reconciliation').load(url,function(data) {
        refreshUI();
    });
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

            $('#shipdate').datepicker();

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
        var url = cgiroot+'ajax_pallet_details.cfm?palletid='+palletid;
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

function promptInvoice(shipmentid) {
    globals['shipmentid'] = shipmentid; 
    $('#shipment_invoice').val('');
    $('#dialog_invoice').dialog("open");
}

var execute_saveInvoice = function() {
    var shipment = {
//        fnc: 'saveInvoice',
//        shipment: globals['shipmentid'],
        invoice_number: $('#shipment_invoice').val(),
        accounting_status: 1,
    }
//    var url = cgiroot+'ajax_shipments_action.cfm';
    var url = cgiroot + 'shipment/' + globals['shipmentid'] + '/';
    $.post(url,shipment,function(data) {
console.log(data);
        if (data.success) {
            showStatus(0);
            $('#dialog_invoice').dialog("close");
//            window.location.reload();
        } else {
            displayErrorDialog(data);
        }
    },'json');
};

function submitInvoice(shipmentid) {
    if (confirm('Submit this invoice?')) {
        var shipment = {
//            fnc: 'submitInvoice',
//            shipmentid: shipmentid,
            accounting_status: 2,
        };
//        var url = cgiroot+'ajax_shipments_action.cfm';
        var url = cgiroot + 'shipment/' + shipmentid + '/submit/';
        $.post(url,shipment,function(data) {
console.log(data);
            if (data.success) {
                showStatus(1);
            } else {
                displayErrorDialog(data);
            }
        },'json');
    }
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
                alert(data.message);
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
    var shipment = {
        fnc: 'updateshipment',
        shipmentid: globals['shipmentid'],
        carrier: $('#carrier').val(),
        shipperaddress: $('#shipperaddress').val(),
        pro: $('#pro').val(),
        loadnum: $('#loadnum').val(),
//        tracking: $('#tracking').val(),
        thirdparty: $('#3rdparty').val(),
//        thirdpartyaddress: $('#3rdpartyaddress').val(),
//        thirdpartyphone: $('#3rdpartyphone').val(),
//        thirdpartyper: $('#3rdpartyper').val(),
//        thirdpartyrecvd: $('#3rdpartyrecvd').val(),
//        thirdpartychgadvanced: $('#3rdpartychgadvanced').val(),
        class: $('#class').val(),
        numpallets: $('#numpallets').val(),
        shipdate: $('#shipdate').val() ? new Date($('#shipdate').val()) : null,
        shipperinstructions: $('#shipperinstructions').val(),
        consigneeinstructions: $('#consigneeinstructions').val(),
        insidedelivery: $('#insidedelivery').prop('checked') || 0,
        liftgate: $('#liftgate').prop('checked') || 0,
        appointment: $('#appointment').prop('checked') || 0,
        sortseg: $('#sortseg').prop('checked') || 0,
    }
console.log(shipment);
    var url = cgiroot+'ajax_shipments_action.cfm';
    $.post(url,shipment,function(data) {
        $('#shipment_'+globals['shipmentid']).removeClass('selected');
        selectShipment(globals['shipmentid']);
console.log(data);
    },'json');
}

function execute_shipShipment() {
    var shipment = {
        fnc: 'ship',
        shipmentid: globals['shipmentid']
    }
console.log(shipment);
    var url = cgiroot+'ajax_shipments_action.cfm';
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
    var url = cgiroot+'ajax_pallets_action.cfm';
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

function completeReconciliation(returnid) {
    if (confirm('Are you sure you want to complete this reconciliation item?')) {
//        var url = 'ajax_reconciliation_action.cfm';
        var url = cgiroot + 'reconciliation/' + returnid + '/';
        var params = {
//            fnc: 'reconcile_return',
//            returnid: returnid,
        };
        $.post(url, params, function(data) {
console.log(data);
            refreshReconciliation();
        }, 'json');
    }
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

$(document).ready(function() {
    refreshUI();
    refreshShipments();
    refreshReconciliation();

    $('#dialog_ship_shipment').dialog({
        autoOpen: false,
        resizable: false,
        modal: true,
        position: { my: "top", at: "top+200", of: window },
        buttons: {
            Ship: function() {
                $( this ).dialog( "close" );
                execute_shipShipment();
            },
            Cancel: function() {
                $( this ).dialog( "close" );
            }
        }
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

    $('#dialog_invoice').dialog({
        autoOpen: false,
        resizable: false,
        modal: true,
        width: 600,
        position: { my: "top", at: "top+200", of: window },
        buttons: {
            Submit: function() {
                execute_saveInvoice();
            },
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

});

