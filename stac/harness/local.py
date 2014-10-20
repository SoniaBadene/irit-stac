# pylint: disable=W0105
"""
Paths and settings used for this experimental harness
In the future we may move this to a proper configuration file.
"""

# Author: Eric Kow
# License: CeCILL-B (French BSD3-like)

import itertools

from educe.stac.sanity.main import STAC_REVIEWERS

from attelo.harness.config import\
    LearnerConfig,\
    DecoderConfig,\
    EvaluationConfig

LOCAL_TMP = 'TMP'
"""Things we may want to hold on to (eg. for weeks), but could
live with throwing away as needed"""

SNAPSHOTS = 'data/SNAPSHOTS'
"""Results over time we are making a point of saving"""

TRAINING_CORPORA = ['data/pilot',
                    'data/socl-season1',
                    'data/socl-season2']
"""Corpora for use in building/training models and running our
incremental experiments. Later on we should consider using the
held-out test data for something, but let's make a point of
holding it out for now.

Note that by convention, corpora are identified by their basename.
Something like `data/socl-season1` would result
in a corpus named "socl-season1". This could be awkward if the basename
is used in more than one corpus, but we can revisit this scheme as
needed.
"""

ALL_CORPUS = 'all'
"""
name for a distinguished virtual corpus combining all the other corpora
(generated by the harness)
"""

EVALUATION_CORPORA = [ALL_CORPUS] + TRAINING_CORPORA
"""
which of the corpora to run the evaluation on
"""

LEX_DIR = "data/resources/lexicon"
"""
Lexicons used to help feature extraction
"""

ANNOTATORS = "(?i)" + "|".join(STAC_REVIEWERS)
"""
Which annotators to read from during feature extraction
"""

TAGGER_JAR = 'lib/ark-tweet-nlp-0.3.2.jar'
"POS tagger jar file"


CORENLP_DIR = 'lib/stanford-corenlp-full-2013-06-20'
"CoreNLP directory"


CORENLP_SERVER_DIR = "lib/corenlp-server"
"corenlp-server directory (see http://github.com/kowey/corenlp-server)"


CORENLP_ADDRESS = "tcp://localhost:5900"
"0mq address to server"


LEARNERS = [LearnerConfig.simple("bayes"),
            LearnerConfig.simple("maxent")]
"""Attelo learner algorithms to try (probably along with variations in
configuration settings)

If the second element is None, we use the same learner for attachment
and relations; otherwise we use the first for attachment and the second
for relations
"""

DECODERS = [DecoderConfig.simple(x) for x in
            ["last", "local", "locallyGreedy", "mst"]]
"""Attelo decoders to try in experiment"""


WINDOW = 5
"""
Limited extracted EDUs to those separated by at most WINDOW EDUs.
Adjacent EDUs are separated by 0.

Note that you can set this to -1 to disable windowing algother.
"""


# TODO: make this more elaborate as the configs get more complicated
def _mk_econf_name(learner, decoder):
    """
    generate a short unique name for a learner/decoder combo
    """
    rname = learner.relate
    lname = learner.attach + ("_R_" + rname if rname else "")

    return "%s-%s" % (lname, decoder.name)


EVALUATIONS = [EvaluationConfig(name=_mk_econf_name(l, d),
                                learner=l,
                                decoder=d) for l, d in
               itertools.product(LEARNERS, DECODERS)]
"""Learners and decoders that are associated with each other.
The idea her is that if multiple decoders have a learner in
common, we will avoid rebuilding the model associated with
that learner.  For the most part we just want the cartesian
product, but some more sophisticated learners depend on the
their decoder, and cannot be shared
"""

MODELERS = [EvaluationConfig(name=l.name,
                             learner=l,
                             decoder=None)
            for l in LEARNERS]
"""
Like evaluations modulo decoders.

For now in practice, this is identical to LEARNERS, but if we
are to introduce decoder-based learners, this would change
slightly to accomodate those. Most learners would be decoder
indepnedent, save the decoder-based ones which would vary
accordingly
"""


ATTELO_CONFIG_FILE = "code/parser/stac-features.config"
"""Attelo feature configuration"""
