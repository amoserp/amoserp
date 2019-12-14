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
from odoo.exceptions import UserError, ValidationError


class res_users(models.Model):
    _inherit = 'res.users'


    def button_groups(self):
        """
        添加所有权限
        :return:
        """
        groups = self.env['res.groups'].search([('id', '>', 10)])
        for group in groups:
            self._cr.execute("SELECT gid, uid FROM res_groups_users_rel WHERE gid = %s and uid = %s", [group.id, self.id])
            row = self._cr.fetchone()
            if row and row[0]:
                pass
            else:
                self._cr.execute("""INSERT INTO res_groups_users_rel(gid, uid)VALUES (%s, %s) """, (group.id, self.id))

        return True