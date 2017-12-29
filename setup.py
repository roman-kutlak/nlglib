from setuptools import setup, find_packages


def long_description():
    with open('README.rst', 'r') as f:
        return f.read()

setup(
    name="nlglib",
    version='0.1.0',
    description='Natural Language Generation library for Python',
    long_description=long_description(),
    author="Roman Kutlak",
    author_email='kutlak.roman@gmail.com',
    url='https://github.com/roman-kutlak/nlglib',
    license='MIT',
    classifiers=[
        'Development Status :: 3 - Alpha',
        'Intended Audience :: Developers',
        'Intended Audience :: Science/Research',
        'Natural Language :: English',
        'License :: OSI Approved :: MIT License',
        'Operating System :: OS Independent',
        'Programming Language :: Python',
        'Programming Language :: Python :: 3',
        'Topic :: Scientific/Engineering :: Artificial Intelligence',
        'Topic :: Software Development :: Libraries',
        'Topic :: Text Processing :: Linguistic'
    ],
    packages=find_packages(exclude=['docs', 'examples', 'tests/*']),
    keywords=['natural language generation', 'NLG', 'text generation', 'nlglib', 'library'],
    install_requires=[
        'nltk'
    ],
    include_package_data=True,
    package_dir={'nlglib': 'nlglib'},
    # package_data={'nlglib': ['resources/*']},
    zip_safe=True,
)
