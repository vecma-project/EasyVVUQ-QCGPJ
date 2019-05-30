from setuptools import setup, find_packages

setup(
name='EasyVVUQ-QCGPJ',

version='0.0.2.dev1',

description='A lightweight wrapper on EasyVVUQ enabling the execution of VVUQ '
'using the QCG Pilot Job mechanism.',

long_description='A lightweight wrapper on EasyVVUQ enabling the execution of VVUQ '
'using the QCG Pilot Job mechanism.',

url='https://github.com/vecma-project/EasyVVUQ-QCGPJ',

author='Bartosz Bosak',

install_requires=[
'scipy==1.2.1',
'qcgpilotmanager @ git+https://github.com/vecma-project/QCG-PilotJob.git@master#egg=qcgpilotmanager',
'easyvvuq @ git+https://github.com/UCL-CCS/EasyVVUQ.git@master#egg=easyvvuq',
],

packages=find_packages(),

include_package_data=True
)
