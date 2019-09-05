from setuptools import setup, find_packages

setup(
name='EasyVVUQ-QCGPJ',

version='0.0.3.dev1',

description='A lightweight wrapper on EasyVVUQ enabling the execution of VVUQ '
'using the QCG Pilot Job mechanism.',

long_description='A lightweight wrapper on EasyVVUQ enabling the execution of VVUQ '
'using the QCG Pilot Job mechanism.',

url='https://github.com/vecma-project/EasyVVUQ-QCGPJ',

author='Bartosz Bosak',

install_requires=[
    'pytest',
    'pytest-pep8',
    'scipy==1.2.1',
    'qcgPilotManager @ git+https://github.com/vecma-project/QCG-PilotJob.git@issue_33_node_launcher#egg=qcgPilotManager',
    'easyvvuq @ git+https://github.com/UCL-CCS/EasyVVUQ.git@dev#egg=easyvvuq'
    #'qcgPilotManager==0.4.1',
    #'easyvvuq==0.3'
],

packages=find_packages(),

scripts=[
    'scripts/easyvvuq_app',
    'scripts/easyvvuq_encode',
    'scripts/easyvvuq_execute'
],

include_package_data=True
)
