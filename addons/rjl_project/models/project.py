##############################################################################
#
#    HZ
#    Copyright (C) 2017.
#
##############################################################################

from odoo.osv import expression
from odoo import api, fields, models, _
import odoo.addons.decimal_precision as dp
from datetime import datetime
import pdb

class Project(models.Model):
    _name = 'project.project'
    _inherit = ['project.project', 'mail.thread', 'ir.needaction_mixin']

    @api.one
    @api.depends('project_amount', 'total_expense')
    def _compute_gp(self):
        self.gross_profit = self.boq_amount - self.total_expense - self.po_amount

    @api.one
    @api.depends('completation')
    def _compute_done(self):
        if self.completation >= 100:
            self.done = True


    @api.one
    def _compute_gp_percentage(self):
        if self.boq_amount > 0:
            self.gross_profit_percentage = self.gross_profit / self.boq_amount * 100

    @api.one
    @api.depends('rab_ids.sub_total')
    def _compute_total_rab(self):
        total_rab = 0.0
        total_material = 0.0
        for rab in self.rab_ids:
            total_rab += rab.sub_total
            if rab.product_id.type != 'service':
                total_material += rab.sub_total
        self.rab_amount = total_rab
        self.total_material_amount = total_material
    
    @api.one
    def _compute_total_material_amount(self):
        total_material = 0.0
        for rab in self.rab_ids:
            if rab.product_id.type != 'service':
                total_material += rab.sub_total
        self.total_material_amount = total_material

    @api.one
    def _compute_total_komisi(self):
        #pdb.set_trace()
        if self.total_jasa_amount > 0:
            komisi_percentage = ( (self.total_jasa_amount - self.total_expense) / self.total_jasa_amount * 100) - 50
            if komisi_percentage > 0 and komisi_percentage <= 50:
                percentage = komisi_percentage / 50 * 20 / 100
                self.total_komisi = self.total_jasa_amount * percentage
    @api.one
    def _compute_jasa_amount(self):
        total_jasa = 0.0
        for rab in self.rab_ids:
            if rab.product_id.type == 'service':
                total_jasa += rab.sub_total
        self.total_jasa_amount = total_jasa
    
    @api.one
    def _compute_total_outstanding(self):
        self.outstanding_amount = self.boq_amount - self.payment_amount
        if self.boq_amount >0:
            self.outstanding_percentage = (self.boq_amount - self.payment_amount) / self.boq_amount * 100

    @api.one
    @api.depends('boq_ids.price_subtotal')
    def _compute_total_boq(self):
        total_boq = 0.0
        for boq in self.boq_ids:
            total_boq += boq.price_subtotal
        self.boq_amount = total_boq

    @api.one
    @api.depends('payment_invoice_ids.amount_total')
    def _compute_total_payment(self):
        total_payment = 0.0
        for payment in self.payment_invoice_ids:
            total_payment += payment.amount_total
        self.payment_amount = total_payment

    @api.one
    @api.depends('expense_ids', 'po_ids', 'po_ids.amount_total', 'po_ids.state', 'expense_ids.total_amount', 'expense_ids.state', 'po_ids', 'po_ids.amount_total')
    def _compute_total_expenses(self):
        total_expense = 0.0
        total_po = 0.0
        for expense in self.expense_ids:
            total_expense += expense.total_amount
        for purchase in self.po_ids:
            total_po += purchase.amount_total
        self.total_expense = total_expense
        self.po_amount = total_po

    @api.one
    @api.depends('progression_ids.completation')
    def _compute_project_completation(self):
        task_completation = 0
        for x in self.progression_ids:
            task_completation += x.completation * x.bobot / 100
            task_completation += x.completation_jasa * x.bobot / 100
        if task_completation != 0:
            self.completation = task_completation
        else:
            self.completation = 0

    @api.one
    def _compute_remaining_days(self):
        remaining_day = datetime.strptime(self.date, '%Y-%m-%d') - datetime.today()
        self.remaining_day = remaining_day.days

    @api.one
    def _compute_color(self):
        percentage = 0
        if self.target_progress:
            if self.target_progress > 0:
                percentage = self.remaining_day / self.target_progress * 100
                if percentage < 10:
                    self.color = 3
                elif percentage < 20:
                    self.color = 5
                elif percentage < 50:
                    self.color = 4
                elif percentage > 50:
                    self.color = 1

    company_id = fields.Many2one('res.company', string='Company', change_default=True, required=True, default=lambda self: self.env.user.company_id)
    currency_id = fields.Many2one('res.currency', related='company_id.currency_id', string="Company Currency", readonly=True, store=True)
    payment_invoice_ids = fields.One2many('account.invoice', 'project_id', domain=[('type', '=', 'out_invoice'), ('project_id', '!=', False), ('state', '=', 'paid')])
    expense_ids = fields.One2many('hr.expense', 'project_id', domain=[('state', '=', 'done'), ('project_id', '!=', False)])
    completation = fields.Integer(string='Project Completation', compute='_compute_project_completation')
    po_ids = fields.One2many('purchase.order', 'project_id', string='Purchase Order')
    picking_ids = fields.One2many('stock.picking', 'project_id', string='Stock Picking')
    rab_ids = fields.One2many('project.rab', 'project_id', string='RAB')
    boq_ids = fields.One2many('project.boq', 'project_id', string='BOQ')
    progression_ids = fields.One2many('project.progression', 'project_id', string='Project Progression')
    project_amount = fields.Monetary(string='Project Amount', digits=dp.get_precision('Product Price'), required=True)
    rab_amount = fields.Monetary(string='Total RAB', compute='_compute_total_rab', digits=dp.get_precision('Product Price'), store=True)
    total_material_amount = fields.Monetary(string='Total RAB Material', compute='_compute_total_material_amount', digits=dp.get_precision('Product Price'))
    total_jasa_amount  = fields.Monetary(string='Total Jasa Amount', compute='_compute_jasa_amount')
    total_komisi = fields.Monetary(string='Total Komisi', compute='_compute_total_komisi')
    boq_amount = fields.Monetary(string='Total BOQ', compute='_compute_total_boq', digits=dp.get_precision('Product Price'), store=True)
    po_amount = fields.Monetary(string='Total PO', compute='_compute_total_expenses', digits=dp.get_precision('Product Price'))
    payment_amount = fields.Monetary( string='Total Payment', compute='_compute_total_payment', digits=dp.get_precision('Product Price'))
    outstanding_amount = fields.Monetary(string='Total Outstanding', compute='_compute_total_outstanding')
    outstanding_percentage= fields.Float(string='Outstanding Percentage (%)', compute='_compute_total_outstanding')
    total_expense = fields.Monetary(string='Total Expenses', compute='_compute_total_expenses', digits=dp.get_precision('Product Price'))
    gross_profit = fields.Monetary(string='Gross Profit', compute='_compute_gp')
    gross_profit_percentage = fields.Float(string='GP Percentage', compute='_compute_gp_percentage')
    pm_id = fields.Many2one('hr.employee', required=True, string='Project Manager')
    done = fields.Boolean(string='Done', compute='_compute_done', store=True)
    member_ids = fields.Many2many('hr.employee', 'project_member_rel', 'employee_id', 'project_id', string='Project Member')
    remaining_day = fields.Integer(string='Remaining Days', compute='_compute_remaining_days')
    target_progress = fields.Integer(string='Target Progress')
    color = fields.Integer(string='Color Index', compute='_compute_color')

class ProjectBoq(models.Model):
    _name = 'project.boq'

    @api.one
    @api.depends('product_qty', 'product_price')
    def _compute_price_subtotal(self):
        self.price_subtotal = self.product_qty * self.product_price

    project_id = fields.Many2one('project.project', string='Project')
    product_id = fields.Many2one('product.product', string='Product')
    product_qty = fields.Float(string='Product Qty')
    product_price = fields.Float(string='Unit Price', digits=dp.get_precision('Product Price'))
    price_subtotal = fields.Float(string='Price Subtotal', digits=dp.get_precision('Product Price'), compute='_compute_price_subtotal')

class ProjectRab(models.Model):
    _name = 'project.rab'

    @api.one
    @api.depends('product_qty', 'price_unit')
    def _compute_sub_total(self):
        self.sub_total = self.product_qty * self.price_unit

    @api.one
    @api.depends('project_id.po_ids.order_line.product_id', 'project_id.po_ids.order_line.product_qty', 'project_id.po_ids.state', 'project_id.po_ids')
    def _compute_purchased_qty(self):
        qty = 0
        po_ids = []
        for po in self.project_id.po_ids:
            if po.state == 'purchase':
                po_ids.append(po.id)
        for x in self.env['purchase.order.line'].search([('order_id', 'in', po_ids), ('product_id', '=', self.product_id.id)]):
            qty += x.product_qty
        self.purchased_qty = qty

    @api.one
    @api.depends('project_id.picking_ids.pack_operation_product_ids.qty_done')
    def _compute_received_qty(self):
        qty = 0
        for picking in self.project_id.picking_ids:
            for move in picking.pack_operation_product_ids:
                if self.product_id == move.product_id:
                    qty += move.qty_done
        self.received_qty = qty

    @api.one
    def _compute_bobot(self):
        for x in self:
            if x.product_id.type != 'service':
                if x.sub_total > 0 and x.project_id.total_material_amount > 0:
                    x.bobot = x.sub_total / x.project_id.total_material_amount * 100
            else:
                x.bobot = 0.0
    project_id = fields.Many2one('project.project', required=True, string='Project')
    due_date = fields.Date(string='Due Date')
    bobot = fields.Float(string='Progress Material', compute='_compute_bobot')
    task_id = fields.Many2one('project.job.task', string='Project Task') 
    product_id = fields.Many2one('product.product', required=True, string='Product')
    product_qty = fields.Float(required=True, string='Product Qty', digits=dp.get_precision('Product Unit of Measure'))
    purchased_qty = fields.Float(string='Purchased Qty', digits=dp.get_precision('Product Unit of Measure'), compute='_compute_purchased_qty', store=True)
    received_qty = fields.Float(string='Received Qty', digits=dp.get_precision('Product Unit of Measure'), compute='_compute_received_qty', store=True)
    surplus_qty = fields.Float(string='Surplus Qty', digits=dp.get_precision('Product Unit of Measure'))
    price_unit = fields.Float(required=True, string='Price Unit', digits=dp.get_precision('Product Price'))
    sub_total = fields.Float(string='Sub Total', digits=dp.get_precision('Product Price'), compute='_compute_sub_total', store=True)
    note = fields.Char(string='Keterangan')

class ProjectJobTask(models.Model):
    _name = 'project.job.task'

    @api.multi
    @api.depends('name', 'parent_id')
    def name_get(self):
        result = []
        for record in self:
            if record.parent_id:
                name = record.parent_id.name + ' - ' + record.name
            else:
                name = record.name
            result.append((record.id, name))
        return result

    name = fields.Char(string='Task Name', required=True)
    parent_id = fields.Many2one('project.job.task', string='Parent Task')
    child_ids = fields.One2many('project.job.task', 'parent_id', string='Parent Child')

class ProjectProgression(models.Model):
    _name = 'project.progression'
    _rec_name = 'task_id'

    @api.one
    @api.depends('project_id.rab_ids.received_qty', 'is_material')
    def _compute_completation(self):
        for y in self:
            if y.is_material:
                completation = 0.0
                bobot = 0.0
                for x in y.project_id.rab_ids:
                    if x.product_id.type != 'service':
                        bobot += x.bobot
                y.completation = bobot
    @api.one
    def _compute_bobot(self):
        for y in self:
            if self.is_material:
                if self.project_id.rab_amount > 0:
                    self.bobot = self.project_id.total_material_amount / self.project_id.rab_amount * 100
            else:
                #pdb.set_trace()
                total_jasa = 0.0
                for rab_jasa in self.env['project.rab'].search([('project_id', '=', y.project_id.id), ('task_id', '=', y.task_id.id)]):
                    total_jasa += rab_jasa.sub_total
                if y.project_id.rab_amount > 0:
                    y.bobot = total_jasa / y.project_id.rab_amount * 100 

    project_id = fields.Many2one('project.project', required=True)
    task_id = fields.Many2one('project.job.task', required=True)
    start_date = fields.Date(string='Start Date', required=True)
    due_date = fields.Date(string='Due Date', required=True)
    state = fields.Selection([('on_progress', 'On Progress'), ('warning', 'Warning'), ('delay', 'Delay'), ('done', 'Done')], default='on_progress', string='Status')
    notes = fields.Text(string='Notes')
    bobot = fields.Float(string="Bobot Task", compute='_compute_bobot')
    is_material = fields.Boolean(string='Material Task')
    completation = fields.Integer(string='Completation', compute='_compute_completation')
    completation_jasa = fields.Integer(string='Completation Jasa')
    pic_ids = fields.Many2many('hr.employee', 'task_pic_rel', 'employee_id', 'progression_id', string='Task PIC')

class PurchaseOrder(models.Model):
    _inherit = 'purchase.order'

    project_id = fields.Many2one('project.project', string='Project')

class StockPicking(models.Model):
    _inherit = 'stock.picking'

    project_id = fields.Many2one('project.project', string='Project')

class AccountInvoice(models.Model):
    _inherit = 'account.invoice'

    project_id = fields.Many2one('project.project', string='Project')

class AccountInvoiceLine(models.Model):
    _inherit = 'account.invoice.line'

    project_id = fields.Many2one('project.project', string='Project', related='invoice_id.project_id', store=True)

class HrExpense(models.Model):
    _inherit = 'hr.expense'

    project_id = fields.Many2one('project.project', string='Project')
