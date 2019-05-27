from setuptools import setup, find_packages

setup(
name='easyvvuq-qcgpj',

version='0.0.1.dev1',

description='A lightweight wrapper on EasyVVUQ enabling the execution of VVUQ '
'using the QCG Pilot Job mechanism.',

long_description='A lightweight wrapper on EasyVVUQ enabling the execution of VVUQ '
'using the QCG Pilot Job mechanism.',

url='TODO',

author='Bartosz Bosak',

install_requires=[
'qcgpilotmanager @ git+https://github.com/vecma-project/QCG-PilotJob.git@master#egg=qcgpilotmanager',
'easyvvuq @ git+https://github.com/UCL-CCS/EasyVVUQ.git@qcgpj_integration#egg=easyvvuq',
],

packages=find_packages(),

include_package_data=True
)
