# -*- coding: utf-8 -*-
{
    "name": "Finished goods and by-products costing(Manufacturing)",
    "version": "0.1",
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
             
    "installable": True,
    "auto_install": False,
    'price': 30.00,
     'license': 'AGPL-3',
    'currency': 'EUR',
}
