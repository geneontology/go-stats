from setuptools import setup

with open("README.md", "r") as fh:
    long_description = fh.read()

setup(
    name='go-stats',
    version='1.1.2',
    description='Python Library to generate statistics on a Gene Ontology (GO) release',
    py_modules=["go_stats"],
    packages=[''],
    url="https://github.com/geneontology/go-stats",
    author="Laurent-Philippe Albou",
    author_email="laurent.albou@lbl.gov",
    keywords=["GO", "stats", "GOLR", "statistics", "Gene Ontology"],
    install_requires=[
        'requests',
    ],

    classifiers=[
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.6",
        "Programming Language :: Python :: 3.7",
        "License :: OSI Approved :: BSD License"
    ],

    long_description=long_description,
    long_description_content_type="text/markdown"
)


