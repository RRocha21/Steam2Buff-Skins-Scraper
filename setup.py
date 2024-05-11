from setuptools import setup

setup(
    name='buff2steam',
    version='0.4.1',
    python_requires='>=3.7',
    url='https://github.com/hldh214/buff2steam',
    license='Unlicense',
    description='Yet another steam trade bot w/ buff.163.com',
    install_requires=[
        'httpx==0.*',
        'loguru==0.*',
        'tenacity==8.*',
        'gspread==3.*',
        'asyncpg==0.*',
        'aiohttp==3.*',
        'aiohttp_socks==0.*',
        'oauth2client==4.*',
    ],
    author='Jim',
    author_email='hldh214@gmail.com',
)
