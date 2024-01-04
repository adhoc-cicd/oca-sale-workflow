# Copyright 2018-2020 Tecnativa - Carlos Dauden
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
from odoo.tests import Form, TransactionCase, tagged


@tagged("post_install", "-at_install")
class TestSaleOrderSecondaryUnit(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.product_uom_kg = cls.env.ref("uom.product_uom_kgm")
        cls.product_uom_gram = cls.env.ref("uom.product_uom_gram")
        cls.product_uom_unit = cls.env.ref("uom.product_uom_unit")
        cls.price_list = cls.env["product.pricelist"].create(
            {"name": "price list for test"}
        )
        cls.product = cls.env["product.product"].create(
            {
                "name": "test",
                "uom_id": cls.product_uom_kg.id,
                "uom_po_id": cls.product_uom_kg.id,
            }
        )
        # Set secondary uom on product template
        cls.product.product_tmpl_id.write(
            {
                "secondary_uom_ids": [
                    (
                        0,
                        0,
                        {
                            "name": "unit-500",
                            "uom_id": cls.product_uom_unit.id,
                            "factor": 0.5,
                        },
                    )
                ],
            }
        )
        cls.secondary_unit = cls.env["product.secondary.unit"].search(
            [("product_tmpl_id", "=", cls.product.product_tmpl_id.id)]
        )
        cls.product.sale_secondary_uom_id = cls.secondary_unit.id
        cls.partner = cls.env["res.partner"].create({"name": "test - partner"})
        with Form(cls.env["sale.order"]) as order_form:
            order_form.partner_id = cls.partner
            order_form.pricelist_id = cls.price_list
            with order_form.order_line.new() as line_form:
                line_form.product_id = cls.product
                line_form.product_uom_qty = 1
                line_form.price_unit = 1000.00
        cls.order = order_form.save()

    def test_onchange_secondary_uom(self):
        self.order.order_line.write(
            {"secondary_uom_id": self.secondary_unit.id, "secondary_uom_qty": 5}
        )
        self.order.order_line._compute_product_uom_qty()
        self.assertEqual(self.order.order_line.product_uom_qty, 2.5)

    def test_onchange_secondary_unit_product_uom_qty(self):
        self.order.order_line.update(
            {"secondary_uom_id": self.secondary_unit.id, "product_uom_qty": 3.5}
        )
        self.assertEqual(self.order.order_line.secondary_uom_qty, 7.0)

    def test_default_secondary_unit(self):
        self.order.order_line._onchange_product_id_warning()
        self.assertEqual(self.order.order_line.secondary_uom_id, self.secondary_unit)

    def test_onchange_order_product_uom(self):
        self.order.order_line.update(
            {
                "secondary_uom_id": self.secondary_unit.id,
                "product_uom": self.product_uom_gram.id,
                "product_uom_qty": 3500.00,
            }
        )
        self.assertEqual(self.order.order_line.secondary_uom_qty, 7.0)

    def test_independent_type(self):
        # dependent type is already tested as dependency_type by default
        self.order.order_line.secondary_uom_id = self.secondary_unit.id
        self.order.order_line.secondary_uom_id.write({"dependency_type": "independent"})

        # Remember previous UoM quantity for avoiding interactions with other modules
        previous_uom_qty = self.order.order_line.product_uom_qty
        self.order.order_line.write({"secondary_uom_qty": 2})
        self.assertEqual(self.order.order_line.product_uom_qty, previous_uom_qty)
        self.assertEqual(self.order.order_line.secondary_uom_qty, 2)

        self.order.order_line.write({"product_uom_qty": 17})
        self.assertEqual(self.order.order_line.secondary_uom_qty, 2)
        self.assertEqual(self.order.order_line.product_uom_qty, 17)

    def test_secondary_uom_unit_price(self):
        # Remove secondary uom in sale line to do a complete test of secondary price
        self.assertEqual(self.order.order_line.price_unit, 1000)
        self.order.order_line.secondary_uom_id = False
        self.assertEqual(self.order.order_line.price_unit, 1)
        self.assertEqual(self.order.order_line.secondary_uom_unit_price, 0)
        self.order.order_line.update(
            {"secondary_uom_id": self.secondary_unit.id, "product_uom_qty": 2}
        )

        self.assertEqual(self.order.order_line.secondary_uom_qty, 4)
        self.assertEqual(self.order.order_line.secondary_uom_unit_price, 0.5)

        self.order.order_line.write({"product_uom_qty": 8})
        self.assertEqual(self.order.order_line.secondary_uom_qty, 16)
        self.assertEqual(self.order.order_line.secondary_uom_unit_price, 0.5)
        self.assertEqual(self.order.order_line.price_subtotal, 8)

    def test_packaging_enabled(self):
        """Make sure module is compatible with packaging feature."""
        self.env.user.groups_id |= self.env.ref("product.group_stock_packaging")
        with Form(self.product.product_tmpl_id) as product_f:
            with product_f.packaging_ids.new() as packaging_f:
                packaging_f.name = "dozen"
                packaging_f.qty = 12
                packaging_f.sales = True
        packaging = self.product.product_tmpl_id.packaging_ids
        with Form(self.order) as order_f:
            with order_f.order_line.edit(0) as line_f:
                # Line stays as it was
                self.assertEqual(line_f.price_unit, 1000)
                self.assertEqual(line_f.product_uom_qty, 1)
                self.assertEqual(line_f.secondary_uom_id, self.secondary_unit)
                self.assertEqual(line_f.secondary_uom_qty, 2)
                self.assertFalse(line_f.product_packaging_id)
                self.assertFalse(line_f.product_packaging_qty)
                # We sell 1 dozen by setting the packaging
                line_f.product_packaging_id = packaging
                line_f.product_packaging_qty = 1
                self.assertEqual(line_f.price_unit, 1)
                self.assertEqual(line_f.product_uom_qty, 12)
                self.assertEqual(line_f.secondary_uom_id, self.secondary_unit)
                self.assertEqual(line_f.secondary_uom_qty, 24)
                # We sell 2 dozens by setting the packaging
                line_f.product_packaging_qty = 2
                self.assertEqual(line_f.price_unit, 1)
                self.assertEqual(line_f.product_uom_qty, 24)
                self.assertEqual(line_f.secondary_uom_qty, 48)
                # We sell 1 dozen by setting the secondary unit qty
                line_f.secondary_uom_qty = 24
                self.assertEqual(line_f.price_unit, 1)
                self.assertEqual(line_f.product_uom_qty, 12)
                self.assertEqual(line_f.product_packaging_qty, 1)
                # We sell 2 dozens by setting the primary unit qty
                line_f.product_uom_qty = 24
                self.assertEqual(line_f.price_unit, 1)
                self.assertEqual(line_f.secondary_uom_qty, 48)
                self.assertEqual(line_f.product_packaging_qty, 2)
