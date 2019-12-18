# -*- coding: utf-8 -*-
# &&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&
# AmosERP odoo11.0
# QQ:35350428
# 邮件:35350428@qq.com
# 手机：13584935775
# 作者：'odoo'
# 公司网址： www.odoo.pw  www.100china.cn www.amoserp.com
# Copyright 昆山一百计算机有限公司 2012-2020 Amos
# 日期：2019/12/11
# &&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&

{
    'name': 'AmosERP-产品资料',
    'summary': u'产品',
    'version': '1.0',
    'category': '产品资料',
    'sequence': 10001,
    'author': 'Amos',
    'website': 'http://www.odoo.pw',
    'depends': ['base', 'amos_base'],
    'data': [
        'data/res_attachment_access_data.xml',
        'security/security.xml',
        'security/ir.model.access.csv',
        'views/sequence.xml',
        # 'wizard/product_export_import_wizard.xml',
        'views/product_product_view.xml',
        'views/product_category_view.xml',
        'views/menuitem.xml',
        'views/uom_uom_view.xml',
        'views/add_button_views.xml',
    ],
    'demo': [
    ],
    'installable': True,
    'application': True,
    'auto_install': False,
    'description': """
""",
}

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
