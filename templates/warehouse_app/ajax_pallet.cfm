<CFIF IsDefined("Form.products")>

    <CFSET Form.DSN = DSN>

    <cfinvoke
       component="cfc/ajax_functions"
       method="createPallet"
       returnVariable="getData"
       argumentCollection="#Form#">
    </cfinvoke>

    <cfoutput>#SerializeJSON(getData)#</cfoutput>

<CFELSEIF IsDefined("URL.s")>

    <CFQUERY NAME="ProdCheck" DATASOURCE="#DSN#">
    SELECT Products.*,cases FROM Products,Transactions
    WHERE Products.productid=Transactions.productid
    AND Transactions.shipmentid=<CFQUERYPARAM value="#URL.s#" CFSQLType="CF_SQL_VARCHAR">
    </CFQUERY>

    <table id="pallet_contents" class="infotable" style="width: 500px;">
        <CFOUTPUT QUERY="ProdCheck">
        <tr>
            <td>#pname#</td>
            <td id="cases_req_#PRID#">#cases#</td>
            <td class="cases_incomplete" id="cases_#ProdCheck.PRID#">0</td>
        </tr>
        </CFOUTPUT>
    </table>

<CFELSE>

    Invalid request.

</CFIF>

