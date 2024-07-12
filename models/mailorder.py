from odoo import models, fields, api

class MailOrder(models.Model):
    _name = 'uic.post.mailorder'
    _description = 'Mail Order'

    name = fields.Char(string='Order Reference', required=True, copy=False, readonly=True, index=True, default=lambda self: ('New'))
    sender_id = fields.Many2one('res.partner', string='Sender', required=True)
    recipient_id = fields.Many2one('res.partner', string='Recipient', required=True)
    sending_branch_id = fields.Many2one('res.company', string='Sending Branch', required=True, default=lambda self: self.env.company)
    receiving_branch_id = fields.Many2one('res.company', string='Receiving Branch', required=True)
    package_count = fields.Integer(string='Number of Packages', required=True)
    total_weight = fields.Float(string='Total Weight (kg)', required=True)
    size = fields.Float(string='Size (cubic meters)', required=True)
    is_fragile = fields.Boolean(string='Fragile')
    price = fields.Float(string='Price', compute='_compute_price', store=True)
    status = fields.Selection([
        ('accepting', 'Accepting'),
        ('in_stock', 'In Stock'),
        ('during_delivery', 'During Delivery'),
        ('delivered', 'Delivered'),
    ], string='Status', default='accepting')
    loyalty_points = fields.Float(string='Loyalty Points', compute='_compute_loyalty_points')
    picking_id = fields.Many2one('stock.picking', string='Picking', readonly=True)

    @api.model
    def create(self, vals):
        if vals.get('name', 'New') == 'New':
            vals['name'] = self.env['ir.sequence'].next_by_code('uic.post.mailorder') or 'New'
        order = super(MailOrder, self).create(vals)
        order._create_stock_picking()
        return order

    @api.depends('total_weight', 'size')
    def _compute_price(self):
        for order in self:
            price = 15000
            if order.total_weight > 5:
                price += (order.total_weight - 5) * 1000
            if order.total_weight > 30:
                price += (order.total_weight - 30) * 2000
            if order.size > 1:
                price += 30000
            if order.size > 2:
                price = 0
            order.price = price

    @api.depends('price')
    def _compute_loyalty_points(self):
        for order in self:
            order.loyalty_points = order.price * 0.01
    def _create_stock_picking(self):
        product_delivery = self.env.ref('product.product_delivery', raise_if_not_found=False)
        if not product_delivery:
            product_delivery = self.env['product.product'].create({
                'name': 'Delivery Product',
                'type': 'service',
                'list_price': 0.0,
            })

        stock_picking = self.env['stock.picking'].create({
            'partner_id': self.sender_id.id,
            'location_id': self.env.ref('stock.stock_location_customers').id,
            'location_dest_id': self.env.ref('stock.stock_location_stock').id,
            'picking_type_id': self.env.ref('stock.picking_type_out').id,
            'move_ids_without_package': [(0, 0, {
                'name': self.name,
                'product_id': product_delivery.id,
                'product_uom_qty': 1,
                'product_uom': product_delivery.uom_id.id,
                'location_id': self.env.ref('stock.stock_location_customers').id,
                'location_dest_id': self.env.ref('stock.stock_location_stock').id,
            })],
        })
        return stock_picking