import unittest
from decimal import Decimal

from proteus import Model, Wizard
from trytond.modules.account.tests.tools import (create_chart,
                                                 create_fiscalyear,
                                                 get_accounts)
from trytond.modules.account_invoice.tests.tools import (
    create_payment_term, set_fiscalyear_invoice_sequences)
from trytond.modules.company.tests.tools import create_company, get_company
from trytond.tests.test_tryton import drop_db
from trytond.tests.tools import activate_modules


class TestCommissionWorkflow(unittest.TestCase):

    def setUp(self):
        drop_db()
        super().setUp()

    def tearDown(self):
        drop_db()
        super().tearDown()

    def test(self):
        for with_sale in [False, True]:
            with self.subTest(sale=with_sale):
                drop_db()
                self.run_workflow(with_sale)

    def run_workflow(self, with_sale):
        modules = ['commission_multiple']
        if with_sale:
            modules.append('sale')
        config = activate_modules(modules)

        # Create company
        _ = create_company()
        company = get_company()

        # Reload the context
        User = Model.get('res.user')
        config._context = User.get_preferences(True, config.context)

        # Create fiscal year
        fiscalyear = set_fiscalyear_invoice_sequences(
            create_fiscalyear(company))
        fiscalyear.click('create_period')

        # Create chart of accounts
        _ = create_chart(company)
        accounts = get_accounts(company)

        # Create customer
        Party = Model.get('party.party')
        customer = Party(name='Customer')
        customer.save()

        # Create account category
        ProductCategory = Model.get('product.category')
        account_category = ProductCategory(name="Account Category")
        account_category.accounting = True
        account_category.account_expense = accounts['expense']
        account_category.account_revenue = accounts['revenue']
        account_category.save()

        # Create commission product
        Uom = Model.get('product.uom')
        Template = Model.get('product.template')
        Product = Model.get('product.product')
        unit, = Uom.find([('name', '=', 'Unit')])
        commission_product = Product()
        template = Template()
        template.name = 'Commission'
        template.default_uom = unit
        template.type = 'service'
        template.list_price = Decimal(0)
        template.cost_price = Decimal(0)
        template.account_category = account_category
        if with_sale:
            template.salable = True
        template.save()
        commission_product.template = template
        commission_product.save()

        # Create commission plan
        Plan = Model.get('commission.plan')
        plan = Plan(name='Plan')
        plan.commission_product = commission_product
        plan.commission_method = 'posting'
        line = plan.lines.new()
        line.formula = 'amount * 0.1'
        plan.save()

        # Create payment term
        payment_term = create_payment_term()
        payment_term.save()

        Agent = Model.get('commission.agent')
        agents = []
        for name, formula in [('Agent 1', 'amount * 0.1'),
                ('Agent 2', 'amount * 0.2')]:
            agent_plan = Plan(name=name, commission_product=commission_product,
                commission_method='posting')
            agent_plan.lines.new(formula=formula)
            agent_plan.save()
            party = Party(name=name)
            party.save()
            agent = Agent(party=party, type_='agent', plan=agent_plan,
                currency=company.currency)
            agent.save()
            agents.append(agent)

        Invoice = Model.get('account.invoice')
        if with_sale:
            Sale = Model.get('sale.sale')
            sale = Sale(party=customer, payment_term=payment_term,
                invoice_method='order')
            sale.agents.extend(agents)
            line = sale.lines.new(product=commission_product, quantity=1)
            line.unit_price = Decimal(100)
            sale.click('quote')
            sale.click('confirm')
            sale.click('process')
            invoice, = sale.invoices
            self.assertIsNone(sale.agent)
        else:
            Module = Model.get('ir.module')
            sale_module, = Module.find([('name', '=', 'sale')])
            self.assertNotEqual(sale_module.state, 'activated')
            invoice = Invoice(type='out', party=customer,
                payment_term=payment_term)
            invoice.agents.extend(agents)
            line = invoice.lines.new(product=commission_product, quantity=1)
            line.unit_price = Decimal(100)
            invoice.save()

        self.assertEqual(set(invoice.agents), set(agents))
        invoice.click('post')
        self.assertEqual(invoice.state, 'posted')
        self.assertEqual(
            {c.agent.id: c.amount for c in invoice.lines[0].commissions},
            {agents[0].id: Decimal(10), agents[1].id: Decimal(20)})
        for keep_agents in [True, False]:
            wizard = Wizard('account.invoice.credit', [invoice])
            wizard.form.with_refund = False
            wizard.form.with_agent = keep_agents
            wizard.execute('credit')
            credit, = wizard.actions[0]
            self.assertEqual(set(credit.agents),
                set(agents) if keep_agents else set())
            credit.click('post')
            self.assertEqual(credit.state, 'posted')
            self.assertEqual(
                {c.agent.id: c.amount for c in credit.lines[0].commissions},
                {agents[0].id: Decimal(-10), agents[1].id: Decimal(-20)}
                if keep_agents else {})
