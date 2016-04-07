Examples
========

Some examples of how to use `nlglib`.


Basic Data Structures
---------------------

.. |nlglib| nlglib
.. |simplenlg| SimpleNLG


The library requires `SimpleNLG <https://github.com/simplenlg/simplenlg>`_ for surface realisation.
|nlglib| actually comes with a |simplenlg| jar but as it is not maintained much, it might be
a few minor versions behind.


Create a simple canned string:

.. code-block:: python

    from nlglib import pipeline

    templates = {
        'john': NNP('John', features=dict([Gender.feminine])),
        'paul': NNP('Paul', features=dict([Gender.masculine])),
        'george': NNP('George', features=dict([Gender.masculine])),
        'ringo': NNP('Ringo', features=dict([Gender.masculine])),
        'guitar': Noun('guitar'),
        'bass': Noun('bass guitar'),
        'drums': Noun('drum', features=dict([Number.plural])),
        'Happy': Clause(NP(PlaceHolder(0)), VP('be', AdjP('happy'))),
        'Play': Clause(NP(PlaceHolder(0)), VP('play', NP(PlaceHolder(1)))),
    }
    input_str = 'Play(john, guitar) & Play(paul, guitar); Play(george, bass); Play(ringo, drums)'
    output_str = pipeline.translate(input_str, templates, [])
    print(output_str)

