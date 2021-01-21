from setuptools import setup, find_packages
import sys

setup(
    name='lib_browser',
    packages=find_packages(),
    version='0.0.0',
    author='Justin Furuness',
    author_email='jfuruness@gmail.com',
    url='https://github.com/jfuruness/lib_browser.git',
    download_url='https://github.com/jfuruness/lib_browser.git',
    keywords=['Furuness', 'Browser', 'Wrapper', 'Selenium Wrapper'],
    install_requires=[
        'pynput',
        'selenium'
    ],
    classifiers=[
        'Environment :: Console',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: BSD License',
        'Programming Language :: Python :: 3'],
    entry_points={
        'console_scripts': 'lib_browser = lib_browser.__main__:main'},
    setup_requires=['pytest-runner'],
    tests_require=['pytest'],
)
