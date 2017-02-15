# -*- coding: utf-8 -*-
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
{
    'name': 'Sale Manual Delivery',
    'category': 'Sale',
    'author': 'Camptocamp SA, Odoo Community Association (OCA)',
    'version': '10.0.1.0.0',
    'website': 'http://camptocamp.com',
    'summary': "Sale manual delivery",
    'depends': [
        'delivery',
        'sale',
        'sales_team',
    ],
    'data': [
        'views/crm_team_view.xml',
        'views/sale_order_view.xml',
        'wizard/manual_proc_view.xml',
    ],
    'installable': True,
    'application': False,
    'auto_install': False,
}
