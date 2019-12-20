# -*- coding: utf-8 -*-
# &&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&
# Odoo Connector
# QQ:35350428
# 邮件:35350428@qq.com
# 手机：13584935775
# 作者：'amos'
# 公司网址： www.odoo.pw  www.100china.cn  http://i.youku.com/amoserp
# Copyright 昆山一百计算机有限公司 2012-2018 Amos
# 日期：2018/12/19
# &&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&

from collections import namedtuple
import json
import time

from odoo import api, fields, models, _
from odoo.tools import DEFAULT_SERVER_DATETIME_FORMAT

MOVE_LINE_TYPE = [
    ('out', u'出库'),
    ('in', u'入库'),
    ('other', u'调拨'),
]




class res_col(models.Model):
    _name = "res.col"
    _description = "仓库单据分栏"

    name = fields.Char('名称', required=True)
    sequence = fields.Integer(string=u'排序', default=10)


class stock_picking_type(models.Model):
    _name = "stock.picking.type"
    _description = "单据类型"
    _order = 'sequence, id'
    _rec_name = 'complete_name'

    name = fields.Char('单据名称', required=True)
    complete_name = fields.Char(u'别名')
    color = fields.Integer('颜色')
    sequence = fields.Integer('排序')

    col_id = fields.Many2one('res.col', '分栏')

    view_group = fields.Selection([
        (u'其它出入库', u'其它出入库'),
        (u'出入库', u'出入库'),
        (u'借出类', u'借出类'),
        (u'盘点', u'盘点'),
        (u'其它', u'其它'),
    ], string=u'分组')

    type = fields.Selection(MOVE_LINE_TYPE, u'类型', default='other')
    sequence_id = fields.Many2one('ir.sequence', u'编号规则')
    default_location_src_id = fields.Many2one('stock.location', '默认源位置', )
    default_location_dest_id = fields.Many2one('stock.location', '默认目的位置', )
    code = fields.Selection([
        ('incoming', '供应商'),
        ('outgoing', '客户'),
        ('internal', '内部')],
        '作业的类型', required=True)
    return_picking_type_id = fields.Many2one('stock.picking.type', '退回的作业类型')
    show_entire_packs = fields.Boolean('移动整个包')
    warehouse_id = fields.Many2one(
        'stock.warehouse', '仓库', ondelete='cascade',
        default=lambda self: self.env['stock.warehouse'].search([('company_id', '=', self.env.user.company_id.id)],
                                                                limit=1))
    active = fields.Boolean('是否有效', default=True)
    use_create_lots = fields.Boolean('创建新批次/序列号码', default=True, )
    use_existing_lots = fields.Boolean('使用已有批次/序列号码', default=True, )
    show_operations = fields.Boolean('显示详细作业', default=False, )
    show_reserved = fields.Boolean('显示预留', default=True, )

    # Statistics for the kanban view
    last_done_picking = fields.Char('最近10笔完成的拣货', compute='_compute_last_done_picking')
    count_picking_draft = fields.Integer(compute='_compute_picking_count') #新建
    count_picking_waiting = fields.Integer(compute='_compute_picking_count')#等待部门审批
    count_picking_admin = fields.Integer(compute='_compute_picking_count')#等待仓库确认
    count_picking_late = fields.Integer(compute='_compute_picking_count')#已过时的单据
    barcode = fields.Char('条码', copy=False)

    user_id = fields.Many2one('res.users', string=u'负责人', index=True, track_visibility='onchange',
                              default=lambda self: self.env.user,)
    is_qty = fields.Boolean(default=False, string=u'是否检查库存', track_visibility='onchange',help=u'如果打勾查询库存数量少于库存禁止出库',)


    def _compute_last_done_picking(self):
        # TDE TODO: true multi
        tristates = []
        for picking in self.env['stock.picking'].search([('picking_type_id', '=', self.id), ('state', '=', '已完成')],
                                                        order='date_done desc', limit=10):
            if picking.date_done > picking.date:
                tristates.insert(0, {'tooltip': picking.name or '' + ": " + _('Late'), 'value': -1})
            elif picking.backorder_id:
                tristates.insert(0, {'tooltip': picking.name or '' + ": " + _('Backorder exists'), 'value': 0})
            else:
                tristates.insert(0, {'tooltip': picking.name or '' + ": " + _('OK'), 'value': 1})
        self.last_done_picking = json.dumps(tristates)

    def _compute_picking_count(self):
        # TDE TODO count picking can be done using previous two
        domains = {
            'count_picking_draft': [('state', '=', '新建')],
            'count_picking_waiting': [('state', '=', '待审批')],
            'count_picking_admin': [('state', '=', '仓库')],
            'count_picking_late': [('scheduled_date', '<', time.strftime(DEFAULT_SERVER_DATETIME_FORMAT)),
                                   ('state', '=', '已完成')],
        }
        for field in domains:
            data = self.env['stock.picking'].read_group(domains[field] +
                                                        [('state', 'not in', ('已完成',)),
                                                         ('picking_type_id', 'in', self.ids)],
                                                        ['picking_type_id'], ['picking_type_id'])
            count = {
                x['picking_type_id'][0]: x['picking_type_id_count']
                for x in data if x['picking_type_id']
            }
            for record in self:
                record[field] = count.get(record.id, 0)

    def name_get(self):
        res = []
        for picking_type in self:
            if self.env.context.get('special_shortened_wh_name'):
                if picking_type.warehouse_id:
                    name = picking_type.warehouse_id.name
                else:
                    name = '客户' + ' (' + picking_type.name + ')'
            elif picking_type.warehouse_id:
                name = picking_type.warehouse_id.name + ': ' + picking_type.name
            else:
                name = picking_type.name
            res.append((picking_type.id, name))
        return res

    @api.model
    def _name_search(self, name, args=None, operator='ilike', limit=100, name_get_uid=None):
        args = args or []
        domain = []
        if name:
            domain = ['|', ('name', operator, name), ('warehouse_id.name', operator, name)]
        picking_ids = self._search(domain + args, limit=limit, access_rights_uid=name_get_uid)
        return self.browse(picking_ids).name_get()

    @api.onchange('code')
    def onchange_picking_code(self):
        pass
        # if self.code == 'incoming':
        #     self.default_location_src_id = self.env.ref('stock.stock_location_suppliers').id
        #     self.default_location_dest_id = self.env.ref('stock.stock_location_stock').id
        # elif self.code == 'outgoing':
        #     self.default_location_src_id = self.env.ref('stock.stock_location_stock').id
        #     self.default_location_dest_id = self.env.ref('stock.stock_location_customers').id

    @api.onchange('show_operations')
    def onchange_show_operations(self):
        if self.show_operations is True:
            self.show_reserved = True

    def _get_action(self, action_xmlid):
        action = self.env.ref(action_xmlid).read()[0]
        if self:
            action['display_name'] = self.display_name
        return action

    # def get_action_picking_tree_late(self):
    #     return self._get_action('amos_stock.action_picking_tree_late')
    #
    # def get_action_picking_tree_backorder(self):
    #     return self._get_action('amos_stock.action_picking_tree_backorder')



    def get_stock_picking_all(self):
        """
        判断用户单据类型用来显示不同的列表字段与表单字段
        :return:
        """
        self.ensure_one()
        context = {}


        if self.name == '盘点单':
            return self._get_action('amos_stock.odoo_stock_picking_inventory_actions')

        if self.name == '盘亏单':
            return self._get_action('amos_stock.odoo_stock_picking_losses_actions')

        if self.name == '盘盈单':
            return self._get_action('amos_stock.odoo_stock_picking_overage_actions')

        if self.name == '丢失单':
            return self._get_action('amos_stock.odoo_stock_picking_lose_actions')

        if self.name == '退料单':
            return self._get_action('amos_stock.odoo_stock_picking_return_actions')

        if self.name == '领用单':
            return self._get_action('amos_stock.odoo_stock_picking_out_actions')

        if self.name == '入库单':
            return self._get_action('amos_stock.odoo_stock_picking_in_actions')

        if self.name == '送检单':
            return self._get_action('amos_stock.odoo_stock_picking_tested_out_actions')

        if self.name == '送检还入单':
            return self._get_action('amos_stock.odoo_stock_picking_tested_in_actions')

        if self.name == '报废单':
            return self._get_action('amos_stock.odoo_stock_picking_scrap_actions')

        if self.name == '其它入库单':
            return self._get_action('amos_stock.amos_actions_stock_picking_1')

        if self.name == '其它出库单':
            return self._get_action('amos_stock.odoo_stock_picking_out_other_actions')

        if self.name == '借出单':
            return self._get_action('amos_stock.odoo_stock_lend_out_actions')

            context['search_default_picking_type_id'] = self.id
            context['default_picking_type_id'] = self.id
            context['contact_display'] = 'partner_address'
            # context['search_default_draft1'] = '1'
            search_view_ref = self.env.ref('amos_stock.odoo_stock_lend_out_search', False)
            tree_view_ref = self.env.ref('amos_stock.odoo_stock_lend_out_tree', False)
            form_view_ref = self.env.ref('amos_stock.odoo_stock_lend_out_form', False)

            return {
                'domain': [('picking_type_id', '=', self.id)],
                'name': self.name,
                'res_model': 'stock.picking',
                'type': 'ir.actions.act_window',
                'views': [
                    (tree_view_ref.id, 'tree'),
                    (form_view_ref.id, 'form')],
                'search_view_id': search_view_ref and search_view_ref.id,
                'target': 'current',
                'context': context,
                'flags': {'form': {'action_buttons': False}}
            }
        if self.name == '借出还入单':
            return self._get_action('amos_stock.odoo_stock_lend_out_in_actions')
            context['search_default_picking_type_id'] = self.id
            context['default_picking_type_id'] = self.id
            context['contact_display'] = 'partner_address'
            # context['search_default_draft1'] = '1'
            search_view_ref = self.env.ref('amos_stock.odoo_stock_lend_out_in_search', False)
            tree_view_ref = self.env.ref('amos_stock.odoo_stock_lend_out_in_tree', False)
            form_view_ref = self.env.ref('amos_stock.odoo_stock_lend_out_in_form', False)

            return {
                'domain': [('picking_type_id', '=', self.id)],
                'name': self.name,
                'res_model': 'stock.picking',
                'type': 'ir.actions.act_window',
                'views': [
                    (tree_view_ref.id, 'tree'),
                    (form_view_ref.id, 'form')],
                'search_view_id': search_view_ref and search_view_ref.id,
                'target': 'current',
                'context': context,
                'flags': {'form': {'action_buttons': False}}
            }

        return self._get_action('amos_stock.stock_picking_all')


    def get_action_picking_tree_draft3(self):
        return self._get_action('amos_stock.action_picking_tree_draft3')

    def get_action_picking_tree_draft4(self):
        return self._get_action('amos_stock.action_picking_tree_draft4')

    def get_action_picking_tree_state1(self):

        if self.name == '入库单':
            return self._get_action('amos_stock.odoo_stock_picking_in_actions_state1')
        if self.name == '领用单':
            return self._get_action('amos_stock.odoo_stock_picking_out_actions_state1')
        if self.name == '送检单':
            return self._get_action('amos_stock.odoo_stock_picking_tested_out_actions_state1')
        if self.name == '送检还入单':
            return self._get_action('amos_stock.odoo_stock_picking_tested_in_actions_state1')
        if self.name == '盘点单':
            return self._get_action('amos_stock.odoo_stock_picking_inventory_actions_state1')
        if self.name == '盘盈单':
            return self._get_action('amos_stock.odoo_stock_picking_overage_actions_state1')
        if self.name == '盘亏单':
            return self._get_action('amos_stock.odoo_stock_picking_losses_actions_state1')


        if self.name == '借出单':
            return self._get_action('amos_stock.odoo_stock_lend_out_actions_state1')
        if self.name == '借出还入单':
            return self._get_action('amos_stock.odoo_stock_lend_out_in_actions_state1')
        if self.name == '其它入库单':
            return self._get_action('amos_stock.odoo_stock_picking_in_other_actions_state1')
        if self.name == '其它出库单':
            return self._get_action('amos_stock.odoo_stock_picking_out_other_actions_state1')
        if self.name == '退料单':
            return self._get_action('amos_stock.odoo_stock_picking_return_actions_state1')
        if self.name == '报废单':
            return self._get_action('amos_stock.odoo_stock_picking_scrap_actions_state1')
        if self.name == '丢失单':
            return self._get_action('amos_stock.odoo_stock_picking_lose_actions_state1')

        return self._get_action('amos_stock.action_picking_tree_1')

    def get_action_picking_tree_state2(self):
        if self.name == '入库单':
            return self._get_action('amos_stock.odoo_stock_picking_in_actions_state2')
        if self.name == '领用单':
            return self._get_action('amos_stock.odoo_stock_picking_out_actions_state2')
        if self.name == '送检单':
            return self._get_action('amos_stock.odoo_stock_picking_tested_out_actions_state2')
        if self.name == '送检还入单':
            return self._get_action('amos_stock.odoo_stock_picking_tested_in_actions_view2')
        if self.name == '盘点单':
            return self._get_action('amos_stock.odoo_stock_picking_inventory_actions_state2')
        if self.name == '盘盈单':
            return self._get_action('amos_stock.odoo_stock_picking_overage_actions_state2')
        if self.name == '盘亏单':
            return self._get_action('amos_stock.odoo_stock_picking_losses_actions_state2')

        if self.name == '借出单':
            return self._get_action('amos_stock.odoo_stock_lend_out_actions_state2')
        if self.name == '借出还入单':
            return self._get_action('amos_stock.odoo_stock_lend_out_in_actions_state2')
        if self.name == '其它入库单':
            return self._get_action('amos_stock.odoo_stock_picking_in_other_actions_state2')
        if self.name == '其它出库单':
            return self._get_action('amos_stock.odoo_stock_picking_out_other_actions_state2')
        if self.name == '退料单':
            return self._get_action('amos_stock.odoo_stock_picking_return_actions_state2')
        if self.name == '报废单':
            return self._get_action('amos_stock.odoo_stock_picking_scrap_actions_state2')
        if self.name == '丢失单':
            return self._get_action('amos_stock.odoo_stock_picking_lose_actions_state2')

        return self._get_action('amos_stock.action_picking_tree_2')

    def get_action_picking_tree_state3(self):
        if self.name == '入库单':
            return self._get_action('amos_stock.odoo_stock_picking_in_actions_state3')
        if self.name == '领用单':
            return self._get_action('amos_stock.odoo_stock_picking_out_actions_state3')
        if self.name == '送检单':
            return self._get_action('amos_stock.odoo_stock_picking_tested_out_actions_state3')
        if self.name == '送检还入单':
            return self._get_action('amos_stock.odoo_stock_picking_tested_in_actions_state3')
        if self.name == '盘点单':
            return self._get_action('amos_stock.odoo_stock_picking_inventory_actions_state3')
        if self.name == '盘盈':
            return self._get_action('amos_stock.odoo_stock_picking_overage_actions_state3')
        if self.name == '盘亏':
            return self._get_action('amos_stock.odoo_stock_picking_losses_actions_state3')

        if self.name == '借出单':
            return self._get_action('amos_stock.odoo_stock_lend_out_actions_state3')
        if self.name == '借出还入单':
            return self._get_action('amos_stock.odoo_stock_lend_out_in_actions_state3')
        if self.name == '其它入库单':
            return self._get_action('amos_stock.odoo_stock_picking_in_other_actions_state3')
        if self.name == '其它出库单':
            return self._get_action('amos_stock.odoo_stock_picking_out_other_actions_state3')
        if self.name == '退料单':
            return self._get_action('amos_stock.odoo_stock_picking_return_actions_state3')
        if self.name == '报废单':
            return self._get_action('amos_stock.odoo_stock_picking_scrap_actions_state3')
        if self.name == '丢失单':
            return self._get_action('amos_stock.odoo_stock_picking_lose_actions_state3')

        return self._get_action('amos_stock.action_picking_tree_3')



    def get_action_picking_tree_state4(self):
        if self.name == '入库单':
            return self._get_action('amos_stock.odoo_stock_picking_in_actions_state4')
        if self.name == '领用单':
            return self._get_action('amos_stock.odoo_stock_picking_out_actions_state4')
        if self.name == '送检单':
            return self._get_action('amos_stock.odoo_stock_picking_tested_out_actions_state4')
        if self.name == '送检还入单':
            return self._get_action('amos_stock.odoo_stock_picking_tested_in_actions_view4')
        if self.name == '盘点单':
            return self._get_action('amos_stock.odoo_stock_picking_inventory_actions_state4')
        if self.name == '盘盈':
            return self._get_action('amos_stock.odoo_stock_picking_overage_actions_state4')
        if self.name == '盘亏':
            return self._get_action('amos_stock.odoo_stock_picking_losses_actions_state4')

        if self.name == '借出单':
            return self._get_action('amos_stock.odoo_stock_lend_out_actions_state4')
        if self.name == '借出还入单':
            return self._get_action('amos_stock.odoo_stock_lend_out_in_actions_state4')
        if self.name == '其它入库单':
            return self._get_action('amos_stock.odoo_stock_picking_in_other_actions_state4')
        if self.name == '其它出库单':
            return self._get_action('amos_stock.odoo_stock_picking_out_other_actions_state4')
        if self.name == '退料单':
            return self._get_action('amos_stock.odoo_stock_picking_return_actions_state4')
        if self.name == '报废单':
            return self._get_action('amos_stock.odoo_stock_picking_scrap_actions_state4')
        if self.name == '丢失单':
            return self._get_action('amos_stock.odoo_stock_picking_lose_actions_state4')

        return self._get_action('amos_stock.action_picking_tree_4')