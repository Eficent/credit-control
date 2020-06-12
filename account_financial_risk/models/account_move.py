# Copyright 2020 ForgeFlow
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import api, fields, models


class AccountMoveLine(models.Model):
    _inherit = 'account.move.line'

    risk_currency_id = fields.Many2one(
        related="partner_id.risk_currency_id")
    risk_amount_residual = fields.Monetary(
        string="Risk Residual Amount",
        currency_field="risk_currency_id",
        compute="_compute_risk_amount_residual")

    @api.multi
    @api.depends('debit', 'credit', 'amount_currency', 'currency_id',
                 'matched_debit_ids', 'matched_credit_ids',
                 'matched_debit_ids.amount', 'matched_credit_ids.amount',
                 'move_id.state',
                 'partner_id.credit_currency',
                 'partner_id.manual_credit_currency_id',
                 'partner_id.property_account_receivable_id.currency_id',
                 'partner_id.country_id',
                 'company_id.currency_id')
    def _compute_risk_amount_residual(self):
        for move_line in self:
            move_line.risk_amount_residual = \
                move_line.company_currency_id.with_context(
                    date=move_line.move_id.date or
                    fields.Date.context_today(self)).compute(
                    move_line.amount_residual,
                    move_line.risk_currency_id, round=False
                )
