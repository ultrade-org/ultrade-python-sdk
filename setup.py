import setuptools

setuptools.setup(
    name="ultrade",
    version='0.1.1',
    description="",
    author="Ultrade",
    url="https://github.com/ultrade-org/ultrade-python-sdk",
    packages=setuptools.find_packages(),
    install_requires=[
        "py-algorand-sdk",
        "python-socketio",
        "asyncio",
        "aiohttp",
        "bip-utils"
    ]
)
