# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from datetime import datetime
from dateutil import relativedelta
from odoo.exceptions import UserError

from odoo import api, fields, models, _
from odoo.tools import DEFAULT_SERVER_DATETIME_FORMAT


class stock_location(models.Model):
    _name = "stock.location"
    _description = "储位管理"
    _parent_name = "location_id"
    _parent_store = True
    _order = 'complete_name'
    _rec_name = 'complete_name'

    @api.model
    def default_get(self, fields):
        res = super(stock_location, self).default_get(fields)
        if 'barcode' in fields and 'barcode' not in res and res.get('complete_name'):
            res['barcode'] = res['complete_name']
        return res

    name = fields.Char('位置名称', required=True)
    complete_name = fields.Char("全称", compute='_compute_complete_name', store=True)
    active = fields.Boolean('Active', default=True)
    usage = fields.Selection([
        ('supplier', '供应商位置'),
        ('view', '视图'),
        ('internal', '内部位置'),
        ('customer', '客户位置'),
        ('inventory', '库存损失'),
        ('procurement', '补货'),
        ('transit', '中转')], string='位置类型',
        default='internal', index=True, required=True)
    location_id = fields.Many2one(
        'stock.location', '上级位置', index=True, ondelete='cascade', )
    child_ids = fields.One2many('stock.location', 'location_id', 'Contains')
    partner_id = fields.Many2one('res.partner', '所有者', help="Owner of the location if not internal")
    comment = fields.Text('附加信息')
    posx = fields.Integer('通道(X)', default=0)
    posy = fields.Integer('货架(Y)', default=0)
    posz = fields.Integer('高度(Z)', default=0)
    parent_path = fields.Char(index=True)
    company_id = fields.Many2one(
        'res.company', '公司',
        default=lambda self: self.env['res.company']._company_default_get('stock.location'), index=True, )
    scrap_location = fields.Boolean('是一个报废位置？', default=False)
    return_location = fields.Boolean('是一个退回位置？')
    barcode = fields.Char('条码', copy=False, oldname='loc_barcode')

    _sql_constraints = [('barcode_company_uniq', 'unique (barcode,company_id)', '每个公司的位置条形码必须是唯一的 !')]


    @api.depends('name', 'location_id.complete_name')
    def _compute_complete_name(self):
        """ Forms complete name of location from parent location to child location. """
        if self.location_id.complete_name:
            self.complete_name = '%s/%s' % (self.location_id.complete_name, self.name)
        else:
            self.complete_name = self.name

    def write(self, values):
        if 'usage' in values and values['usage'] == 'view':
            pass

        return super(stock_location, self).write(values)

    def name_get(self):
        ret_list = []
        for location in self:
            orig_location = location
            name = location.name
            while location.location_id and location.usage != 'view':
                location = location.location_id
                if not name:
                    raise UserError(_('You have to set a name for this location.'))
                name = location.name + "/" + name
            ret_list.append((orig_location.id, name))
        return ret_list

    @api.model
    def _name_search(self, name, args=None, operator='ilike', limit=100, name_get_uid=None):
        """ search full name and barcode """
        if args is None:
            args = []
        location_ids = self._search(['|', ('barcode', operator, name), ('complete_name', operator, name)] + args, limit=limit, access_rights_uid=name_get_uid)
        return self.browse(location_ids).name_get()

    def get_putaway_strategy(self, product):
        ''' Returns the location where the product has to be put, if any compliant putaway strategy is found. Otherwise returns None.'''
        current_location = self
        putaway_location = self.env['stock.location']
        while current_location and not putaway_location:
            if current_location.putaway_strategy_id:
                putaway_location = current_location.putaway_strategy_id.putaway_apply(product)
            current_location = current_location.location_id
        return putaway_location

    @api.returns('stock.warehouse', lambda value: value.id)
    def get_warehouse(self):
        """ Returns warehouse id of warehouse that contains location """
        domain = [('view_location_id', 'parent_of', self.ids)]
        return self.env['stock.warehouse'].search(domain, limit=1)

    def should_bypass_reservation(self):
        self.ensure_one()
        return self.usage in ('supplier', 'customer', 'inventory', 'production') or self.scrap_location


