#!/usr/bin/python3.4
# -*- coding: utf-8 -*-

import sys
import signal
import cairo


class DependencyGraph():
    pass


class Relation():
    pass


class Arc():
    pass


class Canvas():
    pass


def draw_arc(graph, canvas, relation):

    arrow_length = 0

    word_start = relation.word_start
    word_end = relation.word_end
    word_spacing = graph.word_spacing

    links_start = relation.relations_start
    links_end = relation.relations_end

    # calculates the space until the first and last word
    letters = sum([len(w) for w in graph.sentence[:word_start - 1]])
    start = (((word_start - 1) * word_spacing) + letters) * 7

    letters = sum([len(w) for w in graph.sentence[:word_end - 1]])
    end = (((word_end - 1) * word_spacing) + letters) * 7

    start_slot = len(relation.relations_start_left)

    # finds start slot by indexing all the relations from the starting node
    # compares the current relation with the index list
    ends = sorted([end for (_, end) in relation.relations_start_right])
    for idx, target in enumerate(ends):
        if target == relation.word_end:
            start_slot += len(relation.relations_start_right) - idx - 1
            break

    end_slot = 0

    # finds end slot by indexing all the relations from the starting node
    # compares the current relation with the index list
    starts = sorted([s for (s, e) in relation.relations_end_left
                     if e == relation.word_end])
    for idx, source in enumerate(starts):
        if source == relation.word_start:
            end_slot += len(starts) - idx - 1
            break

    total_start = len(graph.sentence[word_start - 1]) * 7
    total_end = len(graph.sentence[word_end - 1]) * 7

    # divides the total space given to the word for each slot
    start += (total_start // (links_start + 1)) * (start_slot + 1) - 3
    end += (total_end // (links_end + 1)) * (end_slot + 1) - 3

    x = 13 + start
    y = canvas.height - canvas.arc_base_height

    # coordinates of the center of the arc
    xc = x + canvas.radius
    yc = y - (20 * relation.distance)

    # draws the arrow at the end
    if(relation.origin == relation.word_start):

        canvas.context.move_to(xc - canvas.radius - arrow_length,
                               y - arrow_length - canvas.bheight)
        canvas.context.line_to(xc - canvas.radius, y - canvas.bheight)
        canvas.context.line_to(xc - canvas.radius + arrow_length,
                               y - arrow_length - canvas.bheight)
        canvas.context.stroke()

    # draws line to the first arc
    canvas.context.move_to(x, y - canvas.bheight)
    canvas.context.line_to(x, yc)
    canvas.context.stroke()

    # arc to the right
    angle1 = 3.14
    angle2 = -1.57
    canvas.context.arc(xc, yc, canvas.radius, angle1, angle2)

    xc = end

    # arc to the left
    angle1 = -1.57
    angle2 = 0
    canvas.context.arc(xc, yc, canvas.radius, angle1, angle2)
    canvas.context.stroke()

    # draws line from the second arc
    canvas.context.move_to(xc + canvas.radius, y - canvas.bheight)
    canvas.context.line_to(xc + canvas.radius, yc)
    canvas.context.stroke()

    # draws the arrow at the end
    if(relation.origin == relation.word_end):
        canvas.context.move_to(xc + canvas.radius - arrow_length,
                               y - arrow_length - canvas.bheight)
        canvas.context.line_to(xc + canvas.radius, y - canvas.bheight)
        canvas.context.line_to(xc + canvas.radius + arrow_length,
                               y - arrow_length - canvas.bheight)
        canvas.context.stroke()

    # draws the annotation
    canvas.context.set_font_size(canvas.font_annotation_size)
    # centers the annotation
    canvas.context.move_to(start + ((end - start) / 2) +
                           (10 - len(relation.annotation)), yc - 5)
    canvas.context.show_text(relation.annotation.upper())
    canvas.context.stroke()


def draw(graph):

    canvas = Canvas()

    # Change carefully!!!
    canvas.font_size = 12
    canvas.font_annotation_size = 10
    canvas.arc_base_height = 15
    canvas.bheight = 10
    canvas.radius = 15
    canvas.padding_left = 10

    canvas.width = ((graph.words * graph.word_spacing) + graph.letters) * 7
    canvas.height = canvas.arc_base_height + \
        canvas.bheight + \
        canvas.radius + \
        (graph.max_relation_height * 20)

    # access to the draw canvas
    canvas.surface = cairo.ImageSurface(cairo.FORMAT_ARGB32,
                                        canvas.width,
                                        canvas.height)
    canvas.context = cairo.Context(canvas.surface)

    # background color
    canvas.context.set_source_rgb(1.0, 1.0, 1.0)
    canvas.context.rectangle(0, 0, canvas.width, canvas.height)
    canvas.context.fill()

    # writes the sentence
    canvas.context.select_font_face('monospace',
                                    cairo.FONT_SLANT_NORMAL,
                                    cairo.FONT_WEIGHT_BOLD)
    canvas.context.set_font_size(canvas.font_size)
    canvas.context.move_to(canvas.padding_left, canvas.height-10)
    canvas.context.set_source_rgb(0, 0, 0)

    # writes each word with a spacing
    spacing = ' ' * graph.word_spacing
    canvas.context.show_text(spacing.join(graph.sentence))
    canvas.context.stroke()

    links = [(r.word_start, r.word_end) for r in graph.relations]
    print(links)

    for idx, word in enumerate(graph.sentence):
        print()
        print(word)

        # draws all the arcs from the word
        for relation in graph.relations:

            # relations starting in these word
            if relation.word_start == idx + 1:

                # count relations on the starting and ending node
                relations_start = 0
                relations_end = 0
                relations_start_left = []
                relations_start_right = []
                relations_end_left = []

                for (start, end) in links:

                    if relation.word_start in [start, end]:
                        relations_start += 1
                    if relation.word_end in [start, end]:
                        relations_end += 1
                    if relation.word_start == start:
                        relations_start_right.append((start, end))
                    if relation.word_start == end:
                        relations_start_left.append((start, end))

                relation.relations_start = relations_start
                relation.relations_end = relations_end
                relation.relations_start_left = relations_start_left
                relation.relations_start_right = relations_start_right

                for (start, end) in links:
                    for (_, target) in relations_start_right:
                        if target == end:
                            relations_end_left.append((start, end))

                relation.relations_end_left = relations_end_left
                draw_arc(graph, canvas, relation)

    # saves it to file
    canvas.surface.write_to_png("example.png")


def read_input():
    """ Reads the stdin buffer assumming a pipeline """

    sentence = []

    for line in sys.stdin:
        line = line.rstrip('\n')

        # complete sentence received (each sentence ends with a newline)
        if len(line) == 0:
            generate_graph(sentence)
            sentence.clear()
        else:
            sentence.append(line.split('\t'))

    # ended without a newline but has some sentence in buffer
    if sentence:
        generate_graph(sentence)


def generate_graph(sentence):

    graph = DependencyGraph()

    graph.word_spacing = 4

    graph.sentence = [entry[1] for entry in sentence]
    graph.relations = generate_relations(sentence)

    graph.words = len(graph.sentence)
    graph.letters = sum([len(word) for word in graph.sentence])
    graph.max_relation_height = max([r.distance for r in graph.relations])

    draw(graph)


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

        relation.word_start = word_min
        relation.word_end = word_max

        relations.append(relation)

    # defines the distance of the arc
    for relation in relations:

        distances = []
        # stores all word distances and counts the uniques
        # this value plus one is the maximum height of the
        # arc needed to represent the actual relation
        for sub_relation in relations:

            if relation != sub_relation:
                if sub_relation.word_start >= relation.word_start:
                    if sub_relation.word_end <= relation.word_end:

                        word_distance = sub_relation.word_end -\
                                        sub_relation.word_start

                        distances.append(word_distance)

        relation.distance = len(set(distances)) + 1
        print(distances)

    return relations

if __name__ == "__main__":

    signal.signal(signal.SIGPIPE, signal.SIG_DFL)
    read_input()
