from configparser import ConfigParser
from pathlib import Path

from setuptools import setup


directory = Path(__file__).parent
config = ConfigParser()
config.read(directory / 'tryton.cfg')

setup(
    name='nantic_commission_multiple',
    version=config['tryton']['version'],
    description='Multiple commission agents for invoices and sales',
    long_description=(directory / 'README').read_text(),
    author='NaN·tic',
    license='GPL-3.0-or-later',
    package_dir={'trytond.modules.commission_multiple': '.'},
    packages=['trytond.modules.commission_multiple'],
    package_data={'trytond.modules.commission_multiple': [
        'tryton.cfg', '*.xml', 'view/*.xml']},
    install_requires=['trytond>=8.0,<8.1', 'trytond_commission>=8.0,<8.1'],
    extras_require={'sale': ['trytond_sale>=8.0,<8.1']},
    entry_points={'trytond.modules': [
        'commission_multiple = trytond.modules.commission_multiple']},
    )
