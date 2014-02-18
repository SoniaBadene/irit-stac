# Author: Eric Kow
# License: CeCILL-B (French BSD3)

"""
Visualise discourse and enclosure graphs
"""

import os.path
import sys
import codecs

from educe import stac, graph
from educe.annotation import\
    Annotation
from educe.stac import postag
import educe.corpus
import educe.stac.graph as stacgraph

from stac.util.args import get_output_dir
from stac.util.output import output_path_stub, mk_parent_dirs

class WrappedToken(Annotation):
    """
    Thin wrapper around POS tagged token which adds a local_id
    field for use by the EnclosureGraph mechanism
    """

    def __init__(self, token):
        self.token = token
        anno_id = WrappedToken._mk_id(token)
        super(WrappedToken, self).__init__(anno_id,
                                           token.span,
                                           "token",
                                           {"tag":token.tag,
                                            "word":token.word})

    @classmethod
    def _mk_id(cls, token):
        """
        Generate a string that could work as a node identifier
        in the enclosure graph
        """
        span = token.text_span()
        return "%s_%s_%d_%d"\
                % (token.word,
                   token.tag,
                   span.char_start,
                   span.char_end)

def _stac_enclosure_ranking(anno):
    """
    Given an annotation, return an integer representing its position in
    a hierarchy of nodes that are expected to enclose each other.

    Smaller negative numbers are higher (say the top of the hiearchy
    might be something like -1000 whereas the very bottom would be 0)
    """
    ranking = {"token": -1,
               "edu": -2,
               "turn": -3,
               "dialogue": -4}

    key = None
    if anno.type == "token":
        key = "token"
    elif stac.is_edu(anno):
        key = "edu"
    elif stac.is_turn(anno):
        key = "turn"
    elif stac.is_dialogue(anno):
        key = "dialogue"

    return ranking[key] if key else 0


class StacEnclosureDotGraph(graph.EnclosureDotGraph):
    """
    Conventions for visualising STAC enclosure graphs
    """
    def __init__(self, core):
        super(StacEnclosureDotGraph, self).__init__(core)

    def _unit_label(self, anno):
        span = anno.text_span()
        if anno.type == "token":
            word = anno.features["word"]
            tag = anno.features["tag"]
            return "%s [%s] %s" % (word, tag, span)
        else:
            return "%s %s" % (anno.type, span)

# slightly different from the stock stac-util version because it
# supports live corpus mode
def _read_corpus(args):
    """
    Read and return the corpus specified by the command line arguments
    """
    is_interesting = educe.util.mk_is_interesting(args)
    if args.live:
        reader = stac.LiveInputReader(args.corpus)
        anno_files = reader.files()
    else:
        reader = stac.Reader(args.corpus)
        anno_files = reader.filter(reader.files(), is_interesting)
    return reader.slurp(anno_files, verbose=True)


def _write_dot_graph(k, odir, dot_graph, part=None, run_graphviz=True):
    """
    Write a dot graph and possibly run graphviz on it
    """
    ofile_basename = output_path_stub(odir, k)
    if part is not None:
        ofile_basename += '_' + str(part)
    dot_file = ofile_basename + '.dot'
    svg_file = ofile_basename + '.svg'
    mk_parent_dirs(dot_file)
    with codecs.open(dot_file, 'w', encoding='utf-8') as dotf:
        print >> dotf, dot_graph.to_string()
    if run_graphviz:
        print >> sys.stderr, "Creating %s" % svg_file
        os.system('dot -T svg -o %s %s' % (svg_file, dot_file))


def _main_rel_graph(args):
    """
    Draw graphs showing relation instances between EDUs
    """
    args.stage = 'discourse|units'
    corpus = _read_corpus(args)
    output_dir = get_output_dir(args)

    if args.live:
        keys = corpus
    else:
        keys = [k for k in corpus if k.stage == 'discourse']

    for k in sorted(keys):
        try:
            gra_ = stacgraph.Graph.from_doc(corpus, k)
            if args.strip_cdus:
                gra = gra_.without_cdus()
            else:
                gra = gra_
            dot_gra = stacgraph.DotGraph(gra)
            if dot_gra.get_nodes():
                _write_dot_graph(k, output_dir, dot_gra,
                                 run_graphviz=args.draw)
                if args.split:
                    ccs = gra.connected_components()
                    for part, nodes in enumerate(ccs, 1):
                        gra2 = gra.copy(nodes)
                        _write_dot_graph(k, output_dir,
                                         stacgraph.DotGraph(gra2),
                                         part=part,
                                         run_graphviz=args.draw)
            else:
                print >> sys.stderr, "Skipping %s (empty graph)" % k
        except graph.DuplicateIdException:
            warning = "WARNING: %s has duplicate annotation ids" % k
            print >> sys.stderr, warning


def _main_enclosure_graph(args):
    """
    Draw graphs showing which annotations' spans include the others
    """
    corpus = _read_corpus(args)
    output_dir = get_output_dir(args)
    keys = corpus
    if args.tokens:
        postags = postag.read_tags(corpus, args.corpus)

    for k in sorted(keys):
        annos = [anno for anno in corpus[k].units if anno.type != 'paragraph']
        if args.tokens:
            annos += [WrappedToken(tok) for tok in postags[k]]
        gra_ = graph.EnclosureGraph(annos, key=_stac_enclosure_ranking)
        if args.reduce:
            gra_.reduce()
        dot_gra = StacEnclosureDotGraph(gra_)
        if dot_gra.get_nodes():
            dot_gra.set("ratio","compress")
            _write_dot_graph(k, output_dir, dot_gra,
                             run_graphviz=args.draw)
        else:
            print >> sys.stderr, "Skipping %s (empty graph)" % k

# ---------------------------------------------------------------------
# args
# ---------------------------------------------------------------------

NAME = 'graph'


def config_argparser(parser):
    """
    Subcommand flags.

    You should create and pass in the subparser to which the flags
    are to be added.
    """
    # note: not the usual input args
    parser.add_argument('corpus', metavar='DIR', help='corpus dir')
    parser.add_argument('--output', metavar='DIR', required=True,
                        help='output  dir')
    parser.add_argument('--no-draw', action='store_false',
                        dest='draw',
                        default=True,
                        help='Do not actually draw the graph')
    parser.add_argument('--live', action='store_true',
                        help='Input is a flat collection of aa/ac files)')

    # TODO: would be nice to enforce these groups of args mutually excluding
    # but not sure if the library actually supports it
    psr_rel = parser.add_argument_group("relation graphs")
    psr_rel.add_argument('--split', action='store_true',
                         help='Separate file for each connected component')
    psr_rel.add_argument('--strip-cdus', action='store_true',
                         help='Strip away CDUs (substitute w heads)')

    psr_enc = parser.add_argument_group("enclosure graphs")
    psr_enc.add_argument('--enclosure', action='store_true',
                         help='Generate enclosure graphs')
    psr_enc.add_argument('--reduce', action='store_true',
                         help='Reduce enclosure graphs [requires --enclosure]')
    psr_enc.add_argument('--tokens', action='store_true',
                         help='Include pos-tagged tokens')


    educe_group = parser.add_argument_group('corpus filtering arguments')
    educe.util.add_corpus_filters(educe_group,
                                  fields=['doc', 'subdoc', 'annotator'])
    parser.set_defaults(func=main)


def main(args):
    """
    Subcommand main.

    You shouldn't need to call this yourself if you're using
    `config_argparser`
    """
    if args.enclosure:
        _main_enclosure_graph(args)
    else:
        _main_rel_graph(args)

# vim: syntax=python:
