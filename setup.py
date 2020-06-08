from setuptools import setup, find_packages

with open("README.md", "r") as fh:
    readme = fh.read()

setup(
    name='easyvvuq-qcgpj',

    version='0.3rc9',

    description='A lightweight plugin for EasyVVUQ enabling the execution of VVUQ '
                'using the QCG-PilotJob mechanism.',

    long_description=readme,
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
