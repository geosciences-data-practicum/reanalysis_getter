from setuptools import setup, find_packages
setup(
    name='jetstream',
    version='0.0.2',
    author=['Ivan Higuera-Mendieta',
            'Amanda Farah',
            'Yuqi Song',
            'Jim Franke'],
    author_email='ivanhigueram@uchicago.edu',
    description='Python library for paper results replication',
    include_package_data=True,
    url="",
    packages= find_packages(include=['jetstream']),
)
