from copy import deepcopy


class NLGElement:
    def __init__(self, vname=None):
        self._visitor_name = vname
        self.features = dict()
        self.realisation = ""

    def accept(self, visitor, element='child'):
        """Implementation of the Visitor pattern."""
        if self._visitor_name == None:
            raise ValueError('Error: visit method of uninitialized visitor '
                             'called!')
        # get the appropriate method of the visitor instance
        m = getattr(visitor, self._visitor_name)
        # ensure that the method is callable
        if not hasattr(m, '__call__'):
            raise ValueError('Error: cannot call undefined method: %s on '
                             'visitor' % self._visitor_name)
        # and finally call the callback
        m(self, element)

    def features_to_xml_attributes(self):
        features = ""
        for (k, v) in self.features.items():
            features += '%s="%s" ' % (k, v)
        return features

    def __eq__(self, other):
        if (not isinstance(other, NLGElement)):
            return False
        return (self._visitor_name == other._visitor_name and
                self.features == other.features and
                self.realisation == other.realisation)

    def to_str(self):
        return ""
    
    def __repr__(self):
        text = "[ NLGElement : "
        features = str(self.features)
        if "{}" != features:
            text += "\n\t" + features
        if "" != self.realisation:
            text += "\n\t" + self.realisation
        text += "]"
        return text

    def __str__(self):
        v = StrVisitor()
        self.accept(v)
        return v.to_str()


class String(NLGElement):
    def __init__(self, val=""):
        super().__init__('visit_string')
        self.val = val
    
    def to_xml(self, element):
        text = ('<%s xsi:type="StringElement">'
                '\n\t<val>%s</val>\n</%s>\n'
                % (element, self.val, element))
        return text
    
    def to_str(self):
        return self.val
    
    def __eq__(self, other):
        if (not isinstance(other, String)):
            return False
        return (self.text == other.text)
    
    def __repr__(self):
        return ('[ String : %s ]' % self.val)


class Word(NLGElement):
    def __init__(self, word=None, pos=None):
        super().__init__('visit_word')
        self.word = str(word)
        self.pos = str(pos)

    def to_xml(self, element):
        text = ('<%s xsi:type="WordElement" cat="%s">'
                '\n\t<base>%s</base>\n</%s>\n'
                % (element, self.pos, self.word, element))
        return text
    
    def to_str(self):
        return self.word
    
    def __eq__(self, other):
        if (not isinstance(other, Word)):
            return False
        return (self.word == other.word and
                self.pos == other.pos)
    
    def __repr__(self):
        text = "[ Word : "
        if None is not self.word:
            text += "\n\tword: " + self.word
        if None is not self.pos:
            text += "\n\tPOS : " + self.pos
        
        features = str(self.features)
        if "{}" != features:
            text += "\n\t" + features
        if "" != self.realisation:
            text += "\n\t" + self.realisation
        text += "]"
        return text


class PlaceHolder(NLGElement):
    def __init__(self, id=None, obj=None):
        super().__init__('visit_placeholder')
        self.id = id
        self.object = None

    def to_xml(self, element):
        text = ('<%s xsi:type="StringElement">'
                '\n\t<val>%s</val>\n</%s>\n'
                % (element, str(self.id), element))
        return text

    def to_str(self):
        if (self.object):
            return self.object
        return str(self.id)

    def __eq__(self, other):
        if (not isinstance(other, PlaceHolder)):
            return False
        else:
            return (self.id == other.id and self.object == other.object)

    def __repr__(self):
        return ('PlaceHolder: id = %s' % str(self.id))

    def __str__(self):
        return self.to_str()


class Phrase(NLGElement):
    def __init__(self, type=None, disc_fn=None, vname='visit_phrase'):
        super().__init__(vname)
        self.type = type
        self.disc_fn = disc_fn
        self.front_modifier = list()
        self.pre_modifier = list()
        self.head = None
        self.complement = list()
        self.post_modifier = list()
    
    def add_complements(self, compl):
        if (compl is not None):
            if (isinstance(compl, list)):
                for c in compl:
                    self.complement.append(c)
            else:
                self.complement.append(compl)

    def __eq__(self, other):
        if (not isinstance(other, Phrase)):
            return False
        return (self.type == other.type and
                self.disc_fn == other.disc_fn and
                self.front_modifier == other.front_modifier and
                self.pre_modifier == other.pre_modifier and
                self.head == other.head and
                self.complement == other.complement and
                self.post_modifier == other.post_modifier)
    
    def __repr__(self):
        return ('[ Phrase %s %s:\n\t front: %s\n\t pre: %s'
                '\n\t head: %s\n\t compl: %s\n\t post: %s\n]' %
                (self.type, self.disc_fn,
                 [str(o) for o in self.front_modifier],
                 [str(o) for o in self.pre_modifier],
                 str(self.head),
                 [str(o) for o in self.complement],
                 [str(o) for o in self.post_modifier]))


class Clause(Phrase):
    def __init__(self, subj=None, vp=None):
        super().__init__(type='CLAUSE', vname='visit_clause')
        self.subj = subj
        self.vp = vp

    def to_xml(self, element):
        features = self.features_to_xml_attributes()
        text = '<%s xsi:type="SPhraseSpec" %s>\n' % (element, features)
        return text
    
    def __eq__(self, other):
        if (not isinstance(other, Clause)):
            return False
        return (self.subj == other.subj and self.vp == other.vp)

    def __repr__(self):
        return ('[ Clause :\n\t subject: %s\n\t vp: %s\n]' %
                (str(self.subj), str(self.vp)))


class NP(Phrase):
    def __init__(self, head=None, spec=None):
        super().__init__(type='NOUN_PHRASE', vname='visit_np')
        self.spec = spec
        self.head = head

    def __eq__(self, other):
        if (not isinstance(other, NP)):
            return False
        return (self.spec == other.spec and
                self.head == other.head and
                True == Phrase.__eq__(self, other))

    def to_xml(self, element):
        features = self.features_to_xml_attributes()
        text = '<%s xsi:type="NPPhraseSpec" %s>\n' % (element, features)
        return text


class VP(Phrase):
    def __init__(self, head=None, compl=None):
        super().__init__(type='VERB_PHRASE', vname='visit_vp')
        self.head = head
        self.add_complements(compl)

    def get_object(self):
        for c in self.complement:
            if ('discourseFunction' in c.features and
                c.features['discourseFunction'] == 'OBJECT'):
                return c
        return None

    def remove_object(self):
        compls = list()
        for c in self.complement:
            if ('discourseFunction' in c.features and
                c.features['discourseFunction'] == 'OBJECT'):
                continue
            else:
                compls.append(c)
        self.complement = compls

    def set_object(self, obj):
        self.remove_object()
        if obj is not None:
            obj.features['discourseFunction'] = 'OBJECT'
            self.complement.insert(0, obj)

    def to_xml(self, element):
        features = self.features_to_xml_attributes()
        text = '<%s xsi:type="VPPhraseSpec" %s>\n' % (element, features)
        return text


class PP(Phrase):
    def __init__(self, head=None, compl=None):
        super().__init__(type='PREPOSITIONAL_PHRASE', vname='visit_pp')
        self.head = head
        self.add_complements(compl)
    
    def to_xml(self, element):
        features = self.features_to_xml_attributes()
        text = '<%s xsi:type="PPPhraseSpec" %s>\n' % (element, features)
        return text


class AdvP(Phrase):
    def __init__(self, head=None, compl=None):
        super().__init__(type='ADVERB_PHRASE', vname='visit_pp')
        self.head = head
        self.add_complements(compl)
    
    def to_xml(self, element):
        features = self.features_to_xml_attributes()
        text = '<%s xsi:type="AdvPhraseSpec" %s>\n' % (element, features)
        return text


class AdjP(Phrase):
    def __init__(self, head=None, compl=None):
        super().__init__(type='ADJECTIVE_PHRASE', vname='visit_pp')
        self.head = head
        self.add_complements(compl)
    
    def to_xml(self, element):
        features = self.features_to_xml_attributes()
        text = '<%s xsi:type="AdjPhraseSpec" %s>\n' % (element, features)
        return text


class CoordinatedClause(NLGElement):
    def __init__(self, coords=None, conj='and'):
        super().__init__(vname='visit_coord')
        if coords is None:
            self.coords = list()
        else:
            self.coords = coords
        self.features['conj'] = conj

    def __eq__(self, other):
        if (not isinstance(other, CoordinatedClause)):
            return False
        else:
            return (self.coords == other.coords)

    def to_xml(self, element):
        features = self.features_to_xml_attributes()
        text = ('<%s xsi:type="CoordinatedPhraseElement" %s>\n' %
                (element, features))
        return text


class IVisitor:
    def visit_phrase(self, node, element=''):
        if node.front_modifier:
            for c in node.front_modifier:
                c.accept(self, 'frontMod')
        
        if node.pre_modifier:
            for c in node.pre_modifier:
                c.accept(self, 'preMod')
        
        if node.head:
            node.head.accept(self, 'head')

        if node.complement:
            for c in node.complement:
                c.accept(self, 'compl')

        if node.post_modifier:
            for c in node.post_modifier:
                c.accept(self, 'postMod')



class XmlVisitor(IVisitor):
    def __init__(self):
        self.header = '''
<?xml version="1.0" encoding="utf-8"?>
<nlg:NLGSpec xmlns="http://simplenlg.googlecode.com/svn/trunk/res/xml"
xmlns:nlg="http://simplenlg.googlecode.com/svn/trunk/res/xml"
xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"
xsi:schemaLocation="http://simplenlg.googlecode.com/svn/trunk/res/xml ">
<nlg:Request>

<Document cat="PARAGRAPH">
'''
        self.xml = ''
        self.footer = '''
</Document>
</nlg:Request>
</nlg:NLGSpec>
'''

    def visit_word(self, node, element):
        if (node is not None):
            self.xml += node.to_xml(element)
    
    def visit_string(self, node, element):
        if (node is not None):
            self.xml += node.to_xml(element)
    
    def visit_placeholder(self, node, element):
        if (node is not None):
            self.xml += node.to_xml(element)

    def visit_clause(self, node, element):
        if (node is not None):
            self.xml += node.to_xml(element)
        if node.subj:
            node.subj.accept(self, 'subj')
        if node.vp:
            node.vp.accept(self, 'vp')
        self.xml += '\n</%s>\n' % element

    def visit_np(self, node, element):
        if (node is not None):
            self.xml += node.to_xml(element)
        if node.spec:
            node.spec.accept(self, 'spec')
        self.visit_phrase(node)
        self.xml += '\n</%s>\n' % element

    def visit_vp(self, node, element):
        if (node is not None):
            self.xml += node.to_xml(element)
        self.visit_phrase(node)
        self.xml += '\n</%s>\n' % element

    def visit_pp(self, node, element):
        if (node is not None):
            self.xml += node.to_xml(element)
        self.visit_phrase(node)
        self.xml += '\n</%s>\n' % element

    def visit_coord(self, node, element):
        if (node is not None):
            self.xml += node.to_xml(element)
        for c in node.coords:
            c.accept(self, 'coord')
        self.xml += '\n</%s>\n' % element

    def to_xml(self):
        return self.header + self.xml + self.footer
    
    def clear(self):
        self.xml = ''

    def __repr__(self):
        return ('[ XmlVisitor:\n%s]' % (self.header + self.xml + self.footer))



class StrVisitor(IVisitor):
    def __init__(self):
        self.text = ''
    
    def visit_word(self, node, element):
        if (node is not None):
            self.text += ' ' + node.to_str()
    
    def visit_string(self, node, element):
        if (node is not None):
            self.text += ' ' + node.to_str()
    
    def visit_placeholder(self, node, element):
        if (node is not None):
            self.text += ' ' + node.to_str()
    
    def visit_clause(self, node, element):
        if node.subj:
            node.subj.accept(self)
        if node.vp:
            node.vp.accept(self)
    
    def visit_np(self, node, element):
        if node.spec:
            node.spec.accept(self)
        self.visit_phrase(node)
    
    def visit_vp(self, node, element):
        self.visit_phrase(node)
    
    def visit_pp(self, node, element):
        self.visit_phrase(node)
    
    def visit_coord(self, node, element):
        if len(node.coords) > 2:
            for c in node.coords[:-1]:
                c.accept(self)
                self.text += ','
            self.text = self.text[:-1] # remove the last ", "
            self.text += ' and'
            node.coords[-1].accept(self)
    
        elif len(node.coords) > 1:
            node.coords[0].accept(self)
            self.text += ' and'
            node.coords[1].accept(self)

        elif len(node.coords) > 0:
            node.coords[0].accept(self)

    def to_str(self):
        return self.text.strip()
    
    def clear(self):
        self.text = ''
    
    def __repr__(self):
        return ('[ StrVisitor:\n%s]' % (self.text))












