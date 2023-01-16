import spacy
from spacy.matcher import Matcher
from spacy.matcher import PhraseMatcher
import json
import inflect
import sys



def article_inserter(sent, nlp):
    """Take the input sentence and a spaCy model (the latter is needed for processing
    the sentence) and return a list of sentences in which missing articles are restored.
    """
    alt_sents = []
    
    # Identify the parameters of the missing articles: 
    # their position and the possible types ("a", "an", or "the")
    article_parameters = article_param_identifier(sent, nlp)

    # Form a list sentences where missing articles are inserted to the corresponding positions    
    doc_to_insert = nlp(sent)
    for ind, articles in article_parameters: 
        for art in articles: 
    
            # Insert an article in the sentence
            if ind > 0:
                right_sent_end = doc_to_insert[ind:].text
                left_sent_end = doc_to_insert[:ind].text
                alt_sent = " ".join([left_sent_end, art, right_sent_end])

            # If an article is in the beginning of the sentence  
            # capitalize it and lower the following word
            else:
                right_sent_end = doc_to_insert[ind:].text
                right_sent_end = right_sent_end.replace(right_sent_end[0], right_sent_end[0].lower(), 1)
                art = art.capitalize()
                alt_sent = " ".join([art, right_sent_end])

            alt_sent = alt_sent.strip()
            alt_sents.append(alt_sent)
        
    return alt_sents


def article_param_identifier(sent, nlp):
    """Process noun chunks in a sentence and check if an article 
    is required in each case. Return a list of tuples containing 
    a start index of noun chunk that requires an article and the list of 
    articles that are possible with this noun chunk. If no article is
    missing in a sentence, return an empty list.
    """
    article_parameters = []
    
    # Create a spaCy object
    doc = nlp(sent)

    # Find noun chunks in a sentence
    noun_chunks = doc.noun_chunks

    # Create objects for matching detection
    phrase_matcher = PhraseMatcher(doc.vocab)
    matcher = Matcher(doc.vocab)

    # An object needed to correctly indentify an indefinite article
    p = inflect.engine()
    
    for nchunk in noun_chunks:        
        
        # For the noun chunks headed by nouns
        if nchunk.root.pos_ == "NOUN":
            
            # Filter out nouns that cannot be used with articles
            if no_article_needed(nchunk, matcher, phrase_matcher, nlp): 
                continue
                
            # Cases where only definite article is required  
            elif def_article_is_required(nchunk, matcher, phrase_matcher, nlp):
                article_position = nchunk.start
                articles = ['the']
                article_parameters.append((article_position, articles))

            # Cases where only indefinite article is required  
            elif indef_article_is_required(nchunk, matcher, phrase_matcher, nlp):
                article_position = nchunk.start
                first_word = doc[article_position].text
                indef_article = p.a(first_word).split()[0]
                articles = [indef_article]
                article_parameters.append((article_position, articles))


            # Cases where some article is required and both articles can be used
            elif some_article_is_required(nchunk, matcher, phrase_matcher, nlp):
                article_position = nchunk.start
                first_word = doc[article_position].text
                indef_article = p.a(first_word).split()[0]
                articles = [indef_article, 'the']
                article_parameters.append((article_position, articles))

            else: 
                continue

        # For the noun chunks headed by proper nouns
        elif nchunk.root.pos_ == "PROPN": 

            if propn_def_article_is_required(nchunk, matcher, phrase_matcher, nlp):
                article_position = nchunk.start
                articles = ['the']
                article_parameters.append((article_position, articles))
            else: 
                continue
        else: 
            continue
       
    return article_parameters
    

def no_article_needed(nchunk, matcher, phrase_matcher, nlp): 
    """Return True for the noun chunk that should not 
    occur with an article. Otherwise, return False. 
    """

    # Rule out noun phrases that already have determiners, specifiers, possessive modifiers
    pattern_determiners = [{"TAG": 
                            {"IN":
                              ["DT",    # determiner
                               "WDT",   # wh-determiner 
                               "PRP$",  # possessive pronoun 
                               "WP",    # personal wh-pronoun
                               "CD"     # cardinal number 
                              ]}}]

    matcher.add("DETERMINERS", [pattern_determiners])
    if len(matcher(nchunk)) > 0:
        return True

    # Rule out noun phrases in plural
    try:
        nchunk_number = nchunk.root.morph.get("Number")[0]
    except IndexError:
        nchunk_number = ""

    if nchunk_number == "Plur": 
        # Exclude the construction 'all of the X' in which the definite article is required
        pattern_all_of = [{"LOWER": "all"}, {"TEXT": "of"}] 
        matcher.add("ALL_OF", [pattern_all_of])
        left_items = nchunk.doc[nchunk.root.head.head.i : nchunk.start]
        if len(matcher(left_items)) > 0:
            return False
        else:
            return True
    
    # Rule out non-countable nouns
    else:
        with open("wordlists/noncount_nouns.json", encoding="utf8") as f:
            NONCOUNT_NOUNS = json.loads(f.read())
            phrase_matcher.add("NONCOUNT_NOUNS", list(nlp.pipe(NONCOUNT_NOUNS)))

            root_token = nchunk.root
            if len(phrase_matcher(nchunk)) > 0:
                return True
            else: 
                return False

            

def def_article_is_required(nchunk, matcher, phrase_matcher, nlp): 
    """Return True if the noun chunk specifically 
    requires a definite article. Otherwise, return False.
    """
    
    # If the adjective in superlative form is present
    patterns_superlative = [[{"TAG": "JJS"}],[{"TAG": "RBS"}]]

    matcher.add("SUP_FORMS", patterns_superlative)
    if len(matcher(nchunk)) > 0: 
        return True
    
    # If ordinal adjective ('first', 'second' etc is present)
    pattern_ordinal = [{"ENT_TYPE": "ORDINAL"}]
    matcher.add("ADJ_ORDINAL", [pattern_ordinal])
    if len(matcher(nchunk)) > 0: 
        return True    
    
    # For noun phases in plural (this is only allowed for a construction 'all of the X')
    try: 
        nchunk_number = nchunk.root.morph.get("Number")[0]
    except IndexError: 
        return False

    if nchunk_number == "Plur": 
        return True
    else:
        return False


def indef_article_is_required(nchunk, matcher, phrase_matcher, nlp): 
    """Return True if the noun chunk specifically 
    requires an indefinite article. Otherwise, return False.
    """
    
    # Noun with an adjective in a predicative position
    pattern_adj_predicative = [{"DEP": "amod"}, {"POS": "NOUN", "DEP": "attr"}]
    matcher.add("ADJ_PRED", [pattern_adj_predicative])
    if len(matcher(nchunk)) > 0: 
        return True

     # Gradable adjectives modifiers
    with open("wordlists/degree_adv.json", encoding="utf8") as f:
        DERGEE_ADV = json.loads(f.read())
    
    patterns_degree_adv = []
    for dadv in DERGEE_ADV:
        pattern = [{"LOWER" : dadv}, {"DEP": "amod"}]
        patterns_degree_adv.append(pattern)
                                           
    matcher.add("DEGREE_ADV", patterns_degree_adv)
    if len(matcher(nchunk)) > 0: 
        return True
    
    # Measurement words ("a litre", "a pair", etc)
    with open("wordlists/measurements.json", encoding="utf8") as f:
        MEASURE_WORDS = json.loads(f.read())
        phrase_matcher.add("MEASUREMENTS", list(nlp.pipe(MEASURE_WORDS)))               
        if len(phrase_matcher(nchunk)) > 0:
            return True
        else: 
            return False
        

def some_article_is_required(nchunk, matcher, phrase_matcher, nlp): 
    """Return True if the noun chunk requires an article and both 
    definite ('the') and indefinite ('a'/'an') articles are possible. 
    Otherwise, return False.
    """

    # Noun chunks in predicative position 
    if nchunk.root.dep_ == "attr": 
        return True

    # The noun is modified by a relative clause or other dependents to the right of the noun chunk
    right_context = [token.text for token in nchunk.subtree if token.i >= nchunk.end]
    if len(right_context) > 0:
        return True
    
    # Relational nouns
    with open("wordlists/relational_nouns.json", encoding="utf8") as f:
        REL_NOUNS = json.loads(f.read())
        phrase_matcher.add("REL_NOUNS", list(nlp.pipe(REL_NOUNS)))
        if len(phrase_matcher(nchunk)) > 0: 
            return True
        
    # Subject or object position
    root_token = nchunk.root
    root_dep = nchunk.root.dep_
    if root_dep in ["nsubj", "nsubjpass", "dobj", "dative"]: 
        return True
            
    # For object of prepositions if they immediately follow the verb (but not a participle!) with a preposition  
    elif root_dep in ["pobj"]: 
        pattern_prep_argument = [{"POS": "VERB", "TAG" : {"NOT_IN": ["VBG", "VBN"]}}, {"DEP": "prep"}]
        matcher.add("PREP_ARG_PATTERN", [pattern_prep_argument])

        # The part of a sentence from the verb to the noun chunk
        left_items = nchunk.doc[nchunk.root.head.head.i : nchunk.start]
        matches = matcher(left_items)
        if len(matches) > 0:
            return True 
        else: 
            return False

    else: 
        return False


def propn_def_article_is_required(nchunk, matcher, phrase_matcher, nlp): 
    """For noun chunks headed by proper nouns (PROPN). 
    Return True if the noun chunk requires a definite article. 
    """

    ent_type = nchunk.root.ent_type_
    # If the proper noun is not identified as an entity, the article is not needed
    if ent_type == '': 
        return False
    
    else: 
        # If the proper noun is of the type that typically goes with a definite article, add an article
        if ent_type in ["EVENT", "LOC", "WORK_OF_ART", "FAC"]: 
            return True

        # For geo-political entities, add articles to those entities that require it 
        elif ent_type == "GPE": 
            with open("wordlists/countries_w_articles.json", encoding="utf8") as f:
                ART_COUNTRIES = json.loads(f.read())
                phrase_matcher.add("ART_COUNTRIES", list(nlp.pipe(ART_COUNTRIES)))
                if len(phrase_matcher(nchunk)) > 0: 
                    return True
                else: 
                    return False
        else:
            return False


def main():
    sent = sys.argv[1]
    nlp = spacy.load("en_core_web_sm")
    alt_sents = article_inserter(sent, nlp)

    print(alt_sents)
    return alt_sents

if __name__ == "__main__":
    main()
    


