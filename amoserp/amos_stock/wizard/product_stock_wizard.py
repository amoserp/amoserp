# -*- coding: utf-8 -*-
# &&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&
# Odoo Connector
# QQ:35350428
# 邮件:sale@100china.cn
# 手机：13584935775
# 作者：'amos'
# 公司网址： www.odoo.pw  www.100china.cn
# Copyright 昆山一百计算机有限公司 2012-2016 Amos
# 日期：2014-06-18
# &&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&

from odoo import api, fields, models, tools, SUPERUSER_ID, _
from odoo.exceptions import AccessDenied, AccessError, UserError, ValidationError

class product_stock_wizard(models.TransientModel):
    _name = 'product.stock.wizard'
    _description = u'生成物资库位'

    name = fields.Char(string=u'编号')

    def action_batch(self):

        stock_warehouse_obj = self.env['stock.warehouse']
        product_stock_obj = self.env['product.stock']
        product_obj = self.env['product.product']
        obj_array = stock_warehouse_obj.search([])
        product = product_obj.search([])

        for o in product:
            for oo in obj_array:

                self._cr.execute(
                    "SELECT count(*) FROM product_stock WHERE product_id ='%s' and company_id ='%s' and warehouse_id ='%s' " % (
                    o.id, oo.company_id.id, oo.id))
                lines = self._cr.fetchall()
                if long(lines[0][0]) == 0:
                    pram = {
                        'name': o.id,
                        'warehouse_id': oo.id,
                        'company_id': oo.company_id.id,
                        'uom_id': o.uom_id,
                    }
                    product_stock_obj.create(pram)


