import sys
import re
import logging

from nltk.tree import Tree
from nltk.corpus.reader import BracketParseCorpusReader
from nltk.corpus.reader.util import concat, StreamBackedCorpusView
from util import read_regexp_block2, read_comment_block


class CodedTree(Tree):
    def __init__(self, label, children=None):
        self.id = None
        self.coding_str = None
        self.metadata = None
        self.main = None

        # print("processing node [{}] and children [{}]".format(node_or_str,
        #       ','.join(str(child) for child in children)))
        if children is not None:
            # extract ID/CODING/META nodes
            for child in children:
                if not isinstance(child, CodedTree):
                    pass
                elif re.search("CODING", child.node):
                    self.coding_str = child[0]
                elif re.match("ID", child.node):
                    self.id = child[0]
                elif re.match("META", child.node):
                    self.meta = child

        # convert CODING/ID/META nodes to class AnnotationNode
        children = [AnnotationNode(t) if isinstance(t, CodedTree)
                    and re.search("CODING|ID|META", t.node) else t
                    for t in children]

        if label == "":
            # assume this is a wrapper node
            # make a shortcut to the main tree
            for t in children:
                if isinstance(t, CodedTree):
                    self.main = t
                    break

        # else:
        Tree.__init__(self, label, children)

    def leaves(self):
        """
        Return the leaves of the tree, minus any annotation nodes.
        """
        leaves = []
        for t in self:
            if isinstance(t, AnnotationNode):
                pass
            elif isinstance(t, CodedTree):
                leaves.extend(t.leaves())
            else:
                leaves.append(t)
        return leaves

class AnnotationNode():
    def __init__(self, t):
        # Tree.__init__(self, t.node, t)
        self.node = t.node
        self.children = t[:]

    def __repr__(self):
        return '({} {})'.format(self.node, ' '.join(str(t) for t in self.children))

class PPCHEParseCorpusReader(BracketParseCorpusReader):

    """
    Specialized version of the standard BracketParseCorpusReader.

    Handles CODE, ID, CODING-*, and META nodes as well as /* */ and /~* *~/
    block comments.

    Modified behavior:
        _parse(), _tag(), and _word() extended to remove non-text nodes
        _read_block() is overriden to allow block comments to be skipped

    Additional public methods:
        parsed_coded_sents()
    """

    def parsed_coded_sents(self, fileids=None):
        """Return trees, retaining ID/CODING/META nodes and outer brackets.

        Resulting trees may contain up to children of the root node:
            ((META ...) (CODING ...) (<RootLabel> ...) (ID ...))

        Outer brackets are retained even 
        """
        reader = self._read_parsed_coded_sent_block
        return concat([StreamBackedCorpusView(fileid, reader, encoding=enc)
                       for fileid, enc in self.abspaths(fileids, True)])

    def _read_parsed_coded_sent_block(self, stream):
        return list(filter(None, [self._parse_coded(t)
                                  for t in self._read_block(stream)]))

    def _parse_coded(self, t):
        """Parse a CodedTree."""
        # Do parse work from BracketParseCorpusReader minus normalization
        # This is necessary because normalization removes top level empty
        #   brackets, which doesn't work when there is an ID/CODING/META node
        #   in addition to the actual sentence.
        try:
            return CodedTree.parse(t)
        except ValueError as e:
            sys.stderr.write("Bad tree detected; trying to recover...\n")
            sys.stderr.write("  Recovered by returning a flat parse.\n")
            return CodedTree('S', self._tag(t))

    def _parse(self, t):
        t = self._remove_non_text_nodes(t)
        return BracketParseCorpusReader._parse(self, t)

    def _tag(self, t, tagset=None):
        t = self._remove_non_text_nodes(t)
        return BracketParseCorpusReader._tag(self, t)

    def _word(self, t):
        t = self._remove_non_text_nodes(t)
        return BracketParseCorpusReader._word(self, t)

    def _remove_non_text_nodes(self, t):
        """Remove CODE, ID, CODING, and META nodes."""
        return re.sub(r'(?u)\((CODE|ID|CODING|META)[^)]*\)', '', t)

    def _read_block(self, stream):
        # ignore comment and sentence blocks
        comments = []
        while True:
            blocks = read_comment_block(stream, start_re=re.escape('/*'),
                    end_re=re.escape('*/'))
            blocks.extend(read_comment_block(stream, start_re=re.escape('/~*'),
                    end_re=re.escape('*~/')))
            if blocks == []:
                break
            comments.extend(blocks)

        # Tokens start with unindented left parens.
        toks = read_regexp_block2(stream,
                                 start_re=r'^\(',
                                 end_re='|'.join([re.escape('/*'),
                                                 re.escape('/~*')]))
        # Strip any comments out of the tokens.
        if self._comment_char:
            toks = [re.sub('(?m)^%s.*'%re.escape(self._comment_char),
                           '', tok)
                    for tok in toks]
        return toks
