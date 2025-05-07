import setuptools

from pathlib import Path

this_directory = Path(__file__).parent
long_description = (this_directory / "README.md").read_text()

required_packages = (this_directory / "requirements.txt").read_text().splitlines()

setuptools.setup(
    name="ultrade-sdk",
    version="0.3.15",
    license="MIT",
    description="This SDK provides interface that helps making trading operations within the Ultrade network easier",
    long_description=long_description,
    long_description_content_type="text/markdown",
    author="Ultrade",
    url="https://github.com/ultrade-org/ultrade-python-sdk",
    packages=setuptools.find_packages(exclude=("tests", "docs")),
    install_requires=required_packages,
    extras_require={
        "dev": ["pytest>=7.0", "twine>=4.0.2"],
    },
    python_requires='>=3.10'
)
