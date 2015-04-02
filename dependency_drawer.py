#!/usr/bin/python3.4
# -*- coding: utf-8 -*-

import sys
import signal
import math
import cairo


def draw(sentence_words, max_word_distance, relations):

    # CONSTANT!!!
    word_spacing = 4
    font_size = 12
    font_annotation_size = 10
    arc_base_height = 15
    line_base_height = 10
    radius = 15
    padding_left = 10

    # calculates width taking into account the words
    words = len(sentence_words)
    letters = sum([len(word) for word in sentence_words])
    width = ((words * word_spacing) + letters) * 7

    # calculates height taking into account the max_word_distance
    height = arc_base_height + line_base_height + radius + \
        (max_word_distance * 20)

    surface = cairo.ImageSurface(cairo.FORMAT_ARGB32, width, height)
    context = cairo.Context(surface)

    # background color
    context.set_source_rgb(1.0, 1.0, 1.0)
    context.rectangle(0, 0, width, height)
    context.fill()

    # write the sentence
    context.select_font_face('monospace',
                             cairo.FONT_SLANT_NORMAL,
                             cairo.FONT_WEIGHT_BOLD)
    context.set_font_size(font_size)
    context.move_to(padding_left, height-10)
    context.set_source_rgb(0, 0, 0)

    # writes each word with a spacing
    spacing = ' ' * word_spacing
    context.show_text(spacing.join(sentence_words))
    context.stroke()

    # draws arc with annotation and arrow
    # TODO: abstract
    def draw_arc(start, end, annotation='', word_distance=1, origin=True,
                 count_left=0, count_right=0):

        arrow_length = 0

        ######################################################################
        # figures the start positon and end position
        start_word, start_links = start
        end_word, end_links = end

        # count letters until the word it starts or ends
        letters = sum([len(w) for w in sentence_words[:start_word - 1]])
        start = ((start_word - 1) * word_spacing) + letters

        letters = sum([len(w) for w in sentence_words[:end_word - 1]])
        end = ((end_word - 1) * word_spacing) + letters

        start = start * 7
        end = end * 7

        print()
        print(annotation)
        print("start links", start_links)
        print("end links", end_links)
        print("distance", word_distance)

        start_slot = count_left
        end_slot = word_distance - 1

        total_left = start_links - count_left

        if total_left > 1:
            start_slot += total_left - min(word_distance, total_left) + 1

        print("total to left", (start_links - count_left))

        print("count_left", count_left)
        print("count_right", count_right)
        print("start slot", start_slot)
        print("end_slot", end_slot)

        total_start = len(sentence_words[start_word - 1]) * 7
        total_end = len(sentence_words[end_word - 1]) * 7

        # divides the total space given to the word for each slot
        start += (total_start // (start_links + 1)) * (start_slot + 1) - 3
        end += (total_end // (end_links + 1)) * (end_slot + 1) - 3

        ######################################################################

        x = 13 + start
        y = height - arc_base_height

        # coordinates of the center of the arc
        xc = x + radius
        yc = y - (20 * word_distance)

        # draws the arrow at the end
        if(not origin):
            context.move_to(xc - radius - arrow_length,
                            y - arrow_length - line_base_height)
            context.line_to(xc - radius,
                            y - line_base_height)
            context.line_to(xc - radius + arrow_length,
                            y - arrow_length - line_base_height)
            context.stroke()

        # draws line to the first arc
        context.move_to(x, y - line_base_height)
        context.line_to(x, yc)
        context.stroke()

        # arc to the right
        angle1 = 3.14
        angle2 = -1.57
        context.arc(xc, yc, radius, angle1, angle2)

        xc = end

        # arc to the left
        angle1 = -1.57
        angle2 = 0
        context.arc(xc, yc, radius, angle1, angle2)
        context.stroke()

        # draws line from the second arc
        context.move_to(xc + radius, y - line_base_height)
        context.line_to(xc + radius, yc)
        context.stroke()

        # draws the arrow at the end
        if(origin):
            context.move_to(xc + radius - arrow_length,
                            y - arrow_length - line_base_height)
            context.line_to(xc + radius,
                            y - line_base_height)
            context.line_to(xc + radius + arrow_length,
                            y - arrow_length - line_base_height)
            context.stroke()

        # draws the annotation
        context.set_font_size(font_annotation_size)
        # centers the annotation
        context.move_to(start + ((end - start) / 2) + (10 - len(annotation)),
                        yc - 5)
        context.show_text(annotation.upper())
        context.stroke()

    for relation in relations:
        draw_arc(start=relation.start,
                 end=relation.end,
                 annotation=relation.annotation,
                 word_distance=relation.word_distance,
                 origin=relation.origin,
                 count_left=relation.count_left,
                 count_right=relation.count_right)

    # saves it to file
    surface.write_to_png("example.png")


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

    class Relation():
        pass

    relation = Relation()
    relations = []

    # extracts the raw sentence
    sentence_words = [entry[1] for entry in sentence]

    links = []
    links_from = []
    links_to = []

    for entry in sentence:
        if entry[7] != 'ROOT':
            links_from.append(int(entry[0]))
            links_to.append((int(entry[6])))

    links = links_from + links_to

    print(links_from)
    print(links_to)
    print()

    for entry in sentence:

        id_str = int(entry[0])
        head = int(entry[6])
        deprel = entry[7]

        if deprel == 'ROOT':
            continue

        relation = Relation()
        relation.annotation = deprel
        relation.word_distance = math.fabs(id_str - head)

        if head > id_str:
            relation.origin = False
        else:
            relation.origin = True

        # the relation is always from left to right
        word_min = min(id_str, head)
        word_max = max(id_str, head)

        relation.start = (word_min, links.count(word_min))
        relation.end = (word_max, links.count(word_max))

        count_left = 0
        count_right = 0

        for (source, target) in zip(links_from, links_to):

            # from the left to the leftmost word of the arc
            if target == word_min:
                if source < target:
                    count_left += 1
            if source == word_min:
                if target < source:
                    count_left += 1

            # from the right to the leftmost word of the arc
            if source == word_max:
                if source < target:
                    count_right += 1

            if target == word_max:
                if target < source:
                    count_right += 1

        relation.count_left = count_left
        relation.count_right = count_right

        relations.append(relation)

    max_distance = int(max([r.word_distance for r in relations]))
    draw(sentence_words, max_distance, relations)

if __name__ == "__main__":

    signal.signal(signal.SIGPIPE, signal.SIG_DFL)
    read_input()
