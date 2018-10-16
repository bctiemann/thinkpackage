<CFIF IsDefined("Form.receivableid")>

    <CFSET Form.DSN = DSN>
    <CFSET Form.YourID = YourID>

    <cfinvoke
       component="cfc/ajax_functions"
       method="updateTransaction"
       returnVariable="getData"
       argumentCollection="#Form#">
    </cfinvoke>

    <cfoutput>#SerializeJSON(getData)#</cfoutput>

<CFELSEIF IsDefined("URL.r") AND IsNumeric(URL.r)>

    <CFQUERY NAME="ReceivableCheck" DATASOURCE="#DSN#">
    SELECT * FROM Receivables,Products
    WHERE Receivables.productid=Products.productid
    AND Receivables.receivableid=<CFQUERYPARAM value="#URL.r#" CFSQLType="CF_SQL_NUMERIC">
    </CFQUERY>

    <CFOUTPUT QUERY="ReceivableCheck">
    <p>Packing: #packing# per case</p>
    <p>Expected: #cases# cases</p>
    <p>Enter the number of cases received.</p>
    <input type="number" name="cases" id="cases" placeholder="Cases" min="0" onFocus="showToggleInfo()" />
    <button class="actionbtn" onClick="submitReceivable(#receivableid#)">Done</button>
    </CFOUTPUT>

    <div id="toggle_info">
    <img src="images/kdc300_text.png" />
    </div>

    <div id="error"></div>

<CFELSE>

    Invalid request.

</CFIF>

