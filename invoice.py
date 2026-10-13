from trytond.model import ModelSQL, fields
from trytond.pool import PoolMeta
from trytond.pyson import Eval


class Invoice(metaclass=PoolMeta):
    __name__ = 'account.invoice'

    agents = fields.Many2Many(
        'account.invoice-commission.agent', 'invoice', 'agent',
        'Commission Agents',
        domain=[
            ('type_', '=', 'agent'),
            ('company', '=', Eval('company', -1)),
            ],
        states={
            'invisible': Eval('type') == 'in',
            'readonly': Eval('state') != 'draft',
            })

    @classmethod
    def __setup__(cls):
        super().__setup__()
        cls.agent.states['invisible'] = True

    def _credit(self, **values):
        values.setdefault('agents', self.agents)
        return super()._credit(**values)


class InvoiceAgent(ModelSQL):
    __name__ = 'account.invoice-commission.agent'

    invoice = fields.Many2One(
        'account.invoice', 'Invoice', required=True, ondelete='CASCADE')
    agent = fields.Many2One(
        'commission.agent', 'Agent', required=True, ondelete='RESTRICT')


class InvoiceLine(metaclass=PoolMeta):
    __name__ = 'account.invoice.line'

    @property
    def agent_plans_used(self):
        used = [(agent, plan)
            for agent, plan in super().agent_plans_used
            if agent != self.invoice.agent]
        agents = {agent for agent, _ in used}
        for agent in self.invoice.agents:
            if agent not in agents:
                used.append((agent, agent.plan))
                agents.add(agent)
        return used


class CreditInvoice(metaclass=PoolMeta):
    __name__ = 'account.invoice.credit'

    @property
    def _credit_options(self):
        options = super()._credit_options
        if not self.start.with_agent:
            options['agents'] = []
        return options
