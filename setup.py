from setuptools import setup, find_packages

setup(
    name="nlglib",
    version='0.0.1',
    description='Natural Language Generation library for Python',
    long_description=open('README.md').read(),
    author=["Roman Kutlak"],
    author_email=['roman@kutlak.net'],
    url='http://github.com/roman-kutlak/nlglib',
    license='MIT',
    classifiers=[
        'Development Status :: 2 - Pre-Alpha',
        'Intended Audience :: Developers',
        'Natural Language :: English',
        'License :: OSI Approved :: MIT License',
        'Operating System :: OS Independent',
        'Programming Language :: Python',
        'Programming Language :: Python :: Implementation :: CPython',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.4',
        'Topic :: Software Development :: Libraries :: Python Modules',
        'Topic :: Text Processing :: Linguistic'
    ],
    include_package_data=True,
    packages=find_packages(exclude=['test/*']),
    zip_safe=False,
    keywords=['natural language generation', 'NLG', 'text generation', 'nlglib'], install_requires=['werkzeug']
)
