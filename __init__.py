from trytond.pool import Pool

from . import invoice, sale


def register():
    Pool.register(
        invoice.Invoice,
        invoice.InvoiceAgent,
        invoice.InvoiceLine,
        module='commission_multiple', type_='model')
    Pool.register(
        invoice.CreditInvoice,
        module='commission_multiple', type_='wizard')
    Pool.register(
        sale.Sale,
        sale.SaleAgent,
        module='commission_multiple', type_='model', depends=['sale'])
