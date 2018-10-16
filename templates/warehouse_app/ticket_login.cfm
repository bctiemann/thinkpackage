<CFINCLUDE TEMPLATE="inc_header.cfm">

<div id="content">

<img src="images/tp.png" border=0 hspace=0 vspace=0 alt="Think Package iPad App" />

<div class="above_login" id="toggle_info">
<img src="images/kdc300_text.png" />
</div>

<CFIF NOT StructIsEmpty(Form)>
<div class="above_login"> 
<div id="login_status">   
<h3>ACCESS DENIED</h3>
<CFIF IsDefined("AccessDenied")>
    <p>You have entered an incorrect password for the specified account.</p>
</CFIF>
<CFIF IsDefined("NoMail")>
    <p>The user account you have entered does not exist.</p>
</CFIF>
<CFIF IsDefined("Disabled")>
    <p>Your account has been disabled.</p>
</CFIF>
<CFIF IsDefined("BadKey") AND NOT IsDefined("AccessDenied")>
    <p>Your 2-factor authenticator is invalid or has expired.</p>
</CFIF>
<CFIF IsDefined("Disabled")>
    <p>Your account has been disabled.</p>
</CFIF>
<CFIF IsDefined("NoKey")>
    <p>You do not have a 2-factor key.</p>
</CFIF>
<CFIF IsDefined("KeyExpired")>
    <p>Your 2-factor key has expired.</p>
</CFIF>   
</div>    
</div> 
</CFIF>

<cfform method="post" action="index.cfm">
<table class="loginform">
<tr>
    <td class="data"><cfinput type="text" size="20" name="user" id="user" required="yes" message="You must enter a user name." placeholder="Login" onFocus="showToggleInfo()" autocapitalize="off"></td>
</tr>
<tr>
    <td class="data"><cfinput type="password" size="20" name="pass" required="yes" message="You must enter a password." placeholder="Password" onFocus="showToggleInfo()"></td>
</tr>
<tr>
    <td colspan="2" align="center"><input type="submit" value="Log In"></td>
</tr>
</table>
</cfform>

</div>

<CFINCLUDE TEMPLATE="inc_footer.cfm">
<CFABORT>
