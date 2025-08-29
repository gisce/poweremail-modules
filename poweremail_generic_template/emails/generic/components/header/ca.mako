<%
    from ast import literal_eval
    confvar_obj = pool.get('res.config')
    confvar = literal_eval(confvar_obj.get(
        cursor, uid, 'url_logo_sector', 'https://gisce.net/images/logo.png'
        ))
    model_name = object._name
%>
<table role="presentation" border="0" cellpadding="0" cellspacing="0" width="100%">
  <tr>
    <td class="align-center" width="100%">
        %if 'giscedata' in model_name:
            <img src="${confvar}/images/logo_electricitat.png" height="100" alt="Logo empresa">
        %elif 'giscegas' in model_name:
            <img src="${confvar}/images/logo_gas.png" height="100" alt="Logo empresa">
        %endif
    </td>
  </tr>
</table>
