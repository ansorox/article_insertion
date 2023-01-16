import pytest
import article_insertion as art_in
import spacy
from spacy.matcher import Matcher
from spacy.matcher import PhraseMatcher


@pytest.fixture
def nlp_model(scope="module"):
    """Load an English language model for spaCy."""
    nlp = spacy.load("en_core_web_sm")
    return nlp

# Testing the article_inserter function
various_sentences = [ 
	("Girl came to me.", ["A girl came to me.", "The girl came to me."]),    # capitalization
	("Buy me notebook.", ["Buy me a notebook.", "Buy me the notebook."]),     # choice of the indefinite article
	("Buy me envelope.", ["Buy me an envelope.", "Buy me the envelope."])    # choice of the indefinite article
]

@pytest.mark.parametrize("test_input, expected_output", various_sentences)
def test_article_inserter(test_input, expected_output, nlp_model): 
	result = art_in.article_inserter(test_input, nlp_model)
	assert result == expected_output


# Testing the param_identifier function
mixed_sentences_params = [ 
	("I saw a girl.", []),
	("She bought sugar.", []),
	("A man saw girl.", [(3, ['a', 'the'])]),
	("Matthew saw girl who was singing.", [(2, ['a', 'the'])]),
	("I gave it to ex.", [(4, ['an', 'the'])]),
	("Let's look at int array closer.", [(4, ['an', 'the'])]),
	("I'm going to bed.", []),
	("It's most beautiful city in the world.", [(2, ['the'])]),
	("We visited United States.", [(2, ['the'])]),
	("We visited Brazil.", [])
]

@pytest.mark.parametrize("test_input, expected_output", mixed_sentences_params)
def test_article_param_identifier(test_input, expected_output, nlp_model):
	result = art_in.article_param_identifier(test_input, nlp_model)
	assert result == expected_output



def generate_matcher(nlp_model):
	matcher = Matcher(nlp_model.vocab)
	return matcher

def generate_phrase_matcher(nlp_model):
	phrase_matcher = PhraseMatcher(nlp_model.vocab)
	return phrase_matcher

def get_noun_chunks(nlp_model, sent):
	doc = nlp_model(sent)
	noun_chunks = doc.noun_chunks
	return noun_chunks

def get_function_output(noun_chunks, sent, funct, matchers, nlp_model):
	output = []
	for nchunk in noun_chunks:
		result = funct(nchunk, matchers['matcher'], matchers['phrase_matcher'], nlp_model)
		output.append(result)
	return output


# Testing the no_article_needed function
sent_no_article = [
	("A man saw girl.", [True, False]),
	("A man saw a girl.", [True, True]),
	("I like this actor", [False, True]),    # determiner
	("I've seen my favourite actor today!", [False, True]),    # possessive pronoun
	("She's got one sister.", [False, True]),    # number
	("She has got books.", [False, True]),    # plural
	("She has got all of books.", [False, True, False]),    # all of the X constuction
	("She bought sugar.", [False, True])    # uncountable
]

@pytest.mark.parametrize("test_input, expected_output", sent_no_article)
def test_no_article_needed(test_input, expected_output, nlp_model):
	sent = test_input	
	funct = art_in.no_article_needed
	matcher = generate_matcher(nlp_model)
	phrase_matcher = generate_phrase_matcher(nlp_model)
	matchers = {"matcher": matcher, "phrase_matcher": phrase_matcher}
	noun_chunks = get_noun_chunks(nlp_model, sent)
	output = get_function_output(noun_chunks, sent, funct, matchers, nlp_model)
	assert output == expected_output


# Testing the def_article_is_required function
sent_def_art = [
	("It's greatest city in the world.", [False, True, False]),	# superlative adjective
	("She was most beautiful girl.", [False, True]),	# superlative modifier, most
	("It's least interesting book.", [False, True]),	# superlative modifier, least
	("Sarah is dressing up for first date.", [False, True]), # ordinal 
	("All of students were present.", [False, True])	# all of the X
]

@pytest.mark.parametrize("test_input, expected_output", sent_def_art)
def test_def_article_is_required(test_input, expected_output, nlp_model):
	sent = test_input
	funct = art_in.def_article_is_required
	matcher = generate_matcher(nlp_model)
	matchers = {"matcher": matcher, "phrase_matcher": None}
	noun_chunks = get_noun_chunks(nlp_model, sent)
	output = get_function_output(noun_chunks, sent, funct, matchers, nlp_model)
	assert output == expected_output


# Testing the indef_article_is_required function
sent_indef_art = [
	("The lion is endangered animal.", [False, True]),    # noun with adj in predicative position
	("He bought very expensive piece of furniture for his new apartment.", [False, True, False, False]),    # degree adverb
    ("She has made lot of progress.", [False, True, False])    # measurement word
]

@pytest.mark.parametrize("test_input, expected_output", sent_indef_art)
def test_indef_article_is_required(test_input, expected_output, nlp_model):
	sent = test_input
	funct = art_in.indef_article_is_required
	matcher = generate_matcher(nlp_model)
	phrase_matcher = generate_phrase_matcher(nlp_model)
	matchers = {"matcher": matcher, "phrase_matcher": phrase_matcher}
	noun_chunks = get_noun_chunks(nlp_model, sent)
	output = get_function_output(noun_chunks, sent, funct, matchers, nlp_model)
	assert output == expected_output


# Testing the some_article_is_required function
sent_some_articles_right_context = [
	("Matthew saw girl who was singing.", [True, True, True]), # relative clause
	("Guy in the middle was planning a mutiny.", [True, False, True]),	# prepositional modifier
    ("Woman with a house in London is visiting on Saturday.", [True, True, False, False])	# prepositional modifier
]
sent_some_articles_relnouns = [
	("Put the ring on finger.", [True, True]), # relational noun from the list
	("I gave it to ex.", [True, True, True]) # relational noun from the list
]
sent_some_articles_argument = [
	("Girl came to me.", [True, True]), 	# nsubj
	("My father got new car yesterday.", [True, True]), 	# dobj 
	("She gave postman a letter.", [True, True, True]), 	# dative
	("Let's look at int array closer.", [True, True]), 	# pobj following the verb with preposition
	("She went to beach.", [True, True]), 	# pobj following the verb with preposition
	("She studies business at school.", [True, True, False]), 	# pobj not immediately following the verb with preposition
	("I'm going to bed.", [True, False]) 	# pobj following the ptcp with preposition
]
sent_some_articles_predicative = [
	("He is actor.", [True, True])	# noun in preidicative position
]

sent_some_articles_all = sent_some_articles_right_context + sent_some_articles_relnouns + sent_some_articles_argument + sent_some_articles_predicative

@pytest.mark.parametrize("test_input, expected_output", sent_some_articles_all)
def test_some_article_is_required(test_input, expected_output, nlp_model):
	sent = test_input
	funct = art_in.some_article_is_required
	matcher = generate_matcher(nlp_model)
	phrase_matcher = generate_phrase_matcher(nlp_model)
	matchers = {"matcher": matcher, "phrase_matcher": phrase_matcher}
	noun_chunks = get_noun_chunks(nlp_model, sent)
	output = get_function_output(noun_chunks, sent, funct, matchers, nlp_model)
	assert output == expected_output


# Testing the propn_def_article_is_required function 
sent_propn_def_article = [
	("We visited United States.", [False, True]),	# GPE from the list
	("We wanted to visit Golden Gate.", [False, True]),	# FAC entity identified by the NER
	("It is hard to live in Himalayas.", [False, True]), # LOC entity identified by the NER
	("We visited Brazil.", [False, False]), 	# GPE that's not in the list
	("We visited Andrew.", [False, False])		# PERSON
]

@pytest.mark.parametrize("test_input, expected_output", sent_propn_def_article)
def test_propn_def_article_is_required(test_input, expected_output, nlp_model):
	sent = test_input
	funct = art_in.propn_def_article_is_required
	phrase_matcher = generate_phrase_matcher(nlp_model)
	matchers = {"matcher": None, "phrase_matcher": phrase_matcher}
	noun_chunks = get_noun_chunks(nlp_model, sent)
	output = get_function_output(noun_chunks, sent, funct, matchers, nlp_model)
	assert output == expected_output


