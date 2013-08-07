#django
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.models import User
from django.shortcuts import render, redirect, get_object_or_404
from django.http import HttpResponse
from django.forms import ModelForm
from django.core.cache import cache
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
#uncreative
from models import Quotation, Text
#python
import re
import random
import logging
from collections import namedtuple


#homepage with douglas hueber quotation
def index(request):
	return render(request, "generator/index.html")
#alternate homepage
def index2(request):
	return render(request, "generator/index2.html")


#cache quotations, texts, and markov models
def all_quotes(update = False):
	key = 'all'
	quotes = cache.get(key)
	if quotes is None or update:
		logging.error("allquote DB Query")
		quotes = Quotation.objects.all().order_by('-created')
		quotes = list(quotes)
		cache.set(key, quotes)
	return quotes

def user_quotes(user, update = False):
	key = 'u'+str(user.pk)
	quotes = cache.get(key)
	if quotes is None or update:
		logging.error("userquote DB Query")
		quotes = Quotation.objects.filter(user=user).order_by('-created')
		quotes = list(quotes)
		cache.set(key, quotes)
	return quotes

def user_by_username(username, update = False):
	key = 'uname' + username
	user = cache.get(key)
	if user is None or update:
		logging.error("user by name")
		user = get_object_or_404(User, username=username)
		cache.set(key, user)
	return user

def text_quotes(text, update = False):
	key = 'tq'+str(text.pk)
	quotes = cache.get(key)
	if quotes is None or update:
		logging.error("Textquote DB Query")
		quotes = Quotation.objects.filter(text=text).order_by('-created')
		quotes = list(quotes)
		cache.set(key, quotes)
	return quotes

def get_text(text_id, update = False):
	key = 't' + str(text_id)
	text = cache.get(key)
	if text is None or update:
		logging.error("Text DB Query")
		text = get_object_or_404(Text, pk=text_id)
		cache.set(key, text)
	return text

#cache of markov model dictionary associated with each text
def cached_model(text_id, update = False):
	key = 'm' + str(text_id)
	model = cache.get(key)
	if model is None or update:
		logging.error("Model DB Query")
		text = get_text(text_id)
		content = text.content
		model = Text.generatemodel(content)
		cache.set(key, model)
	return model

#cache of text info -- no content, just titles, authors, and ids
# for add.html page dropdown menu
TextInfo = namedtuple('TextInfo', 'id title author')
def text_info(update = False):
	key = 'txtinfo'
	info = cache.get(key)
	if info is None or update:
		logging.error("txt info db query")
		texts = Text.objects.all().order_by('-created')
		info = []
		for text in texts:
			textinfo = TextInfo(text.id, text.title, text.author)
			info.append(textinfo)
		cache.set(key, info)
	return info

#pagination helper method
def paginate(request, quotes):
	paginator = Paginator(quotes, 5)
	page = request.GET.get('page')
	try:
		quotes = paginator.page(page)
	except PageNotAnInteger:
		quotes = paginator.page(1)
	except EmptyPage:
		quotes=paginator.page(paginator.num_pages)
	return quotes

# main page: displays all quotations
def objects(request):
	if request.user.is_authenticated():
		quotes = all_quotes()
		quotes = paginate(request, quotes)
		return render(request, "generator/allquotes.html", {'quotes': quotes})

	# redirect if user isn't logged in -- could potentially be DRYed
	else:
		next = '/login/?next=/objects'
		if 'HTTP_REFERER' in request.META:
			if '/signup' in request.META.get('HTTP_REFERER'):
				next = '/signup/?next=/objects'
		return redirect(next)

# userpage: same as main, but shows quotations submitted by a particular user
# defaults to user's own page
def userquotes(request, username=""):
	if request.user.is_authenticated():
		if username == request.user.username:
			return redirect('/objects/urtexts')

		if username:
			user = user_by_username(username)
		else:
			user = request.user
		quotes = user_quotes(user)
		quotes = paginate(request, quotes)
		return render(request, "generator/userquotes.html", {'quotes': quotes, 'username': username})

	#redirect if user isn't logged in
	else:
		next = '/login/?next=/objects/urtexts/'
		if 'HTTP_REFERER' in request.META:
			if '/signup' in request.META.get('HTTP_REFERER'):
				next = '/signup/?next=/objects/urtexts/'
		if username:
			next += username
		return redirect(next)

# permalink page for text and its children
def permalink(request, text_id):
	if request.user.is_authenticated():
		text = get_text(text_id)
		quotes = text_quotes(text)
		return render(request, "generator/permalink.html", {'text': text, 'quotes': quotes})

	# redirect if user isn't logged in
	else:
		next = '/login?next=/objects/%s' %str(text_id)
		if 'HTTP_REFERER' in request.META:
			if '/signup' in request.META.get('HTTP_REFERER'):
				next = '/signup/?next=/objects/%s' %str(text_id)
		return redirect(next)


#page for generating random quotations based on texts.
def add(request):


	def render_form(content="", title="", author="", error="", quote = "", text_id=""):
		# include text author, titles, and IDs for dropdown menu
		texts = text_info()
		return render(request, "generator/add.html", {'content': content, 'title': title, 'author': author,
			'error': error, 'quote': quote, 'text_id': text_id, 'texts': texts})
	if not request.user.is_authenticated():
		return render_form()
	if request.method == 'POST':
		# Generate text based on user's input (left side of form)
		if 'generate' in request.POST:
			content = request.POST.get('content')
			author = request.POST.get('author')
			title = request.POST.get('title')
			text_id = request.POST.get('text_id')
			if len(content) < 500:
				error = ("The text you submitted is only {number} character{pl} long.  Please \
					submit a longer text.".format(number = len(content), pl = 's' if len(content)!=1 else ""))
				return render_form(error = error)
			# use a Markov chain to generate a random output based on the input text
			MINLENGTH = 50
			if text_id:
				model = cached_model(text_id)
				quote = Text.generatequote(content, MINLENGTH, model)
			else:
				quote = Text.generatequote(content, MINLENGTH)
			return render_form(content = content, title = title, author = author, quote = quote, text_id = text_id)

		# Save user's text and quotations (right side of form)
		else:
		 	content = request.POST.get('content')
			author = request.POST.get('author')
			title = request.POST.get('title')
			quote = request.POST.get('quote')
			text_id=request.POST.get('text_id')
			
			if text_id:
				text = get_text(text_id)
			else:
				text = Text.objects.create_text(content, title, author, request.user)
				# update cache
				get_text(text.pk, True)
				text_info(True)
			quote = Quotation.objects.create_quotation(quote, request.user, text)
			text_quotes(text, True)
			user_quotes(request.user, True)
			all_quotes(True)
			return redirect('/objects')
	else:
		# generate from existing text
		if request.GET.get('t'):
			text_id=request.GET.get('t')
			text = get_text(text_id)
			content = text.content
			author = text.author
			title = text.title
		# blank form for adding new text
		else:
			content = ""
			text_id = ""
			title = ""
			author = ""
		return render_form(content, title, author, text_id=text_id)


USER_RE = re.compile(r"^[a-zA-Z0-9_-]{3,20}$")
def valid_username(username):
    return username and USER_RE.match(username)

PASS_RE = re.compile(r"^.{3,20}$")
def valid_password(password):
    return password and PASS_RE.match(password)

def error_check(username, password, verify=None):
	error = ""
	#signup specific error
	if verify is not None:
		try:
			if User.objects.get(username=username):
				error = "That username is already taken.  Please choose another."
				return error
		except:
			if password != verify:
				error = "Passwords don't match."
	# error: invalid username or password
	if not valid_username(username) or not valid_password(password):
		error = "Please enter a valid username and password."	
	return error


def signup(request):
	def render_form(username="", error="", next_url="/"):
		return render(request, "generator/signup.html", {'username': username, 'error': error, 'next_url': next_url})
	if (request.POST):
		username = request.POST.get('username')
		password = request.POST.get('password')
		verify = request.POST.get('verify')
		next_url = request.POST.get('next_url')
		error = error_check(username, password, verify)
		if error:
			return render_form(username, error, next_url)
		#successful signup: save user, login, and redirect to welcome page
		else:
			user = User.objects.create_user(username=username, password=password)
			user.save()
			user=authenticate(username=username, password=password)
			login(request, user)
			return redirect(next_url)
	else:
		if request.GET.get('next'):
			next_url=request.GET.get('next')
		else:
			next_url = "/objects"
		if request.user.is_authenticated():
			return redirect(next_url)
		return render_form(next_url=next_url)


def userlogin(request):
	def render_form(username="", error="", next_url="/"):
		return render(request, "generator/login.html", {'username': username, 'error': error, 'next_url': next_url})
	if (request.POST):
		username = request.POST.get('username')
		password = request.POST.get('password')
		next_url = request.POST.get('next_url')
		error = error_check(username, password)
		if error:
			return render_form(username, error, next_url)
		else:
			user = authenticate(username=username, password=password)
			if user is not None:
				login(request, user)
				return redirect(next_url)
			else:
				error = "Please enter a valid username and password."
				return render_form(username, error, next_url)
	else:
		if request.GET.get('next'):
			next_url=request.GET.get('next')
		else:
			next_url = "/objects"
		if request.user.is_authenticated():
			return redirect(next_url)
		return render_form(next_url=next_url)

def userlogout(request):
	logout(request)
	return redirect('/')

def about(request):
	return render(request, "generator/about.html")