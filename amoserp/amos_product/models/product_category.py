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

from odoo.exceptions import AccessDenied, AccessError, UserError, ValidationError
from odoo import _, api, fields, models, modules, tools

class product_category(models.Model):
    _name = "product.category"
    _description = "产品分类"
    _parent_name = "parent_id"
    _parent_store = True
    _rec_name = 'complete_name'
    _order = 'complete_name'

    name = fields.Char('名称', index=True, required=True)
    code = fields.Char(u'产品编码')
    complete_name = fields.Char('产品分类全称', compute='_compute_complete_name',store=True)
    complete_code = fields.Char(u'产品分类编号全称',compute='_compute_complete_name', store=True)
    parent_id = fields.Many2one('product.category', '上级菜单', index=True, ondelete='cascade')
    parent_path = fields.Char(index=True)
    child_id = fields.One2many('product.category', 'parent_id', '下级菜单')
    product_count = fields.Integer('产品个数', compute='_compute_product_count',)
    parent_left = fields.Integer(string=u'左')
    parent_right = fields.Integer(string=u'右')
    sequence = fields.Integer(string=u'排序', default=10)

    @api.depends('name', 'parent_id.complete_name','code', 'parent_id.complete_code')
    def _compute_complete_name(self):
        for category in self:
            if category.parent_id:
                category.complete_name = '%s / %s' % (category.parent_id.complete_name, category.name)
                category.complete_code = '%s%s' % (category.parent_id.complete_code or '', category.code or '')
            else:
                category.complete_name = category.name or ''
                category.complete_code = category.code or ''

    def _compute_product_count(self):
        read_group_res = self.env['product.product'].read_group([('categ_id', 'child_of', self.ids)], ['categ_id'], ['categ_id'])
        group_data = dict((data['categ_id'][0], data['categ_id_count']) for data in read_group_res)
        for categ in self:
            product_count = 0
            for sub_categ_id in categ.search([('id', 'child_of', categ.ids)]).ids:
                product_count += group_data.get(sub_categ_id, 0)
            categ.product_count = product_count

    @api.constrains('parent_id')
    def _check_category_recursion(self):
        if not self._check_recursion():
            raise ValidationError(_('You cannot create recursive categories.'))
        return True

    @api.model
    def name_create(self, name):
        return self.create({'name': name}).name_get()[0]

