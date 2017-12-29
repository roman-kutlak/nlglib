Current Status
==============
This is just a starting point - an alpha version - mainly a wrapper
around _SimpleNLG.

Although it is possible to go from first order logic to text,
there is no sophistication in how things are processed.
The library is still missing basics like aggregation or referring expression generation.


Intro
=====

NLGlib is a library for natural language generation (NLG) written in Python.
It seeks to fill a gap in the NLG field. There are currently no off-the-shelf
libraries that one could take and incorporate into other projects.
The aim of this library is to be useful for general projects that would like
to add a bit of text generation to their capabilities.


Audience
========

The library should be usable by programmers with no prior linguistic knowledge.
Given that the aim of the library is language generation,
some linguistic knowledge is necessary but you should be able to pick it up
from the examples.


Scope
=====

The aim of the library is to create a base for NLG system starting from content
selection all the way to realisation. The library will cover document structuring
tools, lexicalisation, referring expression generation and aggregation.
Realisation will be done using other realisation libraries (_SimpleNLG or pynlg).


History
=======

NLGlib started as a part of the EPSRC project
Scrutable Autonomous Systems (SAsSy): www.scrutable-systems.org
When the project finished, the code was moved to this repository to create
a stand-alone re-usable library.


.. _SimpleNLG: https://github.com/simplenlg/simplenlg