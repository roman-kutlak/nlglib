

from nlglib.spec.phrase import make_noun_phrase


lexicon = new
XMLLexicon(); // built in lexicon

this.phraseFactory = new
NLGFactory(this.lexicon);
this.realiser = new
Realiser(this.lexicon);

this.man = this.phraseFactory.createNounPhrase("the", "man"); // $NON - NLS - 1$ // $NON - NLS - 2$
this.woman = this.phraseFactory.createNounPhrase("the", "woman"); // $NON - NLS - 1$ // $NON
// -NLS - 2$
this.dog = this.phraseFactory.createNounPhrase("the", "dog"); // $NON - NLS - 1$ // $NON - NLS - 2$
this.boy = this.phraseFactory.createNounPhrase("the", "boy"); // $NON - NLS - 1$ // $NON - NLS - 2$

this.beautiful = this.phraseFactory.createAdjectivePhrase("beautiful"); // $NON - NLS - 1$
this.stunning = this.phraseFactory.createAdjectivePhrase("stunning"); // $NON - NLS - 1$
this.salacious = this.phraseFactory.createAdjectivePhrase("salacious"); // $NON - NLS - 1$

this.onTheRock = this.phraseFactory.createPrepositionPhrase("on"); // $NON - NLS - 1$
this.np4 = this.phraseFactory.createNounPhrase("the", "rock"); // $NON - NLS - 1$ // $NON - NLS - 2$
this.onTheRock.addComplement(this.np4);

this.behindTheCurtain = this.phraseFactory.createPrepositionPhrase("behind"); // $NON - NLS - 1$
this.np5 = this.phraseFactory.createNounPhrase("the", "curtain"); // $NON - NLS - 1$
// $NON - NLS - 2$
this.behindTheCurtain.addComplement(this.np5);

this.inTheRoom = this.phraseFactory.createPrepositionPhrase("in"); // $NON - NLS - 1$
this.np6 = this.phraseFactory.createNounPhrase("the", "room"); // $NON - NLS - 1$ // $NON - NLS - 2$
this.inTheRoom.addComplement(this.np6);

this.underTheTable = this.phraseFactory.createPrepositionPhrase("under"); // $NON - NLS - 1$
this.underTheTable.addComplement(this.phraseFactory.createNounPhrase("the", "table"));
// $NON - NLS - 1$ // $NON - NLS - 2$

this.proTest1 = this.phraseFactory.createNounPhrase("the", "singer"); // $NON - NLS - 1$
// $NON - NLS - 2$
this.proTest2 = this.phraseFactory.createNounPhrase("some", "person"); // $NON - NLS - 1$
// $NON - NLS - 2$

this.kick = this.phraseFactory.createVerbPhrase("kick"); // $NON - NLS - 1$
this.kiss = this.phraseFactory.createVerbPhrase("kiss"); // $NON - NLS - 1$
this.walk = this.phraseFactory.createVerbPhrase("walk"); // $NON - NLS - 1$
this.talk = this.phraseFactory.createVerbPhrase("talk"); // $NON - NLS - 1$
this.getUp = this.phraseFactory.createVerbPhrase("get up"); // $NON - NLS - 1$
this.fallDown = this.phraseFactory.createVerbPhrase("fall down"); // $NON - NLS - 1$
this.give = this.phraseFactory.createVerbPhrase("give"); // $NON - NLS - 1$
this.say = this.phraseFactory.createVerbPhrase("say"); // $NON - NLS - 1$