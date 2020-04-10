from setuptools import setup, find_packages

exec(open('wikidata_property_extraction/version.py').read())

setup(
    name="wikidata_property_extraction",
    version=__version__,
    packages=find_packages(),
    description="A package to extract multilingual labels of all elements of"
                + " a given property from WikiData and a given list of "
                + "languages. The goal of this package is to provide an easy "
                + "access to elements in WikiData. Especially the extraction "
                + "of elements from ontologies that have a related property in"
                + " WikiData.",
    keywords="biomedical, ontology, translation, wikidata",
    classifiers=[
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.5",
        "Programming Language :: Python :: 3.6",
        "Programming Language :: Python :: 3.7",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Development Status :: 4 - Beta",

    ],
    author="Léo Bouscarrat, EURA NOVA",
    author_email="leo.bouscarrat@euranova.eu, research@euranova.eu",
    install_requires=["pandas", "requests", "tqdm"],
    url='https://github.com/euranova/wikidata_property_extraction',
    project_urls={'Paper': 'https://hal.archives-ouvertes.fr/hal-02531140v1'},
    python_requires='>=3',
)
