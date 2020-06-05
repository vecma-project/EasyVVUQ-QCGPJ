from setuptools import setup, find_packages

setup(
name='EasyVVUQ-QCGPJ',

version='0.3rc1',

description='A lightweight wrapper on EasyVVUQ enabling the execution of VVUQ '
'using the QCG Pilot Job mechanism.',

long_description='A lightweight wrapper on EasyVVUQ enabling the execution of VVUQ '
'using the QCG Pilot Job mechanism.',

url='https://github.com/vecma-project/EasyVVUQ-QCGPJ',

author='Bartosz Bosak',

install_requires=[
    'pytest',
    'pytest-pep8',
    'easyvvuq >= 0.6',
    'qcg-pilotjob == 0.8.0rc4'
],

packages=find_packages(),

scripts=[
    'scripts/easyvvuq_app',
    'scripts/easyvvuq_encode',
    'scripts/easyvvuq_execute',
    'scripts/easyvvuq_encode_execute'
],

include_package_data=True
)
