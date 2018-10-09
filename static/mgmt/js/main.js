var cgiroot = '/mgmt/';
var apiroot = '/api/';
var globals = {};
var keyinput = '';
var keyinput_timeout = null;
var filter_popup_timeout = 2000;
var units = 'metric';


$(document).ajaxError(function() {
    alert('An error occurred executing this function.');
  $( ".log" ).text( "Triggered ajaxError handler." );
});

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
    return (/^(GET|HEAD|OPTIONS|TRACE)$/.test(method));
}
$.ajaxSetup({
    beforeSend: function(xhr, settings) {
        if (!csrfSafeMethod(settings.type) && !this.crossDomain) {
            xhr.setRequestHeader("X-CSRFToken", csrftoken);
        }
    }
});

var SchedElements = new Array();
function updateCalendar(dir,ldate) {
  var querystr = '';
  for (i in SchedElements) {
    querystr += i+"="+SchedElements[i]+"&";
  }
  if (dir && ldate && dir!=0 && ldate!=0) {
    querystr += "MonthChange="+dir+"&LastDate="+ldate;
  }
  var url = "inc_calendar.cfm?"+querystr;
  $('#livecalendar').load(url);
//  ajaxReplace(url,document.getElementById('livecalendar'));
}
function toggleSchedElement(element,dir,ldate) {
  if (SchedElements[element]) {
    delete SchedElements[element];
  } else {
    SchedElements[element]=true;
  }
  updateCalendar(dir,ldate);
}
var BillingInfoShown = false;
function toggleBillingInfo() {
  var source = document.getElementById('billinginfo_hidden');
  var target = document.getElementById('billinginfo');
  if (BillingInfoShown == true) {
    target.innerHTML = "";
    BillingInfoShown = false;
  } else {
    target.innerHTML = source.innerHTML;
    BillingInfoShown = true;
  }
}
function showHistory(customerid) {
  var url = "inc_history.cfm?customerid="+customerid;
  $('#history').load(url);
//  ajaxReplace(url,document.getElementById('history'));
}

function nop() {}

function deleteDis(i) {
	var answer = confirm("Delete discount code?")
	if (answer){
		window.location = "discounts.cfm?deletediscount="+ i;
	}
}


function checkType() {
	var objAdmin = document.getElementById('admin');
	var objSend = document.getElementById('send');
	var objAid = document.getElementById('aid');
	var	tmin = objAdmin.value;

$.getJSON('cfc/2fac.cfc', {
	method: 'checkType',
	returnformat: 'json',
	adm: tmin },

	function(adata) {

	if (adata.F == 1 && adata.TF == 2) {
	objSend.style.visibility="visible";
        $('#send_btn').css('visibility','visible');
	objAid.value = adata.AID;
	} else {
	objSend.style.visibility="hidden";
	objAid.value = 0;
	}

	});


}

function doSend() {
	var objAid = document.getElementById('aid');
	var aid = objAid.value;
$.get("tkt.cfm", { aid: +aid} );

}


function carChange() {
	var objCar = document.getElementById('carid');
	var selValue = objCar.options[objCar.selectedIndex].value;
	var objMilesout = document.getElementById('milesout');
	var objMilesback = document.getElementById('milesback');
	var objMilesinc = document.getElementById('milesinc');
	var objDepamount = document.getElementById('depamount');
	var objDamageout = document.getElementById('damageout');
	var objwheelDF = document.getElementById('wheelDF');
	var objwheelPF = document.getElementById('wheelPF');
	var objwheelDR = document.getElementById('wheelDR');
	var objwheelPR = document.getElementById('wheelPR');
	var objnoselip = document.getElementById('noselip');
	var objrearbump = document.getElementById('rearbump');

$.getJSON('cfc/miles.cfc', {
	method: 'getMiles',
	returnformat: 'json',
	carid: selValue },
//	ShowMiles
	function(data) {

		objMilesout.value = data.MILEAGE;
		objMilesback.value = data.MILEAGE;
		objMilesinc.value = data.MILESINC;
		objDepamount.value = data.DEPOSIT +".00";
		objDamageout.value = data.DAMAGE;

		for (var i = 0; i < objwheelDF.length; i++) {
			if (objwheelDF.options[i].value == data.WHEELDF) {
				objwheelDF.options[i].selected=true
			}
		}
		for (var i = 0; i < objwheelPF.length; i++) {
			if (objwheelPF.options[i].value == data.WHEELPF) {
				objwheelPF.options[i].selected=true
			}
		}
		for (var i = 0; i < objwheelDR.length; i++) {
			if (objwheelDR.options[i].value == data.WHEELDR) {
				objwheelDR.options[i].selected=true
			}
		}
		for (var i = 0; i < objwheelPR.length; i++) {
			if (objwheelPR.options[i].value == data.WHEELPR) {
				objwheelPR.options[i].selected=true
			}
		}
		for (var i = 0; i < objnoselip.length; i++) {
			if (objnoselip.options[i].value == data.NOSELIP) {
				objnoselip.options[i].selected=true
			}
		}
		for (var i = 0; i < objrearbump.length; i++) {
			if (objrearbump.options[i].value == data.REARBUMP) {
				objrearbump.options[i].selected=true
			}
		}


	});

}


function refreshCustomers(filter) {
//    var url = cgiroot+'ajax_customers_list.cfm?filter='+filter;
    var url = cgiroot + 'customers_list/?filter=' + filter;
    $('#customers_list_wrap').load(url,function() {
    });
}

function toggleInactiveCustomers() {
    globals['showinactive'] = globals['showinactive'] ? 0 : 1;
    refreshCustomers();
}

function loadLocationsList(customerid,locationid) {
//    var url = cgiroot+'ajax_locations_list.cfm?customerid='+customerid;
    var url = cgiroot + 'locations_list/' + customerid;
    $('#locations_list').load(url,function() {
        if (locationid) {
            loadLocation(locationid,customerid);
            var rowpos = $('li#location_'+locationid).position().top - $('#locations_list').position().top;
console.log(rowpos);
            $('#locations_list_wrap').animate({scrollTop: rowpos});
        }
    });
}

function loadContactsList(customerid,custcontactid) {
//    var url = cgiroot+'ajax_contacts_list.cfm?customerid='+customerid;
    var url = cgiroot + 'contacts_list/' + customerid;
    $('#contacts_list').load(url,function() {
        if (custcontactid) {
            loadCustContact(custcontactid,customerid);
            var rowpos = $('li#custcontact_'+custcontactid).position().top - $('#contacts_list').position().top;
            $('#contacts_list_wrap').animate({scrollTop: rowpos});
        }
    });
}

function loadCustomer(refresh_list) {
    $('#contactform').hide();
    $('#locationform').hide();
    $('#customerform').show();
}

function loadLocation(locationid,customerid,refresh_list) {
    $('#contactform').hide();
    $('#locationform').show();
    $('#customerform').hide();
//    var url = cgiroot+'ajax_location_form.cfm?customerid='+customerid+'&locationid='+locationid;
//    var url = cgiroot + 'location_form/?client_id=' + customerid + '&location_id=' + locationid;
    var url;
    if (locationid) {
        url = cgiroot + 'location/' + locationid;
    } else {
        url = cgiroot + 'location/add/' + customerid;
    }
    $('.items_list li').removeClass('selected');
    $('#locationform').load(url, function() {
        $('li#location_'+locationid).addClass('selected');
        if (refresh_list) {
//            loadLocationsList(customerid,locationid);
            loadLocationsList(customerid,null);
        }
    });
}

function loadCustContact(custcontactid,customerid,refresh_list) {
    $('#contactform').show();
    $('#locationform').hide();
    $('#customerform').hide();
//    var url = cgiroot+'ajax_contact_form.cfm?customerid='+customerid+'&custcontactid='+custcontactid;
//    var url = cgiroot + 'contact_form/?client_id=' + customerid + '&custcontact_id=' + custcontactid;
    var url;
    if (custcontactid) {
        url = cgiroot + 'contact/' + custcontactid;
    } else {
        url = cgiroot + 'contact/add/' + customerid;
    }
    $('.items_list li').removeClass('selected');
    $('#contactform').load(url,function() {
        $('li#custcontact_'+custcontactid).addClass('selected');
        if (refresh_list) {
//            loadContactsList(customerid,custcontactid);
            loadContactsList(customerid,null);
        }
    });
}

function updateLocation(customerid, locationid) {
    var location = {
        client:           customerid,
        customer_contact: $('#customer_contact').val() || 0,
        name:             $('#id_name').val(),
        address:          $('#address').val(),
        address_2:        $('#address_2').val(),
        city:             $('#city').val(),
        state:            $('#id_state').val(),
        zip:              $('#id_zip').val(),
        receiving_hours:  $('#receiving_hours').val(),
        notes:            $('#notes').val(),
    };
console.log(location);
    var url = cgiroot + 'location/';
    if (locationid) {
        url += locationid + '/';
    } else {
        url += 'add/' + customerid + '/';
    }
    $.post(url,location,function(data) {
console.log(data);
        $('.error').removeClass('error');
        if (data.success) {
            loadLocation(data.pk, customerid, true);
            $('#locationform').hide();
        } else {
            for (var field in data) {
                var error = data[field][0];
                $('#id_' + field).addClass('error').attr('error-text', error.message);
                console.log(field);
            }
        }
    },'json');
}

function updateCustContact(custcontactid) {
    var customerid = $('#id_client').val();
    var custcontact = {
        client:           customerid,
        custcontact:      custcontactid,
        first_name:       $('#id_first_name').val(),
        last_name:        $('#id_last_name').val(),
        title:            $('#id_title').val(),
        email:            $('#id_email').val(),
        password:         $('#id_password').val(),
        phone_number:     $('#id_phone_number').val(),
        phone_extension:  $('#id_phone_extension').val(),
        mobile_number:    $('#id_mobile_number').val(),
        fax_number:       $('#id_fax_number').val(),
        notes:            $('#id_contact_notes').val()
    };
console.log(custcontact);
    var url = cgiroot + 'contact/';
    if (custcontactid) {
        url += custcontactid + '/';
    } else {
        url += 'add/' + customerid + '/';
    }
    $.post(url,custcontact,function(data) {
console.log(data);
        $('.error').removeClass('error');
        if (data.success) {
            if ($('#isprimary').val() == 1) {
                $('#email_primary').html(custcontact.email);
                $('#tel_primary').html(custcontact.tel+' '+custcontact.telext);
            }
            loadCustContact(data.pk,customerid,true);
            $('#contactform').hide();
        } else {
            for (var field in data) {
                var error = data[field][0];
                $('#id_' + field).addClass('error').attr('error-text', error.message);
                console.log(field);
            }
        }
    },'json');
}

function deleteLocation(customerid,locationid) {
    $('#location_delete_confirm').dialog("open");
    globals['customerid'] = customerid;
    globals['locationid'] = locationid;
}

function execute_deleteLocation() {
    var location = {
        is_active: false,
    };
    var url = cgiroot + 'location/' + globals['locationid'] + '/delete/';
    $.post(url, location, function(data) {
        window.location = cgiroot + '/' + globals['customerid'] + '/profile';
    },'json');
}

function deleteCustContact(customerid,custcontactid) {
    $('#custcontact_delete_confirm').dialog("open");
    globals['customerid'] = customerid;
    globals['custcontactid'] = custcontactid;
}

function execute_deleteCustContact() {
    var custcontact = {
        is_active: false,
    };
    var url = cgiroot + 'contact/' + globals['custcontactid'] + '/delete/';
    $.post(url,custcontact,function(data) {
//        loadCustContact(null,globals['customerid'],true);
        window.location = cgiroot + '/' + globals['customerid'] + '/profile';
    },'json');
}

function updateClient(customerid) {
    var customer = {
        company_name:      $('#id_company_name').val(),
        primary_contact:   $('#id_primary_contact').val(),
        is_active:         $('#id_is_active').val(),
        has_warehousing:   $('#id_has_warehousing').val(),
        parent:            $('#id_parent').val(),
        notes:             $('#id_client_notes').val()
    }
console.log(customer);
    var url = cgiroot + customerid + '/profile/';
    $.post(url,customer,function(data) {
console.log(data);
//        window.location = 'profile.cfm?customerid='+customerid;
        window.location = url;
    },'json');
}

function selectProduct(productid,load_details,elem) {
    if (!$('#product_'+productid).hasClass('selected')) {
        $('.product_detail').html('');
        $('tr.product').removeClass('selected_history');
        $('tr.product').removeClass('selected');
        $('.action').removeClass('selected');
        $('#product_'+productid).addClass('selected');

        if (elem) {
//            elem.children('input').focus();
//            elem.children('input').select();
            elem.parent().children().children('input').each(function() {
                $(this).val($(this).val().replace(/,/g,''));
            });
        }

        if (load_details != false) {
            var url = cgiroot + 'product/' + productid;
            $('.switch-units.weight').html(units == 'metric' ? 'kg' : 'lb');
            $('.switch-units.length').html(units == 'metric' ? 'cm' : 'in');
            $('#product_details').load(url,function() {
                $('.switch-units').click(function() {
                    units = units == 'metric' ? 'imperial' : 'metric';
                    $('#id_length').val($('#length_' + units).val());
                    $('#id_width').val($('#width_' + units).val());
                    $('#id_height').val($('#height_' + units).val());
                    $('#id_gross_weight').val($('#gross_weight_' + units).val());
                    $('.switch-units.weight').html(units == 'metric' ? 'kg' : 'lb');
                    $('.switch-units.length').html(units == 'metric' ? 'cm' : 'in');
                });
            });
        }
    }
}

function saveProduct(productid) {
    var product = {
        client:               $('#customerid').val(),
        item_number:          $('#itemnum_'+productid).val(),
        location:             $('#location_'+productid).val() || null,
        client_product_id:    $('#ctag_'+productid).val(),
        name:                 $('#pname_'+productid).val(),
        packing:              Math.floor($('#packing_'+productid).val()),
        cases_inventory:      Math.floor($('#remain_'+productid).val()),
        PO:                   $('#PO_'+productid).val() ? $('#PO_'+productid).val() : null,
        contracted_quantity:  $('#id_contracted_quantity').length ? Math.floor($('#id_contracted_quantity').val()) : null,
        unit_price:           $('#id_unit_price').val() ? $('#id_unit_price').val() : null,
        gross_weight:         isNaN(parseFloat($('#id_gross_weight').val())) ? 0 : parseFloat($('#id_gross_weight').val()),
        length:               isNaN(parseFloat($('#id_length').val())) ? 0 : parseFloat($('#id_length').val()),
        width:                isNaN(parseFloat($('#id_width').val())) ? 0 : parseFloat($('#id_width').val()),
        height:               isNaN(parseFloat($('#id_height').val())) ? 0 : parseFloat($('#id_height').val()),
        is_domestic:          $('#id_is_domestic').val(),
        account_prepay_type:  $('#id_account_prepay_type').val(),
    };
console.log($('#id_contracted_quantity'));
    if (units == 'imperial') {
        product.gross_weight *= 0.453592;
        product.length *= 2.54;
        product.height *= 2.54;
        product.width *= 2.54;
    }
console.log(product);
    var url = cgiroot + 'product/';
    if (productid == 'new') {
        url += 'add/' + $('#customerid').val() + '/';
    } else {
        url += productid + '/';
    }
console.log(url);
    $.post(url,product,function(data) {
console.log(data);
        if (data.success) {
            globals['productid'] = null;
            refreshInventory();
            selectProduct(null,false);
            $('#dialog_saveproduct_result').dialog("open");
        } else {
            alert(data.message);
        }
    },'json');
}

function deleteProduct(productid, permanent) {
    globals['productid'] = productid;
    if (permanent) {
        $('#product_permdelete_confirm').dialog('open');
    } else {
        $('#product_delete_confirm').dialog('open');
    }
}

function undeleteProduct(productid) {
    globals['productid'] = productid;
    $('#product_undelete_confirm').dialog('open');
}

function selectShipment(shipmentid) {
    if (!$('#shipment_'+shipmentid).hasClass('selected')) {
        $('.shipment_detail').html('');
        $('tr.shipment').removeClass('selected');
        $('#shipment_'+shipmentid).addClass('selected');
//        var url = cgiroot+'ajax_shipment_details.cfm?shipmentid='+shipmentid;
        var url = cgiroot + 'shipment/' + shipmentid + '/';
        $('#shipment_details').load(url,function() {
            refreshUI();
        });
    }
}

function cancelShipment(shipmentid) {
    globals['shipmentid'] = shipmentid;
    $('#shipment_cancel_confirm').dialog('open');
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
            doc_id: docid,
            fnc: 'delete_doc',
        };
        $.post(url, params, function(data) {
console.log(data)
            if (data.success) {
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

function execute_addCustomer() {
    var url = cgiroot+'ajax_coname_action.cfm';
    var customer = {
        fnc: 'add',
        coname: $('#customer_name_new').val()
    };
    $.post(url,customer,function(data) {
console.log(data);
        if (data.STATUS == 'success') {
            var url_cust = cgiroot+'ajax_customers_list.cfm';
            $('#customers_list_wrap').load(url_cust,function() {
                var rowpos = $('li#customer_'+data.CUSTOMERID).position().top - $('#customers_list').position().top;
//console.log(rowpos);
                $('#customers_list_wrap').animate({scrollTop: rowpos});
            });
        } else {
            alert(data.MESSAGE);
        }
        resetAddCustomerButton();
    },'json');
}

function execute_deleteProduct(active, permanent) {
    var product = {
        fnc: 'delete',
        productid: globals['productid'],
        active: active,
        is_active: active > 0,
        permanent: permanent,
        is_deleted: permanent,
    }
console.log(product);
//    var url = cgiroot+'ajax_product_action.cfm';
    var url = cgiroot + 'product/' + globals['productid'] + '/delete/';
    $.post(url,product,function(data) {
        globals['productid'] = null;
        globals['history'] = null;
        refreshInventory();
        $('#product_details').html('');
        $('#product_history').html('');
    },'json');
}

function execute_cancelShipment() {
    var shipment = {fnc: 'cancel', shipmentid: globals['shipmentid']}
    var url = cgiroot+'ajax_shipments_action.cfm';
    $.post(url,shipment,function(data) {
console.log(data);
        var url_ship = cgiroot+'ajax_shipments_list.cfm?customerid='+$('#customerid').val();
        $('#list_shipments').load(url_ship,function(data) {
            refreshUI();
        });
    },'json');
}

function incomingProduct(productid) {
    $('.product_detail').html('');
//    var url = cgiroot+'ajax_product_incoming.cfm?productid='+productid;
    var url = cgiroot + 'receivable/add/' + productid;
    $('#product_incoming').load(url,function() {
        $('tr.product').removeClass('selected');
        $('tr.product').removeClass('selected_history');
        $('#product_'+productid).addClass('selected_history');
        $('.action').removeClass('selected');
        $('#action_incoming_'+productid).addClass('selected');
//        $('#productdetail_'+productid+' input').prop('disabled',false);
        $('#id_date_received').datepicker();
    });
}

function addReceivable(productid) {
    var receivable = {
        fnc:            'addincoming',
        product:        productid,
        client:         $('#customerid').val(),
        purchase_order: $('#id_purchase_order_incoming').val(),
        shipment_order: $('#id_shipment_order_incoming').val(),
        cases:        Math.floor($('#id_cases_incoming').val()),
//        date_received:  new Date($('#id_date_received').val())
        date_received:  $('#id_date_received').val(),
    }
console.log(receivable);
    if ($('#id_date_received').val()) {
//        var url = cgiroot+'ajax_product_action.cfm';
        var url = cgiroot + 'receivable/add/' + productid + '/';
        $.post(url,receivable,function(data) {
console.log(data);
            refreshInventory();
            showProductHistory(productid);
//            $('#dialog_addreceivable_result').dialog("open");
        },'json');
    } else {
        alert('Please select the expected arrival date.');
    }
}

function showProductHistory(productid,fromdate,todate) {
console.log(fromdate);
console.log(todate);
    fromdate = fromdate ? fromdate : '';
    todate = todate ? todate : '';
    $('.product_detail').html('');
//    var url = cgiroot+'ajax_product_history.cfm?productid='+productid+'&fromdate='+fromdate+'&todate='+todate;
    var url = cgiroot + 'product/' + productid + '/history/?fromdate=' + fromdate + '&todate=' + todate;
    $('#product_history').load(url,function() {
        $('tr.product').removeClass('selected');
        $('tr.product').removeClass('selected_history');

        $('#product_'+productid).addClass('selected_history');
        $('.action').removeClass('selected');
        $('#action_history_'+productid).addClass('selected');

//        $('#productdetail_'+productid+' input').prop('disabled',false);
        $('#fromdate').datepicker({
            onSelect: function() {
                showProductHistory(productid,this.value,$('#todate').val());
            }
        });
        $('#todate').datepicker({
            onSelect: function() {
                showProductHistory(productid,$('#fromdate').val(),this.value);
            }
        });
        refreshUI();
    });
}

function saveTransaction(receivableid,productid) {
    globals['receivableid'] = receivableid;
    globals['productid'] = productid;
    $('#incoming_save_confirm').dialog('open');
}

function execute_saveTransaction() {
    var transaction = {
        fnc:              'update',
        receivableid:     globals['receivableid'],
        productid:        globals['productid'],
        cases:            Math.floor($('#cases_'+globals['receivableid']).val()),
        shipment_order:   $('#SO_'+globals['productid']).val(),
        purchase_order:   $('#PO_'+globals['productid']).val(),
    }

console.log(transaction);
//    var url = cgiroot+'ajax_transaction_action.cfm';
    var url = cgiroot + 'receivable/' + globals['receivableid'] + '/confirm/';
    $.post(url,transaction,function(data) {
console.log(data);
        if (data.success) {
            if (data.warning) {
                $('#cases_mismatch_warning').show();
            } else {
                $('#cases_mismatch_warning').hide();
            }
            $('#dialog_confirmreceivable_result').dialog("open");
//            showProductHistory(globals['productid']);
        } else {
            alert(data.message);
        }
    },'json');
}

function cancelIncoming(receivableid,productid) {
    globals['receivableid'] = receivableid;
    globals['productid'] = productid;
    $('#incoming_cancel_confirm').dialog('open');
}

function execute_cancelIncoming() {
    var transaction = {
        fnc:              'delete',
        transactionid:    globals['transactionid']
    }
//    var url = cgiroot+'ajax_transaction_action.cfm';
    var url = cgiroot + 'receivable/' + globals['receivableid'] + '/delete/';
    $.post(url,transaction,function(data) {
console.log(data);
        refreshInventory();
        showProductHistory(globals['productid']);
        globals['productid'] = null;
    });
}

function refreshUI() {
    $('.editable .product input').keyup(function(e) {
        if (e.keyCode == 13) {
            saveProduct($(this).attr('productid'));
        }
    }).click(function() {
//        $(this).select();
    });

    $('table.inventory tr.product td.clickable').click(function() {
        selectProduct($(this).attr('productid'),true,$(this));
    });

    $('table.shipments tr.shipment td.clickable').click(function() {
        selectShipment($(this).attr('shipmentid'));
    });

    $('table.history tr.product td.clickable').click(function() {
        showProductHistory($(this).attr('productid'));
        $(this).find('input').blur();
    });

    // Customers list filter
    $('#customer_list_warehousing_yes').click(function() {
        refreshCustomers($(this).hasClass('selected') ? null : 'warehousing');
        $(this).toggleClass('selected');
        $('.customers_filter li').not('#customer_list_warehousing_yes').removeClass('selected');
    });
    $('#customer_list_warehousing_no').click(function() {
        refreshCustomers($(this).hasClass('selected') ? null : 'no-warehousing');
        $(this).toggleClass('selected');
        $('.customers_filter li').not('#customer_list_warehousing_no').removeClass('selected');
    });
    $('#customer_list_inactive').click(function() {
        refreshCustomers($(this).hasClass('selected') ? null : 'inactive');
        $(this).toggleClass('selected');
        $('.customers_filter li').not('#customer_list_inactive').removeClass('selected');
    });
    $('*').tooltip();
    $('button').tooltip('disable');

    $('button.show-shipment-docs').button({
        icons: {
            primary: "ui-icon-document"
        },
        text: true
    });
}

function showInactive(show_inactive) {
    globals['active_filter'] = show_inactive ? 0 : 1;
    globals['productid'] = null;
    $('.product_detail').html('');
    refreshInventory();
}

function showShipped(show_shipped) {
    globals['shipped_filter'] = show_shipped ? 0 : 1;
    $('.shipment_detail').html('');
    refreshShipments();
}

function refreshInventory() {
console.log('refreshInventory');
    if (!('active_filter' in globals)) {
        globals['active_filter'] = 1;
    }

    $('#list_inventory tbody').empty().append($('<img>', {
        src: '/static/images/loading_bar.gif',
        class: 'loading',
    }));

//    var url = cgiroot+'ajax_inventory_list.cfm?customerid='+$('#customerid').val()+'&active_filter='+globals['active_filter'];
    var url = cgiroot + $('#customerid').val() + '/inventory/list/?active_filter=' + globals['active_filter'];
console.log(url);
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

        refreshUI();

        if (globals['history']) {
            selectProduct(globals['history'],false,null);
            showProductHistory(globals['history']);
            var rowpos = $('tr#product_' + globals['history']).position().top - $('table.inventory tbody').position().top;
            $('table.inventory tbody').animate({ scrollTop: rowpos});
        } else if (globals['productid']) {
            selectProduct(globals['productid'],true,null);
            var rowpos = $('tr#product_' + globals['productid']).position().top - $('table.inventory tbody').position().top;
            $('table.inventory tbody').animate({ scrollTop: rowpos});
        }
    });
}

function hideLocationFilter() {
    if ($('#location_filter').is(':hover')) {
        setTimeout('hideLocationFilter()',filter_popup_timeout);
    } else {
        $('#location_filter').hide();
    }
}

function refreshShipments(shipmentid) {
    if (!('shipped_filter' in globals)) {
        globals['shipped_filter'] = 1;
    }

    $('#list_shipments tbody').empty().append($('<img>', {
        src: '/static/images/loading_bar.gif',
        class: 'loading',
    }));

//    var url = cgiroot+'ajax_shipments_list.cfm?customerid='+$('#customerid').val()+'&shipped_filter='+globals['shipped_filter'];
    var url = cgiroot + $('#customerid').val() + '/shipments/list/?shipped_filter=' + globals['shipped_filter'];
console.log(url);
    $('#list_shipments').load(url,function(data) {
        refreshUI();
        if (shipmentid) {
            selectShipment(shipmentid);
            var rowpos = $('tr#shipment_' + shipmentid).position().top - $('table.shipments tbody').position().top;
            $('table.shipments tbody').animate({ scrollTop: rowpos});
        }
    });
}

function setupAddCustomerButton() {
    $('#customer_name_new').val('');
    $('#add_customer').click(function() {
        $('#customer_name_new').show(function() {
            $('#customer_name_new').css('visibility', 'visible');
            $('#customer_name_new').animate({
                width: 230,
                marginLeft: 10
            },200);
        });
        $('#add_customer').button().click(function() {
            if ($('#customer_name_new').val()) {
                $('#add_customer_confirm').dialog('open');
            } else {
                resetAddCustomerButton();
            }
        });
    });
}

function resetAddCustomerButton() {
    $('#customer_name_new').animate({
        width: 0,
        marginLeft: 0
    },200,function() {
        $('#customer_name_new').css('visibility', 'hidden');
        $('#add_customer').off("click");
        setupAddCustomerButton();
    });
}

function focusDocument() {
    var frameDoc = top.frames['frame'].contentWindow;
    $(frameDoc).focus();
}

function clearKeyInput() {
    keyinput = '';
}

function focusCustomer(name) {
    var matching_customers = $('#customers_list li div:startsWith('+name+')');
    if (matching_customers.length) {
        var rowpos = matching_customers.first().parent().position().top - $('#customers_list').position().top;
        $('#customers_list_wrap').animate({ scrollTop: rowpos});
    }
}

$.extend($.expr[":"], {
    "startsWith": function(elem, i, match, array) {
        return (elem.textContent.replace(/\s/g,'') || elem.innerText || "").toLowerCase().indexOf((match[3] || "").toLowerCase()) == 0;
    }
});


function generateReport(productid) {
    fromdate = $('#fromdate').val();
    todate = $('#todate').val();
    var url = cgiroot+'gen_report.cfm?productid='+productid+'&fromdate='+fromdate+'&todate='+todate;
    window.open(url);  
}

function setupInventoryList(customerid) {
    globals['customerid'] = customerid;
    $('#dialog_inventory_list').dialog('open');
}

function setupInventoryAnalysis(customerid) {
    globals['customerid'] = customerid;
    $('#dialog_inventory_analysis').dialog('open');
}

function setupProductTransfer(productid, customerid) {
    $('#transfer_remain_selected').html($('#remain_'+productid).val());
    $('#transfer_cases').val('');
    $('.transfer_destination').empty();
//    var url = cgiroot+'ajax_product_action.cfm';
    if (customerid) {
        var url = apiroot + customerid + '/products/';
        $.get(url, {
            method: 'getCustomerProducts', 
            customerid: customerid,
            source_productid: productid,
        }, function(data) {
console.log(data);
            for (p in data) {
                var li = $('<li>', {
                    productid: data[p].id,
                    customerid: customerid,
                });
                li.append($('<span>', {
                    html: data[p].cases_inventory,
                    class: 'remain',
                }));
                var productStr = data[p].name;
                if (data[p].item_number)
                    productStr = data[p].item_number + ' ' + productStr;
                if (data[p].packing)
                    productStr = productStr + ' [' + data[p].packing + ']';
                li.append($('<span>', {
                    html: productStr,
                }));
                $('#transfer_product').append(li);
            }
            var li = $('<li>', {
                productid: null,
                customerid: customerid,
            });
            li.append($('<span>', {
                html: 0,
                class: 'remain',
            }));
            var productStr = '(Create new product)';
            li.append($('<span>', {
                html: productStr,
            }));
            $('#transfer_product').append(li);

            $('#transfer_product li').click(function() {
                execute_transferProduct(productid, $(this).attr('productid'), $(this).attr('customerid'));
            });
        }, 'json');
        $('#dialog_transfer_selectproduct').dialog('open');
    } else {
        var url = apiroot + '/clients/';
        $.get(url, {'method': 'getCustomers'}, function(data) {
            for (c in data) {
                var li = $('<li>', {
                    customerid: data[c].id,
                    class: data[c].id == globals['customerid_current'] ? 'invalid-target' : 'valid-target',
                });
                li.append($('<span>', {
                    html: data[c].company_name,
                    css: {'paddingLeft': data[c].depth * 20},
                }));
                $('#transfer_customer').append(li);
            }
            $('#transfer_customer li.valid-target').click(function() {
                $('#dialog_transfer_selectcustomer').dialog('close');
                setupProductTransfer(productid, $(this).attr('customerid'));
            });
        }, 'json');
        $('#dialog_transfer_selectcustomer').dialog('open');
    }
}

function execute_transferProduct(from_productid, to_productid, to_customerid) {
//    var url = cgiroot+'ajax_product_action.cfm';
    var url = cgiroot + 'product/' + from_productid + '/transfer/';
    var cases = parseInt($('#transfer_cases').val());
    if (!cases) {
        alert('Please enter the number of cases to transfer.');
        return;
    }
    if (cases > $('#transfer_remain_selected').html()) {
        alert('Number of cases specified is more than the number remaining.');
        return;
    };
    $('#dialog_transfer_selectproduct').dialog('close');
    var params = {
        method: 'transferProduct',
        from_productid: from_productid,
        to_productid: to_productid,
        to_customerid: to_customerid,
        cases: cases,
    };
    $.post(url, params, function(data) {
        if (data.success) {
            alert('Inventory successfully transferred.');
            refreshInventory();
        } else {
            alert(data.error);
        }
    }, 'json');
}

function setupSearch() {
    $('#search_client').val($('.customerheader').html());
    $('#dialog_search .clear').val('');
    $('#dialog_search').dialog('open');
}

function execute_search() {
    var search = $('#form_search').serialize();
    var url = 'search.cfm?' + search;
    window.open(url);
}


$(document).ready(function() {
    $('#toolsmenulink').click(function() {
        $('.popupbox').hide();
        $('#menu_tools').show();
        return false;
    });
    $('#adminmenulink').click(function() {
        $('.popupbox').hide();
        $('#menu_admin').show();
        return false;
    });
    $('html').click(function() {
        $('.popupbox').hide();
    });

    $('#add_customer').button({
      icons: {
        primary: "ui-icon-plusthick"
      },
      text: false
    })
    setupAddCustomerButton();
    refreshCustomers();
    refreshInventory();
    refreshShipments();

    refreshUI();

    setTimeout('focusDocument()',100);
    $('body').keyup(function(e) {
        if (e.keyCode == 27) {
            $('tr.product').removeClass('selected');
            $('tr.product').removeClass('selected_history');
            $('.action').removeClass('selected');
//            $('tr.product input').prop('disabled',true);
            $('tr.product input').blur();
        }
        if ($('#customers_list_wrap').length && e.target.nodeName != 'INPUT') {
            clearTimeout(keyinput_timeout);
            keyinput_timeout = setTimeout('clearKeyInput()',1000);
            keyinput += String.fromCharCode(e.which);
            focusCustomer(keyinput);
        }
    });

    $( "#add_customer_confirm" ).dialog({
        autoOpen: false,
        resizable: false,
        height: 180,
        modal: true,
        buttons: {
            "Add customer": function() {
                execute_addCustomer();
                $( this ).dialog( "close" );
            },
            Cancel: function() {
                $( this ).dialog( "close" );
                resetAddCustomerButton();
            }
        }
    });

    $( "#custcontact_delete_confirm" ).dialog({
        autoOpen: false,
        resizable: false,
        modal: true,
        buttons: {
            "Delete contact": function() {
                execute_deleteCustContact();
                $( this ).dialog( "close" );
            },
            Cancel: function() {
                $( this ).dialog( "close" );
                resetAddCustomerButton();
            }
        }
    });

    $( "#location_delete_confirm" ).dialog({
        autoOpen: false,
        resizable: false,
        modal: true,
        buttons: {
            "Delete location": function() {
                execute_deleteLocation();
                $( this ).dialog( "close" );
            },
            Cancel: function() {
                $( this ).dialog( "close" );
            }
        }
    });

    $( "#product_delete_confirm" ).dialog({
        autoOpen: false,
        resizable: false,
        height: 180,
        modal: true,
        buttons: {
            "Delete": function() {
                execute_deleteProduct(0, false);
                $( this ).dialog( "close" );
            },
            Cancel: function() {
                $( this ).dialog( "close" );
            }
        }
    });

    $( "#product_permdelete_confirm" ).dialog({
        autoOpen: false,
        resizable: false,
        height: 180,
        modal: true,
        buttons: {
            "Delete": function() {
                execute_deleteProduct(0, true);
                $( this ).dialog( "close" );
            },
            Cancel: function() {
                $( this ).dialog( "close" );
            }
        }
    });

    $( "#product_undelete_confirm" ).dialog({
        autoOpen: false,
        resizable: false,
        height: 180,
        modal: true,
        buttons: {
            "Restore": function() {
                execute_deleteProduct(1);
                $( this ).dialog( "close" );
            },
            Cancel: function() {
                $( this ).dialog( "close" );
            }
        }
    });

    $( "#shipment_cancel_confirm" ).dialog({
        autoOpen: false,
        resizable: false,
        height: 180,
        modal: true,
        buttons: {
            "Cancel shipment": function() {
                execute_cancelShipment();
                $( this ).dialog( "close" );
            },
            Dismiss: function() {
                $( this ).dialog( "close" );
            }
        }
    });

    $( "#incoming_cancel_confirm" ).dialog({
        autoOpen: false,
        resizable: false,
        height: 180,
        modal: true,
        buttons: {
            "Cancel receivable": function() {
                execute_cancelIncoming();
                $( this ).dialog( "close" );
            },
            Dismiss: function() {
                $( this ).dialog( "close" );
            }
        }
    });

    $( "#incoming_save_confirm" ).dialog({
        autoOpen: false,
        resizable: false,
        height: 180,
        modal: true,
        buttons: {
            "Confirm receivable": function() {
                execute_saveTransaction();
                $( this ).dialog( "close" );
            },
            Dismiss: function() {
                $( this ).dialog( "close" );
            }
        }
    });

    $('#dialog_addreceivable_result').dialog({
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

    $('#dialog_confirmreceivable_result').dialog({
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

    $('#dialog_saveproduct_result').dialog({
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

    $('#shipment_upload_form').dialog({
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

    $('#dialog_inventory_list').dialog({
        autoOpen: false,
        resizable: false,
        modal: true,
        position: { my: "top", at: "top+200", of: window },
        buttons: {
            Generate: function() {
                $( this ).dialog( "close" );
                var url = 'gen_inventory_list.cfm?customerid=' + globals['customerid'] + '&last_months=' + $('#last_months').val();
                window.open(url);
            },
            Cancel: function() {
                $( this ).dialog( "close" );
            }
        }
    });

    $('#dialog_inventory_analysis').dialog({
        autoOpen: false,
        resizable: false,
        modal: true,
        position: { my: "top", at: "top+200", of: window },
        buttons: {
            Generate: function() {
                $( this ).dialog( "close" );
                var url = 'gen_inventory_analysis.cfm?customerid=' + globals['customerid'];
//                window.open(url);
            },
            Cancel: function() {
                $( this ).dialog( "close" );
            }
        }
    });


    $('#dialog_transfer_selectcustomer').dialog({
        autoOpen: false,
        resizable: false,
        modal: true,
        position: { my: "top", at: "top+100", of: window },
        maxHeight: 600,
        buttons: {
            Cancel: function() {
                $( this ).dialog( "close" );
            }
        }
    });


    $('#dialog_transfer_selectproduct').dialog({
        autoOpen: false,
        resizable: false,
        modal: true,
        position: { my: "top", at: "top+100", of: window },
        maxHeight: 600,
        width: 500,
        buttons: {
            Cancel: function() {
                $( this ).dialog( "close" );
            }
        }
    });


    $('#search_shippedon').datepicker();
    $('#dialog_search').dialog({
        autoOpen: false,
        resizable: false,
        modal: true,
        width: 600,
        position: { my: "top", at: "top+200", of: window },
        buttons: {
            Search: function() {
                $( this ).dialog( "close" );
                execute_search();
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

    // Expand/collapse notification panels
    $('#notifications .list_header').click(function() {
        var section = $(this).attr('section');

        $('.list_wrap[section=' + section + ']').toggleClass('minimized').toggleClass('maximized');

        $('.list_wrap[section=' + section + ']').animate({
            height: $('.list_wrap[section=' + section + ']').hasClass('maximized') ? 600 : $('.list_wrap[section=' + section + ']').hasClass('two') ? 280 : 175,
            maxHeight: $('.list_wrap[section=' + section + ']').hasClass('maximized') ? 600 : 250,
        }, 300, function() {
            $('#notifications .list_header[section=' + section + '] .disclosure').toggleClass('open');
            $('#notifications .list_header[section!=' + section + '] .disclosure').removeClass('open');
        });

        $(this).siblings('.list_wrap').not('[section=' + section + ']').animate({
            height: $('.list_wrap[section=' + section + ']').hasClass('maximized') ? 0 : $('.list_wrap[section=' + section + ']').hasClass('two') ? 280 : 175,
        }, 300, function() {
            $(this).removeClass('maximized').addClass('minimized');
        });
    });

    if (globals['shipmentid']) {
        selectShipment(globals['shipmentid']);
        var rowpos = $('tr#shipment_' + globals['shipmentid']).position().top - $('table.shipments tbody').position().top;
        $('table.shipments tbody').animate({ scrollTop: rowpos});
    }

    $('#toggle_inactive').button({
        text: false,
        icons: { primary: 'ui-icon-person' }
    }).click(function() {
        toggleInactiveCustomers();
    });

    $('table.search tr').click(function() {
        var customerid = $(this).attr('customerid');
        var shipmentid = $(this).attr('shipmentid');
        var productid = $(this).attr('productid');
        var url;
        if (globals['search_itemnum']) {
            url = 'inventory.cfm?customerid=' + customerid + '&history=' + productid;
        } else {
            url = 'shipments.cfm?customerid=' + customerid + '&shipmentid=' + shipmentid;
        }
        window.open(url);
    });

    $('#inventory_list_fromdate').datepicker();
    $('#inventory_list_todate').datepicker();
    $('#delivery_list_fromdate').datepicker();
    $('#delivery_list_todate').datepicker();
    $('#incoming_list_fromdate').datepicker();
    $('#incoming_list_todate').datepicker();

});



