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

from odoo import api, fields, models, tools, SUPERUSER_ID, _
from odoo.exceptions import AccessDenied, AccessError, UserError, ValidationError
from odoo.osv import expression
from datetime import datetime, timedelta
import json
from lxml import etree

class stock_picking_scrap(models.Model):
    _name = "stock.picking.scrap"
    _inherit = 'stock.picking'
    _table = "stock_picking"
    _description = u"报废单"





class stock_move(models.Model):
    _inherit = "stock.move"

    @api.model
    def _get_default_scrap_warehouse_id(self):

        records = self.env['stock.warehouse'].sudo().search([('name', '=', self._context['initial']),('company_id', '=', self._context['company_id'])], order="id desc",  limit=1)

        return records.id or False

    f_scrap_warehouse_id = fields.Many2one('stock.warehouse', u'从仓库')
    t_scrap_warehouse_id = fields.Many2one('stock.warehouse', u'到仓库',  default=_get_default_scrap_warehouse_id)



