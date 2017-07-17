__author__ = 'kenneth'


corpus = PPCHEParseCorpusReader("test", "test.psd")
corpus3 = PPCHEParseCorpusReader("test", "recursive_coding.psd")

def test1():
    print('sents')
    for token in corpus.sents():
        print(token)

    print('parsed_sents')
    for token in corpus.parsed_sents():
        print(token)

    print('parsed_coded_sents')
    for token in corpus.parsed_coded_sents():
        print(token)

def test2():
    for token in corpus.parsed_coded_sents():
        id = "N/A"
        text = "N/A"
        tree = "N/A"
        for subtree in token:
            if subtree.node == "ID":
                id = subtree[0]
            elif subtree.node == "CODING":
                pass
            elif subtree.node == "META":
                pass
            else:
                text = ' '.join(subtree.leaves())
                tree = str(subtree)
        print(" | ".join([id, text, tree]))

def test3():
    target_label = "NP"

    print("ID | SentText | NodeText | CodingString")
    for token in corpus3.parsed_coded_sents():
        id = "???"
        sent_text = "???"
        sent_tree = None
        for subtree in token:
            if subtree.node == "ID":
                id = subtree[0]
            elif subtree.node == "CODING":
                pass
            elif subtree.node == "META":
                pass
            else:
                sent_tree = subtree
        print(repr(sent_tree))
        sent_text, node_results = extract_coded_nodes(sent_tree, target_label)
        for node_text, coding_string in node_results:
            print(" | ".join([id, sent_text, node_text, coding_string]))


def extract_coded_nodes(t, target_label):
    node_text = ""
    node_results = []
    coding_string = ""
    remainder = t

    # check that the node is coded
    # if so, the first child will be a coding node
    if re.search("CODING", t[0].node):
        coding_string = t[0][0]
        remainder = t[1:]

    # accumulate text and results from child nodes
    for child in remainder:
        if child.height() == 2:
            # reached a word node
            node_text += ' ' + child[0]
        else:
            # this is a phrasal node
            child_text, child_results = extract_coded_nodes(child, target_label)
            node_text += child_text
            node_results.extend(child_results)

    # check if the node has the target label; if so, ensure that it is coded
    if t.node == target_label:
        if not coding_string == "":
            node_results.append((node_text, coding_string))
        else:
            raise NotCodedError()

    return node_text, node_results