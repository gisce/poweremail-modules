<!doctype html>
<%
from datetime import datetime
from poweremail.poweremail_template import get_value

today = datetime.today().date().strftime('%Y-%m-%d')

banner_o = pool.get('report.banner')

banners = banner_o.get_report_banners(
  cursor, uid, 'poweremail.templates,{}'.format(template.id),
  today, object.id, context={'lang': lang}
)

try:
  company = eval(banners['generic_email_template_company'])
except:
  company = False

if not company:
  company = pool.get('res.company').browse(cursor, uid, 1, context={})

env['company'] = company
ctx = {
    'lang': lang,
    'raise_exception': True,
}
ctx.update(env)

body_html = get_value(cursor, uid, object.id, message=banners['generic_email_template_body'], template=template, context=ctx)
footer_html = get_value(cursor, uid, object.id, message=banners['generic_email_template_footer'], template=template, context=ctx)
%>
<html>
  <head>
    <meta name="viewport" content="width=device-width" />
    <meta http-equiv="Content-Type" content="text/html; charset=UTF-8" />
    <title>${banners['generic_email_template_title']}</title>
    <style>
      ${banners['generic_email_template_css']}
    </style>
  </head>
  <body class="">
    <table role="presentation" border="0" cellpadding="0" cellspacing="0" class="body">
      <tr>
        <td>&nbsp;</td>
        <td class="container">
          <div class="header">${banners['generic_email_template_header']}</div>
          <div class="content">

            <!-- START CENTERED WHITE CONTAINER -->
            <span class="preheader">${banners['generic_email_template_preheader']}</span>
            <table role="presentation" class="main">

              <!-- START MAIN CONTENT AREA -->
              <tr>
                <td class="wrapper">
                  ${body_html}
                </td>
              </tr>
            <!-- END MAIN CONTENT AREA -->
            </table>
            <!-- START FOOTER -->
            <div class="footer">${footer_html}</div>
            <!-- END FOOTER -->
          <!-- END CENTERED WHITE CONTAINER -->
          </div>
        </td>
        <td>&nbsp;</td>
      </tr>
    </table>
  </body>
</html>