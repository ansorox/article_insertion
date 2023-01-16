

The script `article_insertion.py` inserts missing articles into the sentence. 


## Overview

The script uses the `spaCy` library to find noun chunks in a sentence. It then analyses them to see if they require an article. It uses the following algorithm:

1. For noun chunks headed by nouns:

    1. <a name="no_article_step"></a>Identify noun chunks that do not (necessarily) need an article:
        
        1. Noun chunks that already contain determiners (articles, demonstratives), specifiers, or possessive pronouns. These kinds of modifiers cannot cooccur with articles.
    
        2. Noun chunks that are used in plural. Exception: the noun chunks that are immediately preceded by 'all of' (as this construction requires a definite article, see below). 

        3. Noun chunks that are headed by uncountable nouns. The (non-exhaustive) list of uncountable nouns is stored in the file `noncount_nouns.json`. This list is taken from a [page](https://ieltsliz.com/uncountable-nouns-word-list/) of the IELTS preparation website where the properties of uncountable nouns in English are discussed. 

	Since in most cases articles are used correctly, most of the noun chunks will be filtered out in this step.

	2. Identify noun chunks that can only be used with a definite article:

	    1. Noun chunks containing adjectives in superlative form ('the biggest X') 
	
	    2. Noun chunks containing ordinal adjectives ('the first X', 'the second X') 
	
	    3. Noun chunks in plural. Only noun chunks that are immediately preceded by 'all of' get to this stage, as all others are filtered out during [the first step](#no_article_step) of the algorithm.


	3. <a name="indef_step"></a>Identify noun chunks that can only be used with an indefinite article:

		1. Noun chunks that are used in predicative position and contain adjectives. These are typically descriptions that
		require an indefinite article. 

		2. Noun chunks containing degree adverbs that modify adjectives ('very', 'extremely', 'slightly'). These adverbs are listed in `degree_adv.json`. 

		3. Words for measurement ('litre', 'bunch', 'pair', etc). These words are listed in `measurements.json`. 

    4.  Identify noun chunks that require an article and allow for both definite and indefinite articles. These cases include: 
    
        1. Noun chunks modified by a relative clause or other dependents to the right of the noun chunk. 
    
    	2. Noun chunks headed by relational nouns. Relational nouns (body parts, kinship terms, part-whole terms, etc) are two-place predicates. They typically require a possessive pronoun or a determiner. The list of relational nouns is stored in `relational_nouns.json`. It was created from [a list of human body parts](https://www.britannica.com/dictionary/eb/3000-words/topic/human-body-parts-external) and [a list of kinship terms](https://www.britannica.com/dictionary/eb/3000-words/topic/family-members) taken from [the Britannica Dictionary page](https://www.britannica.com/dictionary).

    	3. Noun chunks in argument positions (subject, direct object, an argument of a dative verb). We also consider the object of prepositions as verb arguments if they immediately follow the verb (e.g. in 'I looked at X.', but not in 'I saw X at Y'). 
    	
    	4. Noun chunks in predicative position (note that noun chunks containing adjectives are ruled out during [the previous step](#indef_step)).
    	

2. For noun chunks headed by proper names: 
    1. Filter out noun chunks that are not assigned any label by a named entity recognition.
    
    2. Identify proper names that are typically used with a definite article: 

	    1. Historic events, non-GPE locations, works of art, famous constructions.

	    2. Geopolitical entities listed in a file `countries_w_articles.json`. This list was taken from a [paper](https://www.tandfonline.com/doi/full/10.1080/00277738.2020.1731241) on patterns of definite article use with country names. Particularly, from [the table](https://www.tandfonline.com/doi/full/10.1080/00277738.2020.1731241) 'Distribution of country names in relation to definite article use'.  I only took the countries which had  > 50% percentage of definite article use. 

The form of an indefinite article ('a' or 'an') is identified using the `inflect` library. 


## Install

The dependencies are the following: 
* Python3.9
* Python modules: `spacy`, `inflect`, `pytest` (you can use `pip install -r requirements.txt`).
* SpaCy `en_core_web_sm` model for the English language. It can be installed with `python -m spacy download en_core_web_sm`

To run the script enter it in the command line and pass it the sentence that you want to process:
    `python article_insertion.py <str>` 

The tests are located in `test_article_insertion.py`.


## Examples

#### Noun chunks with the right context

	python article_insertion.py "Matthew saw girl who was singing."
	['Matthew saw a girl who was singing.', 'Matthew saw the girl who was singing.']`

	python article_insertion.py "Guy in the middle was planning a mutiny."
	['A guy in the middle was planning a mutiny.', 'The guy in the middle was planning a mutiny.']`

	python article_insertion.py "Woman with a house in London is visiting on Saturday."
	['A woman with a house in London is visiting on Saturday.', 'The woman with a house in London is visiting on Saturday.']

   
#### Relational nouns

	python article_insertion.py "Put the ring on finger."
	['Put the ring on a finger.', 'Put the ring on the finger.']
	
	python article_insertion.py "I gave it to ex."
	['I gave it to an ex.', 'I gave it to the ex.']

#### Nouns that are arguments of the verbs

	#nsubj
	python article_insertion.py "Girl came to me."
	['A girl came to me.', 'The girl came to me.']

	#dobj
	python article_insertion.py "My father got new car yesterday."
	['My father got a new car yesterday.', 'My father got the new car yesterday.']

	#dative
	python article_insertion.py "She gave postman a letter."
	['She gave a postman a letter.', 'She gave the postman a letter.']

	#pobj + immediately follow
	python article_insertion.py "Let's look at int array closer."
	["Let's look at an int array closer.", "Let's look at the int array closer."]

	python article_insertion.py "We went to beach."
	['We went to a beach.', 'We went to the beach.']

	python article_insertion.py "I'm going to bed."
	[]

	#pobj + immediately do not follow
	python article_insertion.py "She studies business at school."
	[]


#### Superlative adjectives and adverbs
	python article_insertion.py "It's greatest city in the world."
	["It's the greatest city in the world."]

	python article_insertion.py "She was most beautiful girl."
	['She was the most beautiful girl.']

	python article_insertion.py "It's least interesting book."
	["It's the least interesting book."]
	

#### Ordinal adjective
	python article_insertion.py "Sarah is dressing up for first date."
	['Sarah is dressing up for the first date.']


#### "All of the X"
	python article_insertion.py "All of students were present."
	['All of the students passed the test.']


#### Noun phrases with degree modifiers and measurement words

	python article_insertion.py "He bought very expensive piece of furniture for his new apartment."
	['He bought a very expensive piece of furniture for his new apartment.']

	python article_insertion.py "She has made lot of progress."
	['She has made a lot of progress.']


#### Noun phrases in predicative position

	python article_insertion.py "He is actor."
	['He is an actor.', 'He is the actor.']


	python article_insertion.py "He is good actor."
	['He is a good actor.']




#### Noun phrases with determiners or other specifiers


#### Noun phrases with determiners or other specifiers

	python article_insertion.py "I like this actor"
	[]

	python article_insertion.py "I've seen my favourite actor today."
	[]

	python article_insertion.py "She's got one sister."
	[]
	


#### Noun phrases in plural 

	python article_insertion.py "She bought books."
	[]

	python article_insertion.py "She bought book." 
	['She bought a book.', 'She bought the book.']


#### Noun phrases headed by uncountable nouns  

	python article_insertion.py "She bought sugar."
	[]
 
#### Some proper nouns: locations, work of arts, historic events, etc

	python article_insertion.py "We wanted to visit Golden Gate."
	['We wanted to visit the Golden Gate.']

	python article_insertion.py "It is hard to live in Himalayas."
	['It is hard to live in the Himalayas.']


#### Countries with articles
	python article_insertion.py "We visited United States."
	['We visited the United States.']

	python article_insertion.py "We visited Brazil."
	[]

	python article_insertion.py "We visited Andrew."
	[]
