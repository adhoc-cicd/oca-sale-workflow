# Copyright 2018 Tecnativa - Carlos Dauden
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo.tests import Form, SavepointCase


class TestSaleOrderLineInput(SavepointCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.partner = cls.env["res.partner"].create({"name": "Test"})
        cls.product = cls.env["product.product"].create(
            {"name": "test_product", "type": "service"}
        )

    def test_sale_order_create_and_show(self):
        line_form = Form(
            self.env["sale.order.line"],
            view="sale_order_line_input.view_sales_order_line_input_tree",
        )
        line_form.order_partner_id = self.partner
        line_form.product_id = self.product
        line_form.price_unit = 190.50
        line_form.product_uom = self.env.ref("uom.product_uom_unit")
        line_form.product_uom_qty = 8.0
        line_form.name = "Test line description"
        line = line_form.save()
        self.assertTrue(line.order_id)
        action_dict = line.action_sale_order_form()
        self.assertEquals(action_dict["res_id"], line.order_id.id)
        self.assertEquals(action_dict["res_model"], "sale.order")
