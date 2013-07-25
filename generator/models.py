from django.db import models
from django.contrib.auth.models import User

import random
import re
import string


# character based k-order markov model
class MarkovModel(object):
	#constructor creates a kgram dictionary
	#based on a text or a cached dictionary
	def __init__(self, content, k, model={}):
		self.order = k
		if model:
			self.model = model
		else:
			self.model = {}
			circulartext = content + content[:k]

			for i in range(len(content)):
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
	# one call is one iteration of a Markov chain.
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

# full text model object, source for generated text
class Text(models.Model):
	content = models.TextField()
	created = models.DateTimeField(auto_now_add=True)
	user = models.ForeignKey(User)
	author = models.CharField(max_length = 100, blank = True)
	title = models.CharField(max_length = 100, blank = True)

	objects = TextManager()
	def __unicode__(self):
		return self.content[:50]

	# Markov Chain Text Generator
	# text generator functions are static methods because they might be called
	# before text object is generated
	@staticmethod
	def generate(order, minlength, content, cachedmodel={}):
		model = MarkovModel(content, order, cachedmodel)

		# ad hoc method for choosing a starting point for output text
		# (semi-randomly start output with a capital letter)
		rand=random.randrange(len(content))
		kgram = (content+content[:order])[rand:rand+order]
		# chain kgrams until finding one that starts with a capital letter
		# limit this process to 100 iterations before reverting to default
		for i in range(100):
			if kgram[0].isupper():
				break
			else:
				nextchar = model.random(kgram)
				kgram = kgram[1:] + nextchar
		if not kgram[0].isupper():
			kgram=content[:order]

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
			#continue until end of sentence, 
			if i >= minlength:
				if nextchar == ('.' or '!' or '?'):
					break
				#cut off too-long sentences, unpunctuated blocks
				elif nextchar == '\n' and i >= minlength * 3:
					break
				elif i >= minlength * 6:
					break
		# clean output

		# remove unpaired quotation marks
		pattern = r'(\"(?=\S)[^\"]*(?<=\S)\")|\"'
		output = re.sub(pattern, lambda m: m.group(1) or '', output)
		# remove unpaired parentheses
		# remove unpaired single quotes, leaving apostrophes intact
		if output[-1] == ('.' or '!' or '?'):
			return output
		else:
			while output[-1] not in string.letters and len(output) > 0:
				if output[-1] == ('.' or '!' or '?'):
					return output
				output = output[:-1]
			return output + '.'
	@staticmethod
	def generatequote(content, length, cachedmodel={}):
		ORDER = 6
		return Text.generate(ORDER, length, content, cachedmodel)
	@staticmethod
	def generatemodel(content):
		ORDER = 6
		return MarkovModel(content, ORDER).model


class QuotationManager(models.Manager):
	def create_quotation(self, quote, user, text = None):
		newquote = self.create(quote = quote, user = user, text = text)
		return newquote

class Quotation(models.Model):
	quote = models.TextField()
	user = models.ForeignKey(User)
	created = models.DateTimeField(auto_now_add=True)
	text = models.ForeignKey(Text, blank = True, null = True)
	def __unicode__(self):
		return self.quote

	objects = QuotationManager()


