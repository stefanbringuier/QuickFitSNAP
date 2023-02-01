from setuptools import setup, find_packages

with open("requirements.txt", "r") as f:
    requirements = f.read().splitlines()

setup(
    name='QuickfitSNAP',
    version='0.1',
    description='Quick and dirty SNAP potentials using FitSNAP and materials databases',
    author='Stefan Bringuier',
    author_email='stefanbringuier@gmail.com',
    packages=find_packages(),
    install_requires=requirements,
    include_package_data=True,
)
