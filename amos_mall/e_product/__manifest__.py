# -*- coding: utf-8 -*-
{
    'name': u'草莓-产品资料',
    'summary': 'e-commerce',
    'version': '1.0',
    'category': u'商品',
    'sequence': 100,
    'author': 'Amos',
    'website': 'http://www.100china.cn',
    'depends': ['base','mail','e_base'],
    'data': [
        'security/security.xml',
        'security/ir.model.access.csv',
        'views/e_product.xml',
    ],
    'demo': [
    ],
    'installable': True,
    'application': True,
    'auto_install': False,
    'description': """
    不同的商家可以入驻本系统，每一个商家分配到一个公司ID
    每一个商家只能管理自己的商品
    删除时判断当前用户是不是可以管理产品的商家
    
    提供商家迁移：所以不能有关联字段，
    App总平台产品，由我们提供，商家对商品进行关联，这个只针对品牌产品
    
    非品牌产品，产品标记为非品牌
    """,
}
