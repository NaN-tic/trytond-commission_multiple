from trytond.model import ModelSQL, fields
from trytond.pool import PoolMeta
from trytond.pyson import Eval


class Sale(metaclass=PoolMeta):
    __name__ = 'sale.sale'

    agents = fields.Many2Many(
        'sale.sale-commission.agent', 'sale', 'agent', 'Commission Agents',
        domain=[
            ('type_', '=', 'agent'),
            ('company', '=', Eval('company', -1)),
            ],
        states={
            'readonly': ~Eval('state').in_(['draft', 'quotation']),
            })

    @classmethod
    def __setup__(cls):
        super().__setup__()
        cls.agent.states['invisible'] = True

    @classmethod
    def set_agent(cls, sales):
        super().set_agent(sales)
        for sale in sales:
            if not sale.agents and sale.agent:
                sale.agents = [sale.agent]
            sale.agent = None
        cls.save(sales)

    def _get_invoice(self):
        invoice = super()._get_invoice()
        invoice.agent = None
        invoice.agents = self.agents
        return invoice


class SaleAgent(ModelSQL):
    __name__ = 'sale.sale-commission.agent'

    sale = fields.Many2One(
        'sale.sale', 'Sale', required=True, ondelete='CASCADE')
    agent = fields.Many2One(
        'commission.agent', 'Agent', required=True, ondelete='RESTRICT')
