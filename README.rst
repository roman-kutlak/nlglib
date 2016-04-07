Intro
=====

NLGlib is a library for natural language generation (NLG) written in Python.
It seeks to fill a gap in the NLG field. There are currently no off-the-shelf
libraries that one could take and incorporate into other projects.
The aim of this library is to be useful for general projects that would like
to add a bit of text generation to their capabilities.


Audience
========

The library should be useable by programmers with as little linguistic knowledge
as possible. Given that the aim of the library is language generation,
some linguistic knowledge is necessary.


Scope
=====

The aim of the library is to create a base for NLG system starting from content
selection all the way to realisation. The library will cover document structuring
tools, lexicalisation, referring expression generation and aggregation.
Realisation will be done using other realisation libraries (SimpleNLG or pynlg).
At the moment, the input to the library is a list of First Order Logic formulas
and the output is English text.


History
=======

NLGlib started as a part of the EPSRC project
Scrutable Autonomous Systems (SAsSy): www.scrutable-systems.org
When the project finished, the code was moved to this repository to create
a stand-alone re-usable library.
