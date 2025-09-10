from setuptools import setup, find_packages

setup(
    name="cci-eap-edmdq-marketo",
    version="0.1.0",
    packages=find_packages(),
        package_data={
        '': ['tasks/*'],
    },
    include_package_data=True,
    install_requires=[],
    author="edm",
    author_email="abdul.shaik@crowncastle.com",
    description="Glue job to generate the matching output between osc accounts and marketing data sets",
    classifiers=[
        "Programming Language :: Python :: 3",
        "Operating System :: OS Independent",
    ]
)
