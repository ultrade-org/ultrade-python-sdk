import setuptools
import codecs
import os

here = os.path.abspath(os.path.dirname(__file__))

with codecs.open(os.path.join(here, "README.md"), encoding="utf-8") as fh:
    long_description = "\n" + fh.read()

setuptools.setup(
    name="ultrade2",
    version='0.1.1',
    description="",
    author="Ultrade",
    url="https://github.com/ultrade-org/ultrade-python-sdk",
    packages=setuptools.find_packages(),
    install_requires=[
        "py-algorand-sdk",
        "python-socketio",
        "asyncio",
        "aiohttp"
    ]
)
