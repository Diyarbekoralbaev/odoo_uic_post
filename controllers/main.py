from odoo import http
from odoo.http import request


class UICPost(http.Controller):

    @http.route('/get_status', type='http', auth='public', methods=['POST'], website=True)
    def get_status(self, **post):
        postal_invoice_id = post.get('postal_invoice_id')
        order = request.env['uic.post.mailorder'].sudo().search([('name', '=', postal_invoice_id)], limit=1)
        status = order.status if order else 'Order not found'
        return http.request.render('uic_post.status_result', {'status': status})
