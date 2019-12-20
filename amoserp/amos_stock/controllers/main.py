# -*- coding: utf-8 -*-
# &&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&
# Odoo Connector
# QQ:35350428
# 邮件:sale@100china.cn
# 手机：13584935775
# 作者：'odoo'
# 公司网址： www.odoo.pw  www.100china.cn
# Copyright 昆山一百计算机有限公司 2012-2016 Amos
# 日期：2014-06-18
# &&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&
import os
import odoo
from odoo import http, fields, _
from odoo.http import request
from jinja2 import Environment, FileSystemLoader
from . import jinja_filters
from odoo.exceptions import AccessError
import werkzeug
from werkzeug import url_encode
from odoo.tools import consteq, pycompat
from datetime import datetime, timedelta

BASE_DIR = os.path.dirname(os.path.dirname(__file__))
templateLoader = FileSystemLoader(searchpath=BASE_DIR + "/templates")
env = Environment(loader=templateLoader)
env.filters['date_format'] = jinja_filters.date_format


class Website_Report(http.Controller):
    @http.route(['/report/inout/<int:id>', '/report/inout/<int:id>/<int:warehouse_id>'], type='http',
                auth="none", csrf=False)
    def report_inout(self, id, warehouse_id=None, **kwargs):
        cr, uid, context, pool = request.cr, odoo.SUPERUSER_ID, request.context, request.env
        values = {}
        obj_move = pool['stock.move']

        if warehouse_id == None:
            product = obj_move.sudo().search([('product_id', '=', id), ('state', '=', '已完成')],
                                             order='id asc')
        else:
            product = obj_move.sudo().search(
                [('product_id', '=', id), ('warehouse_id', '=', warehouse_id), ('state', '=', '已完成')], order='id asc')
        tr = ''
        style_class = 'gradeA'
        qty = 0.00
        for obj in product:

            if obj.type == 'other':
                if obj.picking_type_id_name != '丢失单':
                    continue


            if style_class == 'gradeA':
                style_class = 'gradeC'
            else:
                style_class = 'gradeA'

            direction = ''
            if obj.type == 'in':
                qty += obj.product_uom_qty
                direction = '<font color="#FF0000">+</font> '
            elif obj.type == 'out':
                qty += -obj.product_uom_qty
                direction = '<font color="#51c350">-</font> '
            elif obj.type == 'other':
                direction = '<font color="#FF0000">不计算</font> '

            date_datetime =obj.date_done.strftime("%Y-%m-%d %H:%M")

            tr += """

                        <tr class="%s">
                            <td>%s</td>
                            <td>%s</td>
                            <td>%s</td>
                            <td>%s</td>
                            <td>%s</td>
                            <td>%s</td>
                            <td>%s</td>
                            <td>%s</td>
                            <td>%s</td>
                            <td class="center">%s</td>
                            <td class="center">%s</td>
                        </tr>
            """ % (style_class,
                   date_datetime,
                   obj.product_id.default_code,
                   obj.product_id.name,
                   obj.product_id.specification or '',
                   obj.product_uom.name,
                   obj.warehouse_id.name,
                   obj.picking_id.create_uid.name,
                   obj.picking_type_id_name,
                   direction,
                   obj.product_uom_qty,
                   qty
                   )
        values['tr'] = tr

        template = env.get_template('report/zh_CN/inout.html')
        html = template.render(object=values)
        return html
