from django.db import models
from django.contrib.auth.models import User

import random
import re
import string


# character based k-order markov model
class MarkovModel:
	def __init__(self, text, k):
		self.model = {}
		self.order = k
		circulartext = text + text[:k]

		for i in range(len(text)):
			key = circulartext[i:i+k]
			nextchar = circulartext[i+k]
			#insert new key or update value
			if key not in self.model:
				self.model[key] = {}
				self.model[key][nextchar] = 1
			else:
				if nextchar not in self.model[key]:
					self.model[key][nextchar] = 1
				else:
					self.model[key][nextchar] += 1

	def inputcheck(self, kgram, char=None):
		if len(kgram) != self.order:
			raise InputError("kgram is not length %d" %self.order)
		if type(char) is str:
			if len(char) != 1:
				raise InputError("char must be a string of length 1")		

	#returns the # of times a given kgram appears in the original text
	#or if char is given, the number of times kgram is followed by char in the text
	def frequency(self, kgram, char = None):
		self.inputcheck(kgram)

		if kgram not in self.model:
			return 0
		elif char == None:
			total = 0
			for nextchar in self.model[kgram]:
				total += self.model[kgram][nextchar]
			return total
		else:
			return self.model[kgram][char]

	# generates a random character to follow kgram based on frequencies in the original text
	def random(self, kgram):
		self.inputcheck(kgram)
		freq = self.frequency(kgram)
		if freq == 0:
			raise InputError("no such kgram")
		rand = random.randrange(freq)
		count = 0
		for char in self.model[kgram]:
			count += self.model[kgram][char]
			if count > rand:
				return char


class TextManager(models.Manager):
	def create_text(self, content, title, author, user):
		newtext = self.create(content = content, title = title, author = author, user = user)
		return newtext

# full texts, source for generated text
class Text(models.Model):
	content = models.TextField()
	created = models.DateTimeField(auto_now_add=True)
	user = models.ForeignKey(User)
	author = models.CharField(max_length = 100, blank = True)
	title = models.CharField(max_length = 100, blank = True)

	objects = TextManager()
	def __unicode__(self):
		return self.content[:50]


	@staticmethod
	def generate(order, outputlength, text):
		model = MarkovModel(text, order)

		#semi-randomly start output with a capital letter
		rand=random.randrange(len(text))
		kgram = (text+text[:order])[rand:rand+order]
		# chain kgrams until beginning with a capital letter
		# limit this process to 100 iterations before going to a default
		for i in range(100):
			if kgram[0].isupper():
				break
			else:
				nextchar = model.random(kgram)
				kgram = kgram[1:] + nextchar
		if not kgram[0].isupper():
			kgram=text[:order]

		# build output text
		output = kgram
		i = 0
		#construct text of length at least outputlength, and continue until end of sentence
		while True:
			nextchar = model.random(kgram)
			output += nextchar
			if order !=0:
				kgram = kgram[1:] + nextchar
			i += 1
			#break conditions
			if i >= outputlength:
				if nextchar == ('.' or '!' or '?'):
					break
				#cut off too-long sentences, unpunctuated blocks
				elif nextchar == '\n' and i >= outputlength * 5:
					break
		# clean output -- to do: remove unpaired punctuation
		if output[-1] == ('.' or '!' or '?'):
			return output
		else:
			while output[-1] not in string.letters:
				output = output[:-1]
			return output + '.'

	@staticmethod
	def generatequote(text, length):
		ORDER = 6
		return Text.generate(ORDER, length, text)


class QuotationManager(models.Manager):
	def create_quotation(self, quote, user, text = None):
		newquote = self.create(quote = quote, user = user, text = text)
		return newquote

class Quotation(models.Model):
	quote = models.TextField()
	# parent/source text -- leave option to directly input quotations
	user = models.ForeignKey(User)
	created = models.DateTimeField(auto_now_add=True)
	text = models.ForeignKey(Text, blank = True, null = True)
	def __unicode__(self):
		return self.quote

	objects = QuotationManager()


