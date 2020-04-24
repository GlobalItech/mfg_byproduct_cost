# -*- coding: utf-8 -*-
{
    "name": "Finished goods and by-products costing(Manufacturing)",
    'version': '12.0.1.0',
    "author": "ITECH RESOURCES",
    "category": "Manufacturing",
    "description": """
        This module will managed the Manufacturing plus costing,
    """,
    "depends": ['mrp','product', 'stock', 'resource','mrp_byproduct','mrp_account'],
    "data": [
             'views/shafi_work.xml',
             'views/reports.xml',
             ],
    "images": ['static/description/banner.gif'],     
    "license": "LGPL-1",
    "installable": True,
    "auto_install": False,
    'price': 30.00,
    
    'currency': 'USD',
}
