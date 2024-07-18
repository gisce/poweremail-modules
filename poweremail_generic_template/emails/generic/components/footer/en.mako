<% company = object.company_id %>
<table role="presentation" border="0" cellpadding="0" cellspacing="0">
  <tr>
    <td class="content-block">
      <span class="apple-link">${company.partner_id.address[0].street}</span>
      <br> 📞 ${company.partner_id.address[0].phone} / ${company.partner_id.address[0].mobile}
      <br> 📨 ${company.partner_id.address[0].email}
    </td>
  </tr>
  <tr>
    <td class="content-block powered-by">
      <a href="${company.partner_id.website}">${company.partner_id.name}</a>.
    </td>
  </tr>
</table>
