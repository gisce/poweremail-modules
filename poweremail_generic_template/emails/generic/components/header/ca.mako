<%
    from ast import literal_eval
    confvar_obj = pool.get('res.config')
    elect_logo = literal_eval(confvar_obj.get(
        cursor, uid, 'url_logo_elect', 'https://gisce.net/images/logo.png'
        ))
    gas_logo = literal_eval(confvar_obj.get(
        cursor, uid, 'url_logo_gas', 'https://gisce.net/images/logo.png'
        ))
    model_name = object._name
%>
<table role="presentation" border="0" cellpadding="0" cellspacing="0" width="100%">
  <tr>
    <td class="align-center" width="100%">
        %if 'giscedata' in model_name:
            <img src="${elect_logo}" height="100" alt="Logo empresa">
        %elif 'giscegas' in model_name:
            <img src="${gas_logo}" height="100" alt="Logo empresa">
        %endif
    </td>
  </tr>
</table>
