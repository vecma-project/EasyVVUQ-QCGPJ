from setuptools import setup, find_packages

with open("README.md", "r") as fh:
    readme = fh.read()

long_description = readme.split("\n", 2)[2]

setup(
    name='easyvvuq-qcgpj',

    version='0.3',

    description='A lightweight plugin for EasyVVUQ enabling the execution of demanding VVUQ procedures'
                'using the QCG-PilotJob mechanism.',

    long_description=long_description,
    long_description_content_type='text/markdown',

    url='https://github.com/vecma-project/EasyVVUQ-QCGPJ',

    author='Bartosz Bosak',

    install_requires=[
        'pytest',
        'pytest-pep8'
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
