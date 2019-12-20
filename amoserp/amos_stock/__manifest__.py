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
{
    'name': u'AmosERP-仓库',
    'summary': u'库存',
    'version': '1.0',
    'category': u'仓库',
    'sequence': 40001,
    'author': 'Amos',
    'website': 'http://www.odoo.pw',
    'depends': ['base', 'web', 'amos_base','amos_product'],
    'data': [
        'sequence.xml',
        'data/res_col_data.xml',
        'data/stock_warehouse_data.xml',
        'data/stock_location_data.xml',
        'data/stock_picking_type_data.xml',
        'data/ir_cron.xml',

        'security/security.xml',
        'security/ir.model.access.csv',

        'wizard/union_product_stock_wizard.xml',
        'wizard/product_stock_wizard_view.xml',
        'wizard/stock_picking_price_unit_wizard.xml',
        'wizard/inventory_product_wizard.xml',

        'views/product_product_view.xml',
        'views/stock_move_line_view.xml',
        'views/stock_pickin_view.xml',
        'views/stock_move_view.xml',

        'views/stock_picking_1.xml',

        'views/res_company_view.xml',
        
        'views/product_stock_view.xml',
        'views/stock_warehouse_view.xml',

        'views/stock_picking_out_view.xml',
        'views/stock_picking_in_view.xml',

        'views/stock_picking_scrap_view.xml',
        'views/stock_picking_lose_view.xml',
        'views/stock_picking_return_view.xml',

        'views/stock_warehouse_orderpoint_view.xml',
        'views/stock_picking_type_view.xml',
        'views/stock_location_view.xml',

        'views/stock_picking_inventory_view.xml',
        'views/stock_picking_losses_view.xml',
        'views/stock_picking_overage_view.xml',

        'views/stock_picking_tested_out_view.xml',
        'views/stock_picking_tested_in_view.xml',

        'views/stock_lend_out_view.xml',
        'views/stock_lend_out_in_view.xml',

        'views/stock_picking_tested_view.xml',
    ],
    'installable': True,
    'application': True,
    'auto_install': False,
    'description': """
库存
==================================
仓库进出

功能
-------------
* 入库
* 出库
""",
}

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
