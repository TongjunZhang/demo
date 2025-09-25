from setuptools import setup, find_packages

setup(
    name="cci_eap_glue_marketo",
    version="0.1.0",
    packages=find_packages(include=['tasks','tasks.utils', 
                                    'tasks', 'tasks.aws_api_io', 
                                    'tasks','tasks.snowflake_io', 
                                    'tasks', 'tasks.https_io'
                                    'tasks', 'osc_io']),
    include_package_data=True,
    install_requires=[],
    author="Enterprise Data Management",
    author_email="tongjun.zhang@crowncastle.com",
    description="Glue job to extract data from Snowflake and create one Account in OSC",
    classifiers=[
        "Programming Language :: Python :: 3",
        "Operating System :: OS Independent",
    ]
)
