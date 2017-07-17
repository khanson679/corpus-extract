#!/usr/bin/env python

"""
Extract info from a parsed (and coded) corpus and format it as a spreadsheet.
"""

from __future__ import print_function
import sys
import os
import logging
import re
from collections import OrderedDict

from docopt import docopt
from nltk.data import FileSystemPathPointer
import progressbar as pb

from ppche import PPCHEParseCorpusReader

__author__ =  "Kenneth Hanson"
__version__ = "0.1.0"
__date__ =    "5/14/2014"

usage = """
CorpusExtract v{version}
By Kenneth Hanson

Usage:
  corpusextract.py [options] NODE (INFILE... | -d DIR [-f FILTER]) [-o OUTFILE]
  corpusextract.py (-h | --help)
  corpusextract.py --version

Examples:
  corpusextract.py NP-SBJ corpus1.cod corpus2.cod -o np-sbj.ss.txt
  corpusextract.py "NP-*" -d corpus_dir -o np.ss.txt

Arguments:
  NODE     Node label to search for ($ROOT for root, * for wildcard, must be
           quoted to use $ or *)
  INFILE   Input file name (relative to working directory)

Options:
  -h --help     Show this screen.
  --version     Show version.
  -d DIR        Read files in directory (names relative to this directory).
  --debug       Print debug info as well as errors, warnings, and verbose info.
  -f FILTER     Only read files whose names match a regex filter
                  (must be quoted to use wildcards shared by the shell)
  -o OUTFILE    Output file name [default: ce_out.txt]
  -q --quiet    Don't print warnings.
  -s --screen   Print output to screen.
  -v --verbose  Print info beyond warnings and errors.

""".format(version=__version__)

progressbar_widgets = ['Progress: ', pb.Percentage(),
                       ' ', pb.Bar(marker='=', left='[', right=']'),
                       ' ', pb.Timer(), ' ']


class NotCodedError(RuntimeError):
    pass


def load_corpus_by_file(files):
    if not isinstance(files, list):
        raise TypeError("Arg 'files' must be list of strings.")
    return PPCHEParseCorpusReader("", files)


def load_corpus_by_folder(folder, file_filter=""):
    if not isinstance(folder, str):
        raise TypeError("Arg 'folder' must be type 'str'.")
    return PPCHEParseCorpusReader(folder, file_filter)


def extract_nodes(corpus, target_label, showprogress=False):
    """
    Return info for nodes with target label in a dictionary of lists.
    """
    # change target label to regex format
    target_label = re.sub(re.escape('*'), '.*', target_label)

    results = OrderedDict([
        ('ids', []),
        ('node_nums', []),
        ('labels', []),
        ('coding_strings', []),
        ('node_texts', []),
        ('token_texts', [])
    ])

    logging.info("Extracting node '{}' from corpus...".format(target_label))

    parsed_sents = corpus.parsed_coded_sents()
    if showprogress:
        pbar = pb.ProgressBar(widgets=progressbar_widgets,
                              maxval=len(parsed_sents))
        pbar.start()
        progress = 0
        pbar.update(progress)

    # search each tree for (possibly recursively embedded) results
    for token in parsed_sents:
        # extract info shared by all target nodes in tree
        id = token.id if token.id else None
        token_text = ' '.join(token.leaves())

        # find nodes with target label
        if target_label == "$ROOT":
            target_subtrees = [token.main]
        else:
            target_subtrees = list(token.main.subtrees(
                                   filter=lambda t: re.match(t.node,
                                                             target_label)))

        # extract leaf text and coding strings
        labels = [t.node for t in target_subtrees]
        node_texts = [' '.join(t.leaves()) for t in target_subtrees]
        coding_strings = [t.coding_str for t in target_subtrees]
        num_results = len(labels)

        # store info
        results['ids'].extend([id for i in range(num_results)])
        results['node_nums'].extend([i+1 for i in range(num_results)])
        results['token_texts'].extend([token_text for i in range(num_results)])
        results['labels'].extend(labels)
        results['node_texts'].extend(node_texts)
        results['coding_strings'].extend(coding_strings)

        if showprogress:
            progress += 1
            pbar.update(progress)

    if showprogress:
        pbar.finish()

    return results


def print_table(table, label_filter=None, sep='\t', file=sys.stdout):
    """
    Print node info table (formatted as a dict of lists).
    """
    # print table
    print('\t'.join(table.keys()), file=file)
    for entry in zip(*table.itervalues()):
        # TODO: add conditional filter
        print(sep.join([str(cell) for cell in entry]), file=file)


def main():
    """
    Process command line arguments and execute actions.
    """

    #
    # process command line arguments
    #

    args = docopt(usage, version=__version__)

    # process logging options
    if args['--debug']:
        logging.basicConfig(level=logging.DEBUG)
    elif args['--quiet']:
        logging.basicConfig(level=logging.ERROR)
    elif args['--verbose']:
        logging.basicConfig(level=logging.INFO)
    else:
        logging.basicConfig(level=logging.WARNING)

    logging.debug(args)

    # load corpus
    if args['-d']:
        indirname = args['-d']
        filename_filter = args['-f']
        msg = "Loading files from directory '{}'".format(indirname)
        if filter:
            msg += " with filter ' '".format(filter)
        logging.info(msg)
        if not os.path.exists(indirname):
            logging.error("No such directory: '{}'".format(indirname))
            sys.exit(1)
        elif not os.path.isdir(indirname):
            logging.error("Not a directory: '{}'".format(indirname))
            sys.exit(1)
        corpus = load_corpus_by_folder(indirname, filename_filter)
    else:
        logging.info("Loading files: {}".format(args['INFILE']))
        for filename in args['INFILE']:
            if not os.path.exists(filename):
                raise IOError("No such file: '{}'".format(filename))
            elif not os.path.isfile(filename):
                logging.error("Not a file: '{}'".format(filename))
                sys.exit(1)
        corpus = load_corpus_by_file(args['INFILE'])

        # check that file IDs generated from directory and pattern work
        if not corpus.fileids():
            logging.error(
                "No file IDs for combination of directory and filter.")
            sys.exit(1)
        for path in corpus.abspaths():
            try:
                FileSystemPathPointer(path)
            except IOError:
                logging.error("Bad file path generated by directory "
                              "+ filter combination: '{}'".format(path))
                sys.exit(1)

    logging.info("Corpus loaded.")
    logging.debug("Using file IDs: {}".format(corpus.fileids()))

    # configure output
    if args['--screen']:
        # print to screen
        outfile = sys.stdout
        logging.info("Using screen output.")
    else:
        # load output file (see usage message for default)
        outfilename = args['-o']
        try:
            logging.info("Opening output file '{}'...".format(outfilename))
            outfile = open(outfilename, 'w')
        except IOError:
            logging.error(
                "Unable to open output file: '{}'".format(outfilename))
            sys.exit(1)
        else:
            logging.info("Output file loaded.")


    #
    # do work
    #

    try:
        with outfile:
            node_label = args['NODE']
            results = extract_nodes(corpus, node_label, showprogress=True)
            # logging.debug(results)
            print_table(results, file=outfile)

        logging.info("Program ended normally.")
    except Exception:
        logging.error("Program ended on error.", exc_info=True)
        sys.exit(2)

if __name__ == '__main__':
    main()