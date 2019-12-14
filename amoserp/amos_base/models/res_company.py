# -*- coding: utf-8 -*-
# &&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&
# AmosERP odoo11.0
# QQ:35350428
# 邮件:35350428@qq.com
# 手机：13584935775
# 作者：'odoo'
# 公司网址： www.odoo.pw  www.100china.cn www.amoserp.com
# Copyright 昆山一百计算机有限公司 2012-2020 Amos
# 日期：2019/11/14
# &&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&

from odoo import api, fields, models, tools, SUPERUSER_ID, _
from odoo.exceptions import AccessDenied, AccessError, UserError, ValidationError
from odoo.osv import expression


class res_company(models.Model):
    _inherit = 'res.company'

    state_id = fields.Many2one("res.country.state", string=u'省')
    city_id = fields.Many2one('res.city', string=u"市")
    area_id = fields.Many2one('res.area', string=u"区/县")
