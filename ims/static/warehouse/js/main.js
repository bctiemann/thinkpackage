var cgiroot = '/warehouse/';
var globals = {};

function nop() {}

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
//    var url = cgiroot+'ajax_shipments_list.cfm?shipped_filter='+globals['shipped_filter'];
    var url = cgiroot + 'shipments/list/?shipped_filter=' + globals['shipped_filter'];
    $('#list_shipments').load(url,function(data) {
        refreshUI();
        if (shipmentid) {
            selectShipment(shipmentid);
            var rowpos = $('tr#shipment_' + shipmentid).position().top - $('table.shipments tbody').position().top;
            $('table.shipments tbody').animate({ scrollTop: rowpos});
        }
    });
}

function refreshReceivables() {
    if (!('received_filter' in globals)) {
        globals['received_filter'] = 1;
    }
    var url = cgiroot+'ajax_receivables_list.cfm?received_filter='+globals['received_filter'];
    $('#list_receivables').load(url,function(data) {
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
        var url = cgiroot+'ajax_shipment_details.cfm?shipmentid='+shipmentid;
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

function uploadShipmentDoc(shipmentid) {
    globals['shipmentid'] = shipmentid; 
    $('#shipment_upfile').val('');
    $('#shipment_upload_form').dialog("open");
}
                
var execute_uploadShipmentDoc = function(shipmentid) {
    var data = new FormData();
    $.each($('#shipment_upfile')[0].files, function(i, file) {
        data.append('shipment_upfile', file);
    });
    data.append('fnc', 'upload_doc');
    data.append('shipmentid', globals['shipmentid']);
          
    $('.spinner-upload').show();
  
    $.ajax({
        url: 'ajax_shipment_action.cfm', 
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
                $('#shipment_'+globals['shipmentid']).removeClass('selected');
                var successUrl = cgiroot+'ajax_shipment_details.cfm?shipmentid='+data.shipmentid;
                $('#shipment_details').load(successUrl,function() {
                    refreshUI();
                });
                refreshShipments(globals['shipmentid']);
                showShipmentDocs(data.shipmentid);
                $('#shipment_upfile').val('');
            } else {
                alert(data.error);
            }
        },
    }); 
};

var deleteShipmentDoc = function(docid) {
    if (confirm('Are you sure you want to delete this document?')) {
        var url = 'ajax_shipment_action.cfm';
        var params = {
            docid: docid,
            fnc: 'delete_doc',
        };
        $.post(url, params, function(data) {
console.log(data);
            if (data.success) {
                $('#shipment_'+globals['shipmentid']).removeClass('selected');
                var successUrl = cgiroot+'ajax_shipment_details.cfm?shipmentid='+data.shipmentid;
                $('#shipment_details').load(successUrl,function() {
                    refreshUI();
                });
                refreshShipments(globals['shipmentid']);
                showShipmentDocs(data.shipmentid);
                $('#shipment_upfile').val('');
            } else {
                alert(data.error);
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
    var url = 'ajax_shipment_docs.cfm?shipmentid=' + shipmentid;
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
console.log($(this).attr('shipmentid'));
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

    $('#dialog_documents').dialog({
        autoOpen: false,
        resizable: false,
        modal: true,
        width: 600,
        position: { my: "top", at: "top+200", of: window },
    });

});

