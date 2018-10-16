<CFIF IsDefined("URL.m") AND IsDefined("URL.c")>


<CFIF URL.m IS "prodcheck">

    <CFQUERY NAME="ProdCheck" DATASOURCE="#DSN#">
    SELECT Products.*,coname FROM Products,Customers
    WHERE CONCAT("1TP:",UPPER(PRID)) = <CFQUERYPARAM value="#ucase(URL.c)#" CFSQLType="CF_SQL_VARCHAR">
    AND Products.customerid=Customers.customerid
    </CFQUERY>

    <CFIF ProdCheck.recordcount GT 0>

        <CFOUTPUT QUERY="ProdCheck">

        <table class="infotable alternating" style="width: 400px; margin-top: 20px;">
        <tr>
            <td class="label">Customer</td>
            <td class="data">#coname#</td>
        </tr>
        <tr>
            <td class="label">Product</td>
            <td class="data">#pname#</td>
        </tr>
        <tr>
            <td class="label">Created</td>
            <td class="data">#DateFormat(createdon,"mm/dd/yy")#</td>
        </tr>
<!---
        <tr>
            <td class="label">PO ##</td>
            <td class="data">#PO#</td>
        </tr>
        <tr>
            <td class="label">SO ##</td>
            <td class="data">#SO#</td>
        </tr>
--->
        <tr>
            <td class="label">Dimensions (l &times; w &times; h)</td>
            <td class="data">#length# &times; #width# &times; #height# in</td>
        </tr>
        <tr>
            <td class="label">Gross Weight</td>
            <td class="data"><CFIF IsNumeric(GW)>#NumberFormat(GW*2.205,",._")# lb (#NumberFormat(GW,",._")# kg)</CFIF></td>
        </tr>
        </table>

        </CFOUTPUT>

    <CFELSE>

        <p>Sorry, no product found with that ID.</p>

    </CFIF>

<CFELSEIF URL.m IS "pcheck">

    <CFSET palletInfo = ListToArray(URL.c,";")>

    <CFSET PID = palletInfo[1]>

    <CFQUERY NAME="PCheck" DATASOURCE="#DSN#">
    SELECT * FROM Pallets
    WHERE CONCAT("1TP:",UPPER(PID)) = <CFQUERYPARAM value="#ucase(PID)#" CFSQLType="CF_SQL_VARCHAR">
    </CFQUERY>

    <CFIF PCheck.recordcount GT 0 AND IsNumeric(PCheck.palletid)>

        <CFQUERY NAME="BOnPal" DATASOURCE="#DSN#">
        SELECT * FROM OnPallet,Products,Customers
        WHERE palletid = #PCheck.palletid#
        AND Products.productid=OnPallet.productid
        AND Products.customerid=Customers.customerid
        </CFQUERY>

        <CFQUERY NAME="TShip" DATASOURCE="#DSN#">
        SELECT * FROM Shipments,CustContacts,Locations
        WHERE shipmentid=#PCheck.shipmentid#
        AND Shipments.locationid=Locations.locationid
        AND Locations.custcontactid=CustContacts.custcontactid
        </CFQUERY>
        <CFQUERY NAME="TCust" DATASOURCE="#DSN#">
        SELECT coname,email FROM Customers
        WHERE customerid = #PCheck.customerid#
        </CFQUERY>


        <CFOUTPUT>

        <table class="infotable alternating decoded_info" style="margin-top: 20px;">
        <tr>
            <td class="label">Pallet ID</td>
            <td class="data">#PCheck.PID#</td>
        </tr>
        <tr>
            <td class="label">Customer</td>
            <td class="data"><CFIF TShip.recordcount>#TCust.coname#<CFELSE>(Storage Pallet)</CFIF></td>
        </tr>
        <CFIF TShip.recordcount>
        <tr>
            <td class="label">Shipment</td>
            <td class="data">#TShip.shipmentid#</td>
        </tr>
        </CFIF>
        <tr>
            <td class="label">Created</td>
            <td class="data">#DateFormat(PCheck.createdon,"mm/dd/yy")#</td>
        </tr>
        </table>

        </CFOUTPUT>

        <p>Products:</p>

        <table class="infotable alternating decoded_info">
        <CFSET totalGW = 0>
        <CFOUTPUT QUERY="BOnPal">
            <tr>
                <td>
                <CFIF TShip.recordcount IS 0><p class="coname">#coname#</p></CFIF>
                #pname#
                </td>
                <td class="numeric">#NumberFormat(qty,",")#</td>
            </tr>
        <CFSET totalGW += GW * packing>
        </CFOUTPUT>
        </table>
        
        <CFOUTPUT>
        <div class="weight">
            <p>Total gross weight: #NumberFormat(totalGW*2.205,",._")# lb (#NumberFormat(totalGW,",._")# kg)</p>
        </div>
        </CFOUTPUT>

        <CFOUTPUT QUERY="TShip">
        <div class="contact">   
            <p>#name#</p>
            <p>#addr# #addr2#</p>
            <p>#city#, #state# #zip#</p>
            <p>#TShip.fname# #TShip.lname#</p>
            <p>#tel#</p>
        </div>
        </CFOUTPUT>

    <CFELSE>

        <p>Sorry, an error occurred fetching details for that pallet.</p>

    </CFIF>

<CFELSEIF URL.m IS "pallet">

    <cfset ret = StructNew()>

    <CFQUERY NAME="ProdCheck" DATASOURCE="#DSN#">
    SELECT Products.*,coname FROM Products,Customers
    WHERE CONCAT("1TP:",UPPER(PRID)) = <CFQUERYPARAM value="#ucase(URL.c)#" CFSQLType="CF_SQL_VARCHAR">
    AND Products.customerid=Customers.customerid
    </CFQUERY>
    <CFSET ret.productid = ProdCheck.productid>
    <CFSET ret.PRID = ProdCheck.PRID>
    <CFSET ret.pname = ProdCheck.pname>
    <CFSET ret.coname = ProdCheck.coname>

    <cfoutput>#SerializeJSON(ret)#</cfoutput>

</CFIF>

<CFELSE>

Invalid request.

</CFIF>
