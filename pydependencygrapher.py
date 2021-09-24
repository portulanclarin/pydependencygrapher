"""
Draws a dependency graph from a modified CONLL input

Author: João A. Rodrigues (joao.rodrigues@di.fc.ul.pt)
Date: 8 April 2015
"""

__version__ = "1.1.1"

import cairo
import collections
import base64
from io import BytesIO


# defines a named-tuple for the CONLL tokens
Token = collections.namedtuple(
    'Token', 'id form lemma cpostag postag feats head deprel phead pdeprel'
)


ROOT = Token(
    id="1",
    form="-Root-",
    lemma="",
    cpostag="",
    postag="",
    feats="",
    head="_",
    deprel="_",
    phead="_",
    pdeprel="_"
)


class Relation(object):
    def __init__(self, token):
        self.origin = int(token.head)
        self.annotation = token.deprel
        # the relation is always from left to right words
        self.word_start = min(int(token.id), self.origin)
        self.word_end = max(int(token.id), self.origin)
        self.distance = self.word_end - self.word_start


def make_sentence(lines):
    return (
        lines[0].lstrip("#"), # sentence id
        lines[1].lstrip("Sentence:"), # raw sentence
        [Token(*line.split('\t')) for line in lines[2:]], # tokens
    )


def read_input(inputfile):
    """
    Reads sentences from stdin

    The input must be in the following modified CONLL format, ex.:

    #sentence_id
    Sentence: Maria Vitória tem razão .
    1   Maria   MARIA   PNM PNM _       3   SJ-ARG1 _   _
    2   Vitória VITÓRIA PNM PNM _       1   N       _   _
    3   tem     TER     V   V   pi-3s   0   ROOT    _   _
    4   razão   RAZÃO   CN  CN  gs      3   DO-ARG2 _   _
    5   .       .       PNT PNT _       3   PUNCT   _   _


    An empty line ends the sentence.
    The sentence_id is used as the basename of the resulting image file.
    The initial hash (#) is stripped from sentence_id.
    The second line (containing the sentence) is ignored.
    Each token line must contain 10 tab-separated columns:
        1. token id
        2. form
        3. lemma
        4. cpostag
        5. postag
        6. feats
        7. head
        8. deprel
        9. phead
        10. pdeprel

    """
    lines = []
    for line in inputfile:
        line = line.rstrip()
        if line:
            lines.append(line)
        else:
            if len(lines) >= 3:
                yield make_sentence(lines)
            lines = []
    if len(lines) >= 3:
        yield make_sentence(lines)


class DependencyGraph(object):
    """
    Generates the graph data representation for the dependencies
    """

    def __init__(
                self,
                sentence,
                show_tags=True,
                word_spacing=6,
                font_size=12,
                letter_width=7,
                font_annotation_size=10,
                arc_base_height=15,
                bheight=10,
                radius=15,
                padding_left=10,
                draw_root=True,
            ):
        if draw_root:
            self.sentence = [ROOT]
            self.sentence.extend(
                Token(
                    int(t.id)+1,
                    t.form,
                    t.lemma,
                    t.cpostag,
                    t.postag,
                    t.feats,
                    int(t.head)+1 if t.head != '_' else t.head,
                    t.deprel,
                    int(t.phead)+1 if t.phead != '_' else t.phead,
                    t.pdeprel,
                )
                for t in sentence
            )
        else:
            self.sentence = sentence
        self.show_tags = show_tags
        self.word_spacing = word_spacing
        self.forms = [token.form for token in self.sentence]
        self.relations = self.get_relations()
        # the relation height is used to define the arc height,
        # an arc from two neighbor words just needs a 1 relation height
        # an arc from a two word distance needs a 2 relation height...
        # the maximum value from all relations will set the maximum height
        # necessary for the canvas
        self.max_relation_height = max([r.distance for r in self.relations])
        self.font_size = font_size
        self.letter_width = letter_width
        self.font_annotation_size = font_annotation_size
        self.arc_base_height = arc_base_height
        self.bheight = bheight
        self.radius = radius
        self.padding_left = padding_left
        self.surface = None

    def draw(self):
        """
        Draws the main canvas and relations of the dependencies

        Uses the 2D graphics library Cairo: http://cairographics.org/download/
        with the Python bindings: http://cairographics.org/pycairo/
        """

        ntokens = len(self.forms)

        # number of total letters in sentence
        # this is used to count the space of each letter and thus
        # allowing to pin point where to start to draw an arc
        nletters = sum([len(token.form) for token in self.sentence])

        # the width of the canvas is the relation of all the letters in the
        # sentence, words spacing and the letter_width that seems to translate
        # a letter width to the canvas

        self.width = ((ntokens * self.word_spacing) + nletters) * self.letter_width

        # the height of the canvas is: the combination of the highest relation
        # height, the radius of the arc curve and the default arc height
        self.height = self.arc_base_height + self.bheight + self.radius + (self.max_relation_height * 20)

        if self.show_tags:
            # adds height space to write the tags
            self.tags_number = 3
            self.tags_height = self.tags_number * 20
            self.height = self.height + self.tags_height

        # access to the draw canvas
        self.surface = cairo.ImageSurface(cairo.FORMAT_ARGB32, self.width, self.height)
        self.context = cairo.Context(self.surface)

        # background color draw as a white rectangle
        self.context.set_source_rgb(1.0, 1.0, 1.0)
        self.context.rectangle(0, 0, self.width, self.height)
        self.context.fill()

        # writes the sentence taking into account a word spacing
        self.context.select_font_face('monospace',
                                        cairo.FONT_SLANT_NORMAL,
                                        cairo.FONT_WEIGHT_NORMAL)
        self.context.set_font_size(self.font_size)
        if self.show_tags:
            self.context.move_to(self.padding_left, self.height - self.tags_height - 10)
        else:
            self.context.move_to(self.padding_left, self.height-10)
        self.context.set_source_rgb(0, 0, 0)

        spacing = ' ' * self.word_spacing
        self.context.show_text(spacing.join(self.forms))
        self.context.stroke()

        # extracts the relations between the words of the sentence ex.:
        # [(A, B), (1, 2), (3, 4), (3, 5)]
        # word A has a relation to word B
        links = [(r.word_start, r.word_end) for r in self.relations]

        # for each word in the sentence it will generate the necessary information
        # for drawing the arcs that spawn from it
        # it starts from the left of the sentence and draws all the arcs to
        # subsequent words, it does NOT draw from father/head to child, it draws
        # from the first word from the left to the word to its right
        for idx, word in enumerate(self.forms):

            # searches for relations that start from the current word
            for relation in self.relations:
                if relation.word_start == idx + 1:

                    # relations on the starting and ending word
                    relation.relations_start = 0
                    relation.relations_end = 0

                    # stores the relations that come from the
                    # LEFT and RIGHT to the STARTing or ENDing word of an arc:
                    #
                    #                              START RIGHT Relations
                    #                 _____________________________
                    # START LEFT     /_______________________       \
                    #  _________    // ______________        \       \
                    #           \  || /              \        \       \
                    #           |  |||               |        |       |
                    #         WORD_START (A)      WORD_END   WORD (B)  WORD (C)
                    #
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

                    self.draw_arc(relation)

        if self.show_tags:

            # prepares the text stroke as grey
            self.context.select_font_face('monospace',
                                            cairo.FONT_SLANT_NORMAL,
                                            cairo.FONT_WEIGHT_NORMAL)
            self.context.set_font_size(self.font_size)
            self.context.set_source_rgb(0.7, 0.7, 0.7)

            # for each word, retrieves the tags to write
            # writes the tags from bottom to up
            x = self.padding_left
            for t in self.sentence:
                # reset height of bottom tag
                y = self.height - 10
                for field in [t.feats, t.lemma, t.cpostag]:

                    # writes tag
                    self.context.move_to(x, y)
                    self.context.show_text(field)
                    self.context.stroke()

                    y -= 20

                # moves the x coordinate to the same x has the next word
                x += (len(t.form) + self.word_spacing) * self.letter_width


    def draw_arc(self, relation):
        """
        Draws an arc with annotation and an arrow to signal direction
        """

        arrow_length = 3
        self.context.set_line_width(1.2)

        # for simplification
        word_start = relation.word_start
        word_end = relation.word_end
        word_spacing = self.word_spacing

        relations_start = relation.relations_start
        relations_end = relation.relations_end

        # calculates the space from left to the first and last word
        letters = sum([len(w) for w in self.forms[:word_start - 1]])
        start = (((word_start - 1) * word_spacing) + letters) * self.letter_width

        letters = sum([len(w) for w in self.forms[:word_end - 1]])
        end = (((word_end - 1) * word_spacing) + letters) * self.letter_width

        # the slot represents the arcs entries and exit's a word can have
        # the starting slot always takes into account previous arcs that may
        # have ended in the slot's word (always at its left)
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

        # same as previous but for the ending word slot
        starts = sorted([s for (s, e) in relation.relations_end_left
                        if e == relation.word_end])
        for idx, source in enumerate(starts):
            if source == relation.word_start:
                end_slot += len(starts) - idx - 1
                break

        # counts space of the start and end word
        total_start = len(self.forms[word_start - 1]) * self.letter_width
        total_end = len(self.forms[word_end - 1]) * self.letter_width

        # divides the total space given to the word for each slot
        start += (total_start // (relations_start + 1)) * (start_slot + 1) - 1
        end += (total_end // (relations_end + 1)) * (end_slot + 1) - 3

        # coordinates of the center of the arc
        x = self.padding_left + start + 3
        if self.show_tags:
            y = self.height - self.arc_base_height - self.tags_height
        else:
            y = self.height - self.arc_base_height
        xc = x + self.radius
        yc = y - (20 * relation.distance)

        # draws the arrow at the end word
        if(relation.origin == relation.word_end):
            self.context.move_to(xc - self.radius - arrow_length,
                                y - arrow_length - self.bheight)
            self.context.line_to(xc - self.radius, y - self.bheight)
            self.context.line_to(xc - self.radius + arrow_length,
                                y - arrow_length - self.bheight)
            self.context.stroke()

        # draws line from the starting word to its arc
        self.context.move_to(x, y - self.bheight)
        self.context.line_to(x, yc)
        self.context.stroke()

        # draws the arc of the starting word
        angle1 = 3.14
        angle2 = -1.57
        self.context.arc(xc, yc, self.radius, angle1, angle2)

        # puts the x coordinate in the center of the ending word
        # note that there is NOT a context.stroke() between the drawing of the
        # arcs, this is done on purpose so a line from the first arc is draw to
        # the second arc
        xc = end

        # draws the arc of the ending word
        angle1 = -1.57
        angle2 = 0
        self.context.arc(xc, yc, self.radius, angle1, angle2)
        self.context.stroke()

        # draws line from the second arc to the ending word
        self.context.move_to(xc + self.radius, y - self.bheight)
        self.context.line_to(xc + self.radius, yc)
        self.context.stroke()

        # draws the arrow at the end
        if(relation.origin == relation.word_start):
            self.context.move_to(xc + self.radius - arrow_length,
                                y - arrow_length - self.bheight)
            self.context.line_to(xc + self.radius, y - self.bheight)
            self.context.line_to(xc + self.radius + arrow_length,
                                y - arrow_length - self.bheight)
            self.context.stroke()

        # draws the annotation centered
        self.context.set_font_size(self.font_annotation_size)
        c = (x + self.radius) + ((xc - (x + self.radius)) / 2)
        c = c - ((len(relation.annotation) / 2) * self.letter_width) + 3
        self.context.move_to(c,  yc - 5)
        self.context.show_text(relation.annotation.upper())
        self.context.stroke()

    def save_png(self, filename):
        self.surface.write_to_png(filename)

    def as_png(self):
        self.surface.write_to_png(filename)

    def save_buffer(self):
        img_buff = BytesIO()
        self.surface.write_to_png(img_buff)
        return base64.b64encode(img_buff.getvalue()).decode()

    def get_relations(self):
        """
        Create a list of relations (arcs)
        """
        relations = [
            Relation(token) for token in self.sentence
            if token.deprel != "_"
        ]

        # defines the distance of the arc, which influence the height of the arc,
        # from smallest distance relation to highest
        relations.sort(key=lambda r: r.distance)
        for relation in relations:
            distances = set()
            # stores all word distances and counts the uniques
            # this value plus one is the maximum height of the
            # arc needed to represent the actual relation
            for sub_relation in relations:
                if relation != sub_relation:
                    if sub_relation.word_start >= relation.word_start:
                        if sub_relation.word_end <= relation.word_end:
                            distances.add(sub_relation.distance)
            relation.distance = len(distances) + 1
        return relations


def main():
    import signal, sys
    signal.signal(signal.SIGPIPE, signal.SIG_DFL)
    for sentence_id, _, tokens in read_input(sys.stdin):
        graph = DependencyGraph(tokens)
        graph.draw()
        graph.save_png(sentence_id + ".png")


if __name__ == "__main__":
    main()
