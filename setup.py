import setuptools


setuptools.setup(
    name="skrate",
    version="0.1",
    author="David Lenkner",
    description="App for skateboarding progression analysis",
    license="MIT",
    long_description=open("README.md").read(),
    long_description_content_type="text/markdown",
    url="https://github.com/lenknerd/skrate",
    packages=setuptools.find_packages(),
    scripts=["run_skrate"],
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent"
    ],
    install_requires=[
        "click>=7.0",
        "Flask>=1.1.1",
        "Flask-Ext>=0.1",
        "Flask-Session>=0.3.1",
        "Flask-SQLAlchemy>=2.4.1",
        "Flask-Testing>=0.7.1",
        "psycopg2-binary>=2.8.4",
        "pytest>=5.3.2",
        "SQLAlchemy>=1.3.12",
    ],
)
