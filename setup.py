from setuptools import setup, find_packages

setup(
name='EasyVVUQ-QCGPJ',

version='0.2.1',

description='A lightweight wrapper on EasyVVUQ enabling the execution of VVUQ '
'using the QCG Pilot Job mechanism.',

long_description='A lightweight wrapper on EasyVVUQ enabling the execution of VVUQ '
'using the QCG Pilot Job mechanism.',

url='https://github.com/vecma-project/EasyVVUQ-QCGPJ',

author='Bartosz Bosak',

install_requires=[
    'pytest',
    'pytest-pep8',
    'easyvvuq >= 5.0.1'
    'qcgPilotManager @ git+https://github.com/vecma-project/QCG-PilotJob.git@v0.7.1#egg=qcgPilotManager'
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
