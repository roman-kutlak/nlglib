"""Module for English grammar constructors, rules and """
from nlglib.lexicon import feature as f
from nlglib.spec.phrase import CoordinatedPhraseElement, AdjectivePhraseElement, AdverbPhraseElement
from nlglib.spec.phrase import NounPhraseElement, VerbPhraseElement, PrepositionPhraseElement, Clause


class English:
    """Main class containing English language constructs and rules"""

    category_to_clause = {
        f.category.ADJECTIVE_PHRASE: AdjectivePhraseElement,
        f.category.ADVERB_PHRASE: AdverbPhraseElement,
        f.category.NOUN_PHRASE: NounPhraseElement,
        f.category.PREPOSITIONAL_PHRASE: PrepositionPhraseElement,
        f.category.VERB_PHRASE: VerbPhraseElement,
    }

    def __init__(self, lexicon, processor_order=None, **processors):
        self.lexicon = lexicon
        self.processors = processors
        self.processor_order = processor_order
        for processor, instance in processors.items():
            setattr(self, processor, instance)

    def __call__(self, element, **kwargs):
        return self.process(element, **kwargs)

    def process(self, element, **kwargs):
        value = element
        processor_order = self.processor_order or self.processors.keys()
        for processor_name in processor_order:
            processor = self.processors.get(processor_name)
            if not processor:
                continue
            value = processor(value, **kwargs)
            if not value:
                return ''
        return value

    # simple element constructors
    
    def word(self, string, category=f.category.ANY, **features):
        w = self.lexicon.first(string, category)
        w.features.update(features)
    
    def symbol(self, string, **features):
        w = self.lexicon.first(string, category=f.category.SYMBOL, **features)
        w.features.update(features)

    def adjective(self, string, **features):
        return self.word(string, category=f.category.ADJECTIVE, **features)

    def adverb(self, string, **features):
        return self.word(string, category=f.category.ADVERB, **features)

    def auxiliary(self, string, **features):
        return self.word(string, category=f.category.AUXILIARY, **features)

    def conjunction(self, string, **features):
        return self.word(string, category=f.category.CONJUNCTION, **features)
    
    def complementiser(self, string, **features):
        return self.word(string, category=f.category.COMPLEMENTISER, **features)

    def determiner(self, string, **features):
        return self.word(string, category=f.category.DETERMINER, **features)

    def noun(self, string, **features):
        return self.word(string, category=f.category.NOUN, **features)

    def modal(self, string, **features):
        return self.word(string, category=f.category.MODAL, **features)

    def particle(self, string, **features):
        return self.word(string, category=f.category.PARTICLE, **features)

    def preposition(self, string, **features):
        return self.word(string, category=f.category.PREPOSITION, **features)

    def pronoun(self, string, **features):
        return self.word(string, category=f.category.PRONOUN, **features)

    def verb(self, string, **features):
        return self.word(string, category=f.category.VERB, **features)

    # phrase constructors

    def _phrase(self, category, head, *complements, **features):
        cls = self.category_to_clause.get(category)
        if not cls:
            raise ValueError(f"Unknown category f{category}")
        p = cls(lexicon=self.lexicon)
        p.head = head
        p.features.update(features)
        for c in complements:
            p.add_complement(c)
        return p
    
    def adjective_phrase(self, head, *complements, **features):
        return self._phrase(f.category.ADJECTIVE_PHRASE, head, *complements, **features)

    def adverb_phrase(self, head, *complements, **features):
        return self._phrase(f.category.ADVERB_PHRASE, head, *complements, **features)

    def noun_phrase(self, *words, **features):
        p = NounPhraseElement(lexicon=self.lexicon)
        p.features.update(features)
        if not words:
            return p
        if len(words) == 1:
            p.head = words[0]
        elif len(words) == 2:
            p.specifier, p.head = words
        else:
            spec = words[0]
            noun = words[-1]
            modifiers = words[1:-1]
            p.specifier, p.head = spec, noun
            for m in modifiers:
                p.add_modifier(m)
        p.features.update(features)
        return p

    def preposition_phrase(self, head, *complements, **features):
        return self._phrase(f.category.PREPOSITIONAL_PHRASE, head, *complements, **features)

    def verb_phrase(self, head, *objects, **features):
        return self._phrase(f.category.VERB_PHRASE, head, *objects, **features)

    def clause(self, subject, verb, *objects, **features):
        c = Clause(lexicon=self.lexicon)
        c.subject = subject
        c.verb_phrase = verb
        for o in objects:
            c.verb_phrase.add_complement(o)
        c.features.update(features)
        return c

    def coordination(self, *coordinates, **features):
        cc = CoordinatedPhraseElement(lexicon=self.lexicon)
        cc.features.update(**features)
        for c in coordinates:
            cc.add_coordinate(c)
