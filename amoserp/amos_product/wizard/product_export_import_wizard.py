# -*- coding: utf-8 -*-
# &&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&
# AmosERP odoo11.0
# QQ:35350428
# 邮件:35350428@qq.com
# 手机：13584935775
# 作者：'amos'
# 公司网址： www.odoo.pw  www.100china.cn www.100china.cn
# Copyright 昆山一百计算机有限公司 2012-2018 Amos
# 日期：2018/09/12 15:01
# &&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&

import os
import base64
from odoo import api, fields, models, tools, SUPERUSER_ID, _
from odoo.exceptions import AccessDenied, AccessError, UserError, ValidationError
import xlrd
import logging

_logger = logging.getLogger(__name__)
import datetime
import sys
import string

default_encoding = 'utf-8'
if sys.getdefaultencoding() != default_encoding:
    reload(sys)
    sys.setdefaultencoding(default_encoding)


class product_export_import_wizard(models.TransientModel):
    _name = "product.export.import.wizard"
    _description = u"产品导入"

    files = fields.Binary(u'文件', filters='*.xlsx', required=True)

    def import_product(self):
        ono_orders = self.files
        excel = xlrd.open_workbook(file_contents=base64.decodestring(ono_orders))
        sh = excel.sheet_by_index(0)
        product_export = self.env['product.product']
        cell_values = sh._cell_values

        for rx in range(sh.nrows):
            if rx == 0: continue
            default_code = cell_values[rx][0] or ''
            name = cell_values[rx][1] or ''
            specification = cell_values[rx][2] or ''
            categ = cell_values[rx][3] or ''
            uom = cell_values[rx][4] or ''
            list_price = cell_values[rx][5] or 0.00
            public_price = cell_values[rx][6] or 0.00
            #::::分类
            categ_id = False
            if categ:
                rec = self.env['product.category'].search([('name', '=', categ)], limit=1)
                if not rec:
                    line = {
                        'name': categ,
                    }
                    categ_id = self.env['product.category'].create(line).id
                else:
                    categ_id = rec.id
            #::::单位
            # uom_id = False
            # if uom:
            #     rec = self.env['product.uom'].search([('name', '=', uom)], limit=1)
            #     if not rec:
            #         line = {
            #             'name': uom,
            #         }
            #         uom_id = self.env['product.uom'].create(line).id
            #     else:
            #         uom_id = rec.id

            if len(str(default_code)) == 0:
                raise UserError(u"产品编号不存在！第[%d]行" % (rx + 1))
            else:
                product_id = product_export.search([('default_code', '=', default_code.upper())])
                if len(product_id) > 0:
                    raise UserError(u"产品编号已存在！第[%d]行" % (rx + 1))
                else:
                    line = {
                        'default_code': str(default_code.upper()),
                        'name': name,
                        'specification': specification,
                        'categ_id': categ_id,
                        'uom_id': uom,
                        'list_price': list_price,
                        'public_price': public_price,
                    }
                    product = product_export.create(line)

                    product.button_done()

        return True
        # vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
