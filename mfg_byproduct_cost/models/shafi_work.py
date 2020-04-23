from odoo import api, fields, models, _


class mrpadd(models.Model):
    _inherit = 'mrp.subproduct'
     
    cost_a = fields.Float(string='Cost')
    totals_a = fields.Float(string='Total amount',compute='custom123')
    
    @api.onchange('product_id')
    def custom1(self):
        for s in self:
            s.cost_a=s.product_id.standard_price  
    
    @api.depends('product_qty') 
    @api.onchange('product_id','product_qty')
    def custom123(self):
        for s in self:
            s.totals_a=s.cost_a*s.product_qty   
            
class MrpProduction(models.Model):
    _inherit = 'mrp.production'

    def _cal_price(self, consumed_moves):
        """Set a price unit on the finished move according to `consumed_moves`.
        """
        super(MrpProduction, self)._cal_price(consumed_moves)
        work_center_cost = 0
        a=0.0
        finished_move = self.move_finished_ids.filtered(lambda x: x.product_id == self.product_id and x.state not in ('done', 'cancel') and x.quantity_done > 0)
        if self.bom_id.sub_products:
            for s in self.bom_id.sub_products:
                a=a+(s.cost_a*s.product_qty)*self.product_qty
        if finished_move:
            finished_move.ensure_one()
            for work_order in self.workorder_ids:
                time_lines = work_order.time_ids.filtered(lambda x: x.date_end and not x.cost_already_recorded)
                duration = sum(time_lines.mapped('duration'))
                time_lines.write({'cost_already_recorded': True})
                work_center_cost += (duration / 60.0) * work_order.workcenter_id.costs_hour
            if finished_move.product_id.cost_method in ('fifo', 'average'):
                qty_done = finished_move.product_uom._compute_quantity(finished_move.quantity_done, finished_move.product_id.uom_id)
                finished_move.price_unit = (sum([-m.value for m in consumed_moves]) + work_center_cost-a) / qty_done 
                finished_move.value = sum([-m.value for m in consumed_moves]) + work_center_cost
        return True


class MrpCostStructure12(models.AbstractModel):
    _inherit = 'report.mrp_account.mrp_cost_structure'

    @api.multi
    def get_lines(self, productions):
        ProductProduct = self.env['product.product']
        StockMove = self.env['stock.move']
        res = []
        for product in productions.mapped('product_id'):
            mos = productions.filtered(lambda m: m.product_id == product)
            total_cost = 0.0
            total_cost1 =0.0
        

            #get the cost of operations
            operations = []
            Workorders = self.env['mrp.workorder'].search([('production_id', 'in', mos.ids)])
            if Workorders:
                query_str = """SELECT w.operation_id, op.name, partner.name, sum(t.duration), wc.costs_hour
                                FROM mrp_workcenter_productivity t
                                LEFT JOIN mrp_workorder w ON (w.id = t.workorder_id)
                                LEFT JOIN mrp_workcenter wc ON (wc.id = t.workcenter_id )
                                LEFT JOIN res_users u ON (t.user_id = u.id)
                                LEFT JOIN res_partner partner ON (u.partner_id = partner.id)
                                LEFT JOIN mrp_routing_workcenter op ON (w.operation_id = op.id)
                                WHERE t.workorder_id IS NOT NULL AND t.workorder_id IN %s
                                GROUP BY w.operation_id, op.name, partner.name, t.user_id, wc.costs_hour
                                ORDER BY op.name, partner.name
                            """
                self.env.cr.execute(query_str, (tuple(Workorders.ids), ))
                for op_id, op_name, user, duration, cost_hour in self.env.cr.fetchall():
                    operations.append([user, op_id, op_name, duration / 60.0, cost_hour])
            
            by_product_moves = []
            h=productions.product_qty       
            if productions.bom_id.sub_products:
                for q in productions.bom_id.sub_products:
                    by_product_moves.append({
                    'product_ids': q.product_id,
                    'costs':q.cost_a,
                    'cost_a': q.cost_a*h*q.product_qty,
                    'qty1': h*q.product_qty,
                })
            #get the cost of raw material effectively used
            raw_material_moves = []
            query_str = """SELECT product_id, bom_line_id, SUM(product_qty), abs(SUM(price_unit * product_qty))
                            FROM stock_move WHERE raw_material_production_id in %s AND state != 'cancel'
                            GROUP BY bom_line_id, product_id"""
            self.env.cr.execute(query_str, (tuple(mos.ids), ))
            for product_id, bom_line_id, qty, cost in self.env.cr.fetchall():
                raw_material_moves.append({
                    'qty': qty,
                    'cost': cost,
                    'product_id': ProductProduct.browse(product_id),
                    'bom_line_id': bom_line_id
                })
                total_cost += cost

            #get the cost of scrapped materials
            scraps = StockMove.search([('production_id', 'in', mos.ids), ('scrapped', '=', True), ('state', '=', 'done')])
            uom = mos and mos[0].product_uom_id
            mo_qty = 0
            if not all(m.product_uom_id.id == uom.id for m in mos):
                uom = product.uom_id
                for m in mos:
                    qty = sum(m.move_finished_ids.filtered(lambda mo: mo.state != 'cancel' and mo.product_id == product).mapped('product_qty'))
                    if m.product_uom_id.id == uom.id:
                        mo_qty += qty
                    else:
                        mo_qty += m.product_uom_id._compute_quantity(qty, uom)
            else:
                for m in mos:
                    mo_qty += sum(m.move_finished_ids.filtered(lambda mo: mo.state != 'cancel' and mo.product_id == product).mapped('product_qty'))
            for m in mos:
                sub_product_moves = m.move_finished_ids.filtered(lambda mo: mo.state != 'cancel' and mo.product_id != product)
            res.append({
                'product': product,
                'mo_qty': mo_qty,
                'mo_uom': uom,
                'operations': operations,
                'currency': self.env.user.company_id.currency_id,
                'by_product_moves':by_product_moves,
                'raw_material_moves': raw_material_moves,
                'total_cost': total_cost,
                'scraps': scraps,
                'mocount': len(mos),
                'sub_product_moves': sub_product_moves
            })
        return res




