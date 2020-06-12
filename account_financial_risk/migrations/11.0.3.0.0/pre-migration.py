# Copyright 2020 ForgeFlow S.L.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).
from odoo.addons.account_financial_risk.hooks import pre_init_hook
from odoo.tools import column_exists


def migrate(cr, version):
    if not column_exists(cr, "account_invoice", 'company_currency_id'):
        pre_init_hook(cr)
