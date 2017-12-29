Current Status
==============
This is just a starting point - an alpha version - mainly a wrapper
around SimpleNLG_.

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
Realisation will be done using other realisation libraries (SimpleNLG_ or pynlg_).


History
=======

NLGlib started as a part of the EPSRC project
Scrutable Autonomous Systems (SAsSy): www.scrutable-systems.org
When the project finished, the code was moved to this repository to create
a stand-alone re-usable library.


Example
=======

.. code-block:: python

    from nlglib.realisation.simplenlg.realisation import Realiser
    from nlglib.microplanning import *

    realise_en = Realiser(host='roman.kutlak.info', port=40000)
    realise_es = Realiser(host='roman.kutlak.info', port=40001)


    def main():
        p = Clause("María", "perseguir", "un mono")
        p['TENSE'] = 'PAST'
        # expected = 'María persigue un mono.'
        print(realise_es(p))
        p = Clause(NP("la", "rápida", "corredora"), VP("perseguir"), NP("un", "mono"))
        subject = NP("la", "corredora")
        objekt = NP("un", "mono")
        verb = VP("perseguir")
        subject.premodifiers.append("rápida")
        p.subject = subject
        p.predicate = verb
        p.object = objekt
        # expected = 'La rápida corredora persigue un mono.'
        print(realise_es(p))
        p = Clause(NP('this', 'example'), VP('show', 'how cool simplenlg is'))
        # expected = This example shows how cool simplenlg is.
        print(realise_en(p))


    if __name__ == '__main__':
        main()


.. _SimpleNLG: https://github.com/simplenlg/simplenlg
.. _pynlg: https://github.com/mapado/pynlg
