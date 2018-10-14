var cgiroot = '/client/';
var apiroot = '/api/';
var filter_popup_timeout = 2000;

function selectCustomer() {
    var params = {
        customerid: $('.client-picker').val(),
        fnc: 'selectCustomer',
    };
//    var url = cgiroot+'ajax_post.cfm';
    var url = cgiroot + 'select/' + $('.client-picker').val() + '/';
    $.post(url,params,function(data) {
console.log(data);
        if (data.success) {
            location.reload();
        } else {
            alert(data.message);
        }
    },'json');
}


function loadLocation(locationid) {
//    $('#contactform').hide();
    $('#locationform').show();
//    var url = cgiroot+'ajax_location_details.cfm?locationid='+locationid;
    var url = cgiroot + 'profile/location/' + locationid + '/';
    $('.items_list li').removeClass('selected');
    $('#locationform').load(url,function() {
        $('li#location_'+locationid).addClass('selected');
    });
}

function loadLocationsList(locationid) {
//    var url = cgiroot+'ajax_locations_list.cfm';
    var url = cgiroot + 'profile/locations/';
    $('#locations_list').load(url,function() {
        if (locationid) {
            loadLocation(locationid);
            var rowpos = $('li#location_'+locationid).position().top - $('#locations_list').position().top;
console.log(rowpos);
            $('#locations_list_wrap').animate({scrollTop: rowpos});
        }
    });
}

function showTab(tab) {
    globals['tab'] = tab;
    refreshInventory();
}

function refreshInventory() {
    if (!('tab' in globals)) { 
        globals['tab'] = 'request';
    }
//    var url = cgiroot+'ajax_inventory_list.cfm?&tab='+globals['tab'];
    var url = cgiroot + 'inventory/list/?tab=' + globals['tab'];
    if ('shipmentid' in globals) {
        url += '&shipmentid='+globals['shipmentid'];
    }
    $('#list_inventory').load(url,function(data) {
        var locations = [];
        var locations_seen = {};
        $('table.inventory td.location').each(function() {
            locations_seen[$(this).attr('location_id')] = $(this).html();
        });
        if (!l || l == '0') {
            l = 0;
            locations_seen[0] = '(No location)';
        }
        for (var l in locations_seen) {
            if (l)
                locations.push({location_id: l, location_name: locations_seen[l]});
        }
        locations.unshift({location_id: null, location_name: '(All locations)'});
        
        var tooltip = $('<ul>',{class: 'filter_tooltip_list'});
        for (var l in locations) {
            tooltip.append($('<li>',{
                html: locations[l].location_name,
                location_id: locations[l].location_id || '',
                click: function() {
                    if ($(this).attr('location_id') == '') {
                        $('tr.product').show();
                    } else {
                        $('tr.product').hide();
                        $('tr.product[location_id='+$(this).attr('location_id')+']').show();
                    }
//                    $('#location_filter').hide();  
                },
            }));
        }
        $('#location_filter').html(tooltip);
        $('#location_header').hover(function() {
            if ($('#location_filter').is(':hidden')) {
                $('#location_filter').show();
                setTimeout('hideLocationFilter()',filter_popup_timeout);
            }
        }); 
        $('#location_filter').mouseenter(function() {
            globals['location_filter_hovering'] = true;
        });
        $('#location_filter').mouseleave(function() {
            globals['location_filter_hovering'] = false;
        });

//        $('#location_filter').hover(function() { console.log('foo'); });

        refreshUI();
        updateTotalCases();
    });
}

function hideLocationFilter() {
    if (globals['location_filter_hovering'])
        setTimeout('hideLocationFilter()',filter_popup_timeout);
    else
        $('#location_filter').hide();
}  

function refreshUI() {
    var inputs = $('input.delivery_request').keyup(function(e) {
        updateTotalCases();
    }).keydown(function(e) {
        if (e.which == 38) {
            e.preventDefault();
            var prevInput = inputs.get(inputs.index(this) - 1);
            if (prevInput) {
                prevInput.focus();
            }
        } else if (e.which == 40) {
            e.preventDefault();
            var nextInput = inputs.get(inputs.index(this) + 1);
            if (nextInput) {
                nextInput.focus();
            }
        }
    });

    $('table.deliveries tr.delivery td.clickable').click(function() {
        selectDelivery($(this).attr('shipmentid'));
    });
    $(document).tooltip();

    $('button.show-shipment-docs').button({
        icons: {
            primary: "ui-icon-document"
        },
        text: true
    });
}

function selectProduct(productid,fromdate,todate) {
    fromdate = fromdate ? fromdate : '';
    todate = todate ? todate : '';
    $('tr.product').removeClass('selected');
    $('#product_'+productid).addClass('selected');
//    var url = cgiroot+'ajax_product_history.cfm?productid='+productid+'&fromdate='+fromdate+'&todate='+todate;
    var url = cgiroot + 'product/' + productid + '/history/?fromdate=' + fromdate + '&todate=' + todate;
console.log(url);
    $('#shipments_list').load(url,function() {
        $('#fromdate').datepicker({
            onSelect: function() {
                selectProduct(productid,this.value,$('#todate').val());
            }
        });
        $('#todate').datepicker({
            onSelect: function() {
                selectProduct(productid,$('#fromdate').val(),this.value);
            }
        });
        refreshUI();
    });
}

function selectDelivery(shipmentid) {
    $('tr.delivery').removeClass('selected');
console.log(shipmentid);
    $('#delivery_'+shipmentid).addClass('selected');
//    var url = cgiroot+'ajax_delivery_products.cfm?shipmentid='+shipmentid;
    var url = cgiroot + 'inventory/delivery/' + shipmentid + '/products/';
console.log(url);
    $('#delivery_list').load(url,function() {
        $('html, body').animate({ scrollTop: $(document).height() });
    });
}

function loadDelivery(shipmentid) {
    globals['shipmentid'] = shipmentid;
    globals['tab'] = 'request';
    refreshInventory();
}

function updateTotalCases() {
    var totalcases = 0;
    $('input.delivery_request').each(function() {
        var remain = parseInt($(this).attr('remain'));
        var inputVal = parseInt($(this).val());
        if ($(this).val()) {
            $(this).val(inputVal > remain ? remain : inputVal);
            totalcases += inputVal;
        }
    });
    $('#total_cases').html(totalcases);
}

function requestDelivery(locationid) {
    globals['locationid'] = locationid;
    var products = [];
    $('#request_details tbody ').empty();
    $('input.delivery_request').each(function() {
        if ($(this).val().indexOf('0') == 0) {
            $('.zero-inventory-warning').show();
        } else if ($(this).val() > 0) {
            var tr = $('<tr>');
            tr.append($('<td>',{
                html: $('#itemnum_'+$(this).attr('productid')).html()
            }));
            tr.append($('<td>',{
                html: $('#pname_'+$(this).attr('productid')).html()
            }));
            tr.append($('<td>',{
                html: $('#packing_'+$(this).attr('productid')).html(),
                class: 'numeric'
            }));
            tr.append($('<td>',{
                html: $(this).val(),
                class: 'numeric'
            }));
            $('#request_details tbody').append(tr);
            $('.zero-inventory-warning').hide();
        }
    });
    var tr = $('<tr>');
    tr.append($('<td>',{
        html: 'Location: '+$('#location_'+locationid).html(),
        colspan: 4
    }));
    $('#request_details').append(tr);
    $('#dialog_locations').dialog("close");
    $('#dialog_request_confirm').dialog('open');
}


function execute_requestDelivery() {
    var requestdelivery = {
        products: [],
        locationid: globals['locationid'],
        customerid: $('#customerid').val(),
        shipmentid: 'shipmentid' in globals ? globals['shipmentid'] : 0,
    };
console.log(requestdelivery);
//    var url = cgiroot+'ajax_request_delivery.cfm';
    var url = cgiroot + 'inventory/request_delivery/';
    $('input.delivery_request').each(function() {
        if ($(this).val()) {
            requestdelivery['products'].push({
                productid: $(this).attr('productid'),
                cases: parseInt($(this).val()),
            });
        }
    });
console.log(requestdelivery);
    var encoded = {json: JSON.stringify(requestdelivery)};
    $.post(url,encoded,function(data) {
console.log(data);
        $('#dialog_locations').dialog("close");
        if (data.success) {
            $('#dialog_request_result').dialog("open");
        } else {
            alert(data.message);
        }
//        location.reload();
    },'json');
}

function showLocations() {
    if (parseInt($('#total_cases').html()) > 0) {
        $('#dialog_locations').dialog("open");
    }
}

function showSupport() {
    $('#dialog_support').dialog("open");
}

function showChangePassword() {
    $('#dialog_change_password').dialog("open");
}

function confirmReorder() {
    $('#reorder_list tbody').html('');
    $('input[type=checkbox].reorder_product:checked').each(function() {
        var tr = $('<tr>');
        tr.append($('<td>',{ text: $('#pname_'+$(this).attr('productid')).html(), class: 'text pname_reorder' }));
        tr.append($('<td>',{ text: $('#contqty_'+$(this).attr('productid')).html(), class: 'numeric' }));
        tr.append($('<td>',{ text: $('#packing_'+$(this).attr('productid')).html(), class: 'numeric' }));
        tr.append($('<td>',{ text: $('#cases_'+$(this).attr('productid')).html(), class: 'numeric' }));
        tr.append($('<td>',{ text: $('#unitprice_'+$(this).attr('productid')).html(), class: 'numeric' }));
        tr.append($('<td>',{ text: $('#totalprice_'+$(this).attr('productid')).html(), class: 'numeric' }));
        tr.append($('<td>',{ text: $('#delivery_'+$(this).attr('productid')).html(), class: 'text' }));
        $('#reorder_list tbody').append(tr);
    });

    $("#dialog_reorder").nextAll(".ui-dialog-buttonpane").find("button:contains('Reorder')").attr("disabled", true).addClass("ui-state-disabled");
    $('#dialog_reorder').dialog("open");
}

function resultReorder() {
    $('#dialog_reorder_result').dialog("open");
}

function openSalesOrder() {
    var reorder = {
        products: []
    };
    $('input[type=checkbox].reorder_product:checked').each(function() {
        reorder['products'].push({
            productid: $(this).attr('productid')
        });
    });
    var url = cgiroot+'gen_sales_order.cfm?json='+JSON.stringify(reorder);
console.log(url);
    window.open(url);
}

function execute_reorder() {
    var reorder = {
        products: [],
        customerid: $('#customerid').val()
    };
    $('input[type=checkbox].reorder_product:checked').each(function() {
        reorder['products'].push({
            productid: $(this).attr('productid')
        });
    });
    var encoded = {json: JSON.stringify(reorder)};
console.log(encoded);
    var url = cgiroot+'ajax_reorder.cfm';
    $.post(url,encoded,function(data) {
console.log(data);
        resultReorder();
    },'json');
}

function generateReport(productid) {
    fromdate = $('#fromdate').val();
    todate = $('#todate').val();
    var url = cgiroot+'gen_report.cfm?productid='+productid+'&fromdate='+fromdate+'&todate='+todate;
    window.open(url);
}

function execute_changePassword() {
    var passwd = {
        fnc: 'changePassword',
        current_password: $('#current_password').val(),
        new_password_1: $('#new_password_1').val(),
        new_password_2: $('#new_password_2').val(),
    }
//    var url = cgiroot+'ajax_post.cfm';
    var url = cgiroot + 'change_password/';
    $.post(url,passwd,function(data) {
        if (data.success) {
            alert('Password changed successfully.');
        } else {
            alert(data.message);
        }
        $('#current_password').val('');
        $('#new_password_1').val('');
        $('#new_password_2').val('');
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


$(document).ready(function() {
    $('input.delivery_request').keyup(function(e) {
        updateTotalCases();
    });

    $('input#signature').keyup(function(e) {
        if ($('input#signature').val()) {
            $("#dialog_reorder").nextAll(".ui-dialog-buttonpane").find("button:contains('Reorder')").attr("disabled", false).removeClass("ui-state-disabled");
        } else {
            $("#dialog_reorder").nextAll(".ui-dialog-buttonpane").find("button:contains('Reorder')").attr("disabled", true).addClass("ui-state-disabled");
        }
    });

    $('input.reorder_product').click(function(e) {
        var btndisabled = true;
        $('input.reorder_product').each(function() {
            if ($(this).prop('checked')) {
                btndisabled = false;
            }
        });
        $('#btn_reorder').attr('disabled', btndisabled);
    });

    $('#history td.hoverinfo span').hide();
    $('#history tr').hover(function(e) {
        $(this).find('td.hoverinfo span').show();
    },function(e) {
        $(this).find('td.hoverinfo span').hide();
    });

    $('#dialog_support').dialog({
        autoOpen: false,
        resizable: false,
        modal: true,
        position: { my: "top", at: "top+200", of: window },
        buttons: {
            OK: function() {
                $( this ).dialog( "close" );
            }
        }
    });

    $('#dialog_change_password').dialog({
        autoOpen: false,
        resizable: false,
        modal: true,
        width: 500,
        position: { my: "top", at: "top+200", of: window },
        buttons: {
            Submit: function() {
                $( this ).dialog( "close" );
                execute_changePassword();
            },
            Cancel: function() {
                $( this ).dialog( "close" );
            }
        }
    });

    $('#dialog_locations').dialog({
        autoOpen: false,
        resizable: false,
        modal: true,
        position: { my: "top", at: "top+200", of: window },
        buttons: {
            Cancel: function() {
                $( this ).dialog( "close" );
            }
        }
    });

    $('#dialog_reorder').dialog({
        autoOpen: false,
        resizable: false,
        modal: true,
        width: 800,
        position: { my: "top", at: "top+200", of: window },
        buttons: {
            "Reorder": function() {
                execute_reorder();
                $( this ).dialog( "close" );
            },
            Cancel: function() {
                $( this ).dialog( "close" );
            }
        }
    });

    $('#dialog_reorder_result').dialog({
        autoOpen: false,
        resizable: false,
        modal: true,
        position: { my: "top", at: "top+200", of: window },
        buttons: {
            OK: function() {
                $( this ).dialog( "close" );
                window.location.reload();
            }
        }
    });

    $('#dialog_request_confirm').dialog({
        autoOpen: false,
        resizable: false,
        modal: true,
        width: 400,
        position: { my: "top", at: "top+200", of: window },
        buttons: {
            "Confirm": function() {
                execute_requestDelivery();
                $( this ).dialog( "close" );
            },
            Cancel: function() {
                $( this ).dialog( "close" );
            }
        }
    });

    $('#dialog_request_result').dialog({
        autoOpen: false,
        resizable: false,
        modal: true,
        position: { my: "top", at: "top+200", of: window },
        buttons: {
            OK: function() {
                $( this ).dialog( "close" );
                window.location.reload();
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

    $('.client-picker').change(function() {
        selectCustomer();
    });

    refreshInventory();
    loadLocationsList();

});
