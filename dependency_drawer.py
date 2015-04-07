#!/usr/bin/python3.4
# -*- coding: utf-8 -*-

"""
Draws a dependency graph from a modified CONLL input

Author: João A. Rodrigues (joao.rodrigues@di.fc.ul.pt)
Date: 7 April 2015

Version: 0.9
"""

import sys
import signal
import cairo
import collections


class DependencyGraph():
    pass


class Relation():
    pass


class Canvas():
    pass


def read_input():
    """
    Reads the stdin buffer assumming a pipeline

    The input must be in the CONLL format, ex.:

    #index
    Sentence: Maria Vitória tem razão .
    1   Maria   MARIA   PNM PNM _       3   SJ-ARG1 _   _
    2   Vitória VITÓRIA PNM PNM _       1   N       _   _
    3   tem     TER     V   V   pi-3s   0   ROOT    _   _
    4   razão   RAZÃO   CN  CN  gs      3   DO-ARG2 _   _
    5   .       .       PNT PNT _       3   PUNCT   _   _

    """

    sentence = []

    for line in sys.stdin:
        line = line.rstrip('\n')

        # processes a complete sentence stored in the list
        if len(line) == 0:
            generate_graph(sentence)
            sentence.clear()
        # adds word and its annotation data to the list
        else:
            sentence.append(line.split('\t'))

    # ended without a newline but has some sentence in buffer
    if sentence:
        generate_graph(sentence)


def generate_graph(sentence):
    """
    Generates the graph data reprensentation for the dependencies
    """

    graph = DependencyGraph()

    # shows tags
    graph.show_tags = True

    # extracts id, makes it an attribute and removes from sentence list
    graph.id = str(sentence.pop(0)[0])[1:]

    # ignores and removes the sentence line
    sentence.pop(0)

    if(graph.show_tags):
        graph.tags = generate_tags(sentence)

    # defines the space between words
    graph.word_spacing = 6

    # extracts word-form sentence
    graph.sentence = [entry[1] for entry in sentence]

    # handles all the relations of dependency
    graph.relations = generate_relations(sentence)

    # number of words
    graph.words = len(graph.sentence)

    # number of total letters in sentence
    # this is used to count the space of each letter and thus
    # allowing to pin point where to start to draw an arc
    graph.letters = sum([len(word) for word in graph.sentence])

    # the relation height is used to define the arc height,
    # an arc from two neighboor words just needs a 1 relation height
    # an arc from a two word distance needs a 2 relation height...
    # the maximum value from all relations will set the maximum height
    # necessary for the canvas
    graph.max_relation_height = max([r.distance for r in graph.relations])

    draw(graph)


def draw(graph):
    """
    Draws the main canvas and relations of the dependencies

    Uses the 2D graphics library Cairo: http://cairographics.org/download/
    with the Python bindings: http://cairographics.org/pycairo/


    """
    canvas = Canvas()

    # if you really must change something, change carefully!!!
    canvas.font_size = 12
    canvas.letter_width = 7
    canvas.font_annotation_size = 10
    canvas.arc_base_height = 15
    canvas.bheight = 10
    canvas.radius = 15
    canvas.padding_left = 10

    # the width of the canvas is the relation of all the letters in the
    # sentence, words spacing and the letter_width that seems to translate
    # a letter space to the canvas
    canvas.width = ((graph.words * graph.word_spacing) + graph.letters) * \
        canvas.letter_width

    # the height of the canvas is the relation of the highest relation height
    # the radius of the arc curve and the default arc height
    canvas.height = canvas.arc_base_height + \
        canvas.bheight + \
        canvas.radius + \
        (graph.max_relation_height * 20)

    # access to the draw canvas
    canvas.surface = cairo.ImageSurface(cairo.FORMAT_ARGB32,
                                        canvas.width,
                                        canvas.height)
    canvas.context = cairo.Context(canvas.surface)

    # background color draw as a white rectangle
    canvas.context.set_source_rgb(1.0, 1.0, 1.0)
    canvas.context.rectangle(0, 0, canvas.width, canvas.height)
    canvas.context.fill()

    # writes the sentence taking into account a word spacing
    canvas.context.select_font_face('monospace',
                                    cairo.FONT_SLANT_NORMAL,
                                    cairo.FONT_WEIGHT_BOLD)
    canvas.context.set_font_size(canvas.font_size)
    canvas.context.move_to(canvas.padding_left, canvas.height-10)
    canvas.context.set_source_rgb(0, 0, 0)

    spacing = ' ' * graph.word_spacing
    canvas.context.show_text(spacing.join(graph.sentence))
    canvas.context.stroke()

    # extracts the relations between the words of the sentence ex.:
    # [(A, B), (1, 2), (3, 4), (3, 5)]
    # word A as a relation to word B
    links = [(r.word_start, r.word_end) for r in graph.relations]

    # for each word in the sentence it will generate the necessary information
    # for drawing the arcs that spawn from it
    # it starts from the left of the sentence and draws all the arcs to
    # subsequent words, it does NOT draw from father/head to child, it draws
    # from the first word counting from the left to the word to its right
    for idx, word in enumerate(graph.sentence):

        # searches for relations that start from the current word
        for relation in graph.relations:
            if relation.word_start == idx + 1:

                # relations on the starting and ending word
                relation.relations_start = 0
                relation.relations_end = 0

                # stores the references to the relations that come from the
                # LEFT and RIGHT to the STARTing or ENDing word
                #
                # ex.: relations_start_right = [(A, B), (A, C)]
                # this means that in the current word A there are two
                # relations to two words at its right, the B and C words
                relation.relations_start_left = []
                relation.relations_start_right = []
                relation.relations_end_left = []

                for (start, end) in links:

                    if relation.word_start in [start, end]:
                        relation.relations_start += 1

                    if relation.word_end in [start, end]:
                        relation.relations_end += 1

                    if relation.word_start == start:
                        relation.relations_start_right.append((start, end))

                    if relation.word_start == end:
                        relation.relations_start_left.append((start, end))

                for (start, end) in links:
                    for (_, end_right) in relation.relations_start_right:
                        if end == end_right:
                            relation.relations_end_left.append((start, end))

                draw_arc(graph, canvas, relation)

    # output the image resource
    canvas.surface.write_to_png(graph.id + ".png")

    if graph.show_tags:

        canvas.tags_height = 100
        canvas.height = canvas.height + canvas.tags_height

        # copies the content of the previous image
        new_canvas = Canvas()
        new_canvas.surface = cairo.ImageSurface(cairo.FORMAT_ARGB32,
                                                canvas.width,
                                                canvas.height)

        new_canvas.context = cairo.Context(new_canvas.surface)
        new_canvas.context.set_source_surface(canvas.surface, 0, 0)
        new_canvas.context.paint()

        canvas.surface = new_canvas.surface
        canvas.context = new_canvas.context

        # background color draw as a white rectangle
        canvas.context.set_source_rgb(1.0, 1.0, 1.0)
        canvas.context.rectangle(0, canvas.height - canvas.tags_height,
                                 canvas.width, canvas.height)
        canvas.context.fill()


        new_canvas.surface.write_to_png(graph.id + "_tagged.png")



def draw_arc(graph, canvas, relation):
    """
    Draws an arc with annotation and an arrow to signal direction
    """

    arrow_length = 3

    # for simplification
    word_start = relation.word_start
    word_end = relation.word_end
    word_spacing = graph.word_spacing

    relations_start = relation.relations_start
    relations_end = relation.relations_end

    # calculates the space until the first and last word
    letters = sum([len(w) for w in graph.sentence[:word_start - 1]])
    start = (((word_start - 1) * word_spacing) + letters) * 7

    letters = sum([len(w) for w in graph.sentence[:word_end - 1]])
    end = (((word_end - 1) * word_spacing) + letters) * 7

    # the slot represents the arcs entries and exits a word can have
    # the starting slot always takes into account previous arcs that may
    # have ended in these word (always at its left)
    start_slot = len(relation.relations_start_left)

    # indexes all the relations from the starting word to words at its right
    # compares the current relation with the index list and finds the best
    # suitable slot, this is, a slot that will allow to draw an arc taking
    # into account its distance to the ending word and thus defining its
    # correctly height so it doesn't intersect other arcs
    ends = sorted([e for (_, e) in relation.relations_start_right])
    for idx, target in enumerate(ends):
        if target == relation.word_end:
            start_slot += len(relation.relations_start_right) - idx - 1
            break

    end_slot = 0

    # same as previous but for the ending word
    starts = sorted([s for (s, e) in relation.relations_end_left
                     if e == relation.word_end])
    for idx, source in enumerate(starts):
        if source == relation.word_start:
            end_slot += len(starts) - idx - 1
            break

    # counts space of the start and end word
    total_start = len(graph.sentence[word_start - 1]) * 7
    total_end = len(graph.sentence[word_end - 1]) * 7

    # divides the total space given to the word for each slot
    start += (total_start // (relations_start + 1)) * (start_slot + 1) - 1
    end += (total_end // (relations_end + 1)) * (end_slot + 1) - 3

    # coordinates of the center of the arc
    x = canvas.padding_left + start + 3
    y = canvas.height - canvas.arc_base_height
    xc = x + canvas.radius
    yc = y - (20 * relation.distance)

    # draws the arrow at the end
    if(relation.origin == relation.word_end):

        canvas.context.move_to(xc - canvas.radius - arrow_length,
                               y - arrow_length - canvas.bheight)
        canvas.context.line_to(xc - canvas.radius, y - canvas.bheight)
        canvas.context.line_to(xc - canvas.radius + arrow_length,
                               y - arrow_length - canvas.bheight)
        canvas.context.stroke()

    # draws line from starting word to its arc
    canvas.context.move_to(x, y - canvas.bheight)
    canvas.context.line_to(x, yc)
    canvas.context.stroke()

    # draws the arc of the starting word
    angle1 = 3.14
    angle2 = -1.57
    canvas.context.arc(xc, yc, canvas.radius, angle1, angle2)

    # puts the x coordinate in the center of the ending word
    # note that there is NOT a context.stroke() between the drawing of the
    # arcs, this is done on purpose so a line from the first arc is draw to
    # the second arc
    xc = end

    # draws the arc of the ending word
    angle1 = -1.57
    angle2 = 0
    canvas.context.arc(xc, yc, canvas.radius, angle1, angle2)
    canvas.context.stroke()

    # draws line from the second arc
    canvas.context.move_to(xc + canvas.radius, y - canvas.bheight)
    canvas.context.line_to(xc + canvas.radius, yc)
    canvas.context.stroke()

    # draws the arrow at the end
    if(relation.origin == relation.word_start):
        canvas.context.move_to(xc + canvas.radius - arrow_length,
                               y - arrow_length - canvas.bheight)
        canvas.context.line_to(xc + canvas.radius, y - canvas.bheight)
        canvas.context.line_to(xc + canvas.radius + arrow_length,
                               y - arrow_length - canvas.bheight)
        canvas.context.stroke()

    # draws the annotation
    canvas.context.set_font_size(canvas.font_annotation_size)

    # centers the annotation
    c = (x + canvas.radius) + ((xc - (x + canvas.radius)) / 2)
    c = c - ((len(relation.annotation) / 2) * canvas.letter_width) + 3
    canvas.context.move_to(c,  yc - 5)
    canvas.context.show_text(relation.annotation.upper())
    canvas.context.stroke()


def generate_relations(sentence):

    relation = Relation()
    relations = []

    # removes the root relation from the sentence
    sentence = [entry for entry in sentence if entry[7] != 'ROOT']

    # each CONLL entry is a relation
    for entry in sentence:

        id_str = int(entry[0])
        head = int(entry[6])
        deprel = entry[7]

        relation = Relation()
        relation.annotation = deprel

        # marks the origin so the arrow can be draw
        relation.origin = head

        # the relation is always from left to right
        word_min = min(id_str, head)
        word_max = max(id_str, head)
        relation.distance = word_max - word_min

        relation.word_start = word_min
        relation.word_end = word_max

        relations.append(relation)

    # defines the distance of the arc
    # from smallest distance relation to highest
    relations = sorted(relations, key=lambda r: r.distance)
    for relation in relations:
        distances = []
        # stores all word distances and counts the uniques
        # this value plus one is the maximum height of the
        # arc needed to represent the actual relation
        for sub_relation in relations:

            if relation != sub_relation:
                if sub_relation.word_start >= relation.word_start:
                    if sub_relation.word_end <= relation.word_end:
                        distances.append(sub_relation.distance)

        relation.distance = len(set(distances)) + 1

    return relations


# defines a namedtuple for the CONLL entries
cols = 'id form lemma cpostag postag feats head deprel phead pdeprel'
Tag = collections.namedtuple('Tag', cols)


def generate_tags(sentence):
    """ Extracts the CONLL columns """

    tags = []

    for entry in sentence:
        tags.append(Tag(*entry))

    return tags

if __name__ == "__main__":

    signal.signal(signal.SIGPIPE, signal.SIG_DFL)
    read_input()
