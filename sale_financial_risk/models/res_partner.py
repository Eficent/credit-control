# Copyright 2016-2020 Tecnativa - Carlos Dauden
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import _, api, fields, models


class ResPartner(models.Model):
    _inherit = 'res.partner'

    risk_sale_order_include = fields.Boolean(
        string='Include Sales Orders', help='Full risk computation')
    risk_sale_order_limit = fields.Monetary(
        string='Limit Sales Orders',
        currency_field="risk_currency_id",
        help='Set 0 if it is not locked')
    risk_sale_order = fields.Monetary(
        compute='_compute_risk_sale_order',
        currency_field="risk_currency_id",
        compute_sudo=True,
        string='Total Sales Orders Not Invoiced',
        help='Total not invoiced of sales orders in Sale Order state')

    def _get_risk_sale_order_domain(self):
        # When p is NewId object instance bool(p.id) is False
        commercial_partners = self.filtered(lambda p: (
            p.customer and p.id and p == p.commercial_partner_id
        ))
        return self._get_risk_company_domain() + [
            ('state', '=', 'sale'),
            ('commercial_partner_id', 'in', commercial_partners.ids),
        ]

    @api.depends('sale_order_ids.order_line.risk_amount',
                 'child_ids.sale_order_ids.order_line.risk_amount')
    def _compute_risk_sale_order(self):
        self.update({'risk_sale_order': 0.0})
        orders_group = self.env['sale.order.line'].read_group(
            domain=self._get_risk_sale_order_domain(),
            fields=['commercial_partner_id', 'company_id', 'risk_amount'],
            groupby=['commercial_partner_id', 'company_id'],
            orderby='id',
            lazy=False,
        )
        for group in orders_group:
            partner = self.browse(
                group["commercial_partner_id"][0], self._prefetch)
            company_currency = self.env['res.company'].browse(
                group['company_id'][0] or self.env.user.company_id.id
            ).currency_id
            partner.risk_sale_order = company_currency.compute(
                group["risk_amount"], partner.risk_currency_id, round=False)

    @api.model
    def _risk_field_list(self):
        res = super(ResPartner, self)._risk_field_list()
        res.append(('risk_sale_order', 'risk_sale_order_limit',
                    'risk_sale_order_include'))
        return res

    def _get_field_risk_model_domain(self, field_name):
        if field_name == 'risk_sale_order':
            return 'sale.order.line', self._get_risk_sale_order_domain()
        else:
            return super()._get_field_risk_model_domain(field_name)

    @api.multi
    def _get_domain_risk_tree(self):
        domain = super(ResPartner, self)._get_domain_risk_tree()
        risk_type = self._context.get('risk_type')
        if risk_type == "sale":
            domain += [
                ('order_partner_id', 'in', (self | self.child_ids).ids),
                ('state', '=', "sale"),
                '|', ('price_total', '!=', 0.0),
                ('amt_invoice_diff', '!=', 0.0),
            ]
        return domain

    @api.multi
    def _get_view_risk_tree(self, domain):
        view = super(ResPartner, self)._get_view_risk_tree(domain)
        risk_type = self._context.get('risk_type')
        if risk_type == "sale":
            view_tree = self.env.ref('sale_financial_risk.'
                                     'view_sale_line_risk_tree')
            view = {'name': _('Sale Order Lines'),
                    'type': 'ir.actions.act_window',
                    'res_model': 'sale.order.line',
                    'view_type': 'form',
                    'view_mode': 'tree, form',
                    'views': [(view_tree.id, 'tree')],
                    'domain': domain,
                    }
        return view
