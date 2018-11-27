pydependencygrapher
===================

Draws dependency graphs from a modified CONLL input

Usage example
-------------

.. code::

    cat example.conll | ./pydependencygrapher.py

Input example
-------------

.. code::

    #example
    Sentence: Foi Darwin ou foi a evolução?
    1	Foi	SER,IR	V	V	ppi-3s	0	ROOT	_	_
    2	Darwin	Darwin	PNM	PNM	_	1	PRD-ARG2	_	_
    3	ou	OU	CJ	CJ	_	4	CONJ	_	_
    4	foi	SER,IR	V	V	ppi-3s	1	COORD	_	_
    5	a	A	DA	DA	fs	6	SP	_	_
    6	evolução	EVOLUÇÃO	CN	CN	fs	4	PRD-ARG2	_	_
    7	?	?	PNT	PNT	_	1	PUNCT	_	_


Output example
--------------

.. image:: https://raw.githubusercontent.com/joaoantonioverdade/pydependencygrapher/master/example.png
   :alt: dependency graph with tags
