import versioneer

from setuptools import setup, find_packages

with open("README.md", "r") as fh:
    readme = fh.read()

long_description = readme.split("\n", 2)[2]

setup(
    name='easyvvuq-qcgpj',

    version=versioneer.get_version(),
    cmdclass=versioneer.get_cmdclass(),

    description='A lightweight plugin for EasyVVUQ enabling the execution of demanding VVUQ procedures '
                'using the QCG-PilotJob mechanism.',

    long_description=long_description,
    long_description_content_type='text/markdown',

    url='https://github.com/vecma-project/EasyVVUQ-QCGPJ',

    author='Bartosz Bosak',

    install_requires=[
        'pytest',
        'pytest-flake8'
    ],

    packages=find_packages(),

    scripts=[
        'scripts/easyvvuq_encode',
        'scripts/easyvvuq_execute',
        'scripts/easyvvuq_encode_execute',
        'scripts/eqi_utils.sh'
    ],

    include_package_data=True
)
