import errno
import os
import sys
import tempfile
from argparse import ArgumentParser
from urllib.parse import quote
from kbbi import KBBI
from urbandictionary_top import udtop
from googletrans import Translator
import requests
import wikipedia

from flask import Flask, request, abort

from linebot import (
	LineBotApi, WebhookHandler
)
from linebot.exceptions import (
	InvalidSignatureError, LineBotApiError
)
from linebot.models import (
	MessageEvent, TextMessage, TextSendMessage, ImageSendMessage, SourceGroup, SourceRoom,
	TemplateSendMessage, ConfirmTemplate, MessageTemplateAction,
	ButtonsTemplate, ImageCarouselTemplate, ImageCarouselColumn, URITemplateAction,
	PostbackTemplateAction, DatetimePickerTemplateAction,
	CarouselTemplate, CarouselColumn, PostbackEvent,
	StickerMessage, StickerSendMessage, LocationMessage, LocationSendMessage,
	ImageMessage, VideoMessage, AudioMessage, FileMessage,
	VideoSendMessage, AudioSendMessage,
	UnfollowEvent, FollowEvent, JoinEvent, LeaveEvent, BeaconEvent
)

translator = Translator()
wiki_settings = {}


app = Flask(__name__)

line_bot_api = LineBotApi('Njld6qW7PBK7VU6+vXvt69kLjbS8KQ0dhXQ6crmQVpj/wy94eLgRDDEpi+Hus/eUuKqjOhEqlAJ3m3yrv6es68ui2exmrH57ssvEJsx1ZEdxpB8JUng3h+hPGLj0mveJ3YZYaWh3bCzfNszmsWfdiwdB04t89/1O/w1cDnyilFU=')
handler = WebhookHandler('b832b267d6246cf977e7dce943d6b30a')

static_tmp_path = os.path.join(os.path.dirname(__file__), 'static', 'tmp')

# function for create tmp dir for download content
def make_static_tmp_dir():
	try:
		os.makedirs(static_tmp_path)
	except OSError as exc:
		if exc.errno == errno.EEXIST and os.path.isdir(static_tmp_path):
			pass
		else:
			raise

@app.route("/callback", methods=['POST'])
def callback():
	# get X-Line-Signature header value
	signature = request.headers['X-Line-Signature']

	# get request body as text
	body = request.get_data(as_text=True)
	app.logger.info("Request body: " + body)

	# handle webhook body
	try:
		handler.handle(body, signature)
	except InvalidSignatureError:
		abort(400)

	return 'OK'


@handler.add(MessageEvent, message=TextMessage)
def handle_text_message(event):

	text=event.message.text
	
	if isinstance(event.source, SourceGroup):
		subject = line_bot_api.get_group_member_profile(event.source.group_id,
														event.source.user_id)
		set_id = event.source.group_id
	elif isinstance(event.source, SourceRoom):
		subject = line_bot_api.get_room_member_profile(event.source.room_id,
                                                   event.source.user_id)
		set_id = event.source.room_id
	else:
		subject = line_bot_api.get_profile(event.source.user_id)
		set_id = event.source.user_id
	
	def split1(text):
		return text.split('/wolfram ', 1)[-1]
		
	def split2(text):
		return text.split('/kbbi ', 1)[-1]
		
	def split3(text):
		return text.split('/echo ', 1)[-1]

	def split4(text):
		return text.split('/wolframs ', 1)[-1]
	
	def split5(text):
		return text.split('/trans ', 1)[-1]
	
	def split6(text):
		return text.split('/wiki ', 1)[-1]
	
	def split7(text):
		return text.split('/wikilang ', 1)[-1]
		
	def split8(text):
		return text.split('/urban ', 1)[-1]

	def split9(text):
		return text.split('/ox ', 1)[-1]
		
	def ox(keyword):
		oxdict_appid = ('7dff6c56')
		oxdict_key = ('41b55bba54078e9fb9f587f1b978121f')
		
		word = quote(keyword)
		url = ('https://od-api.oxforddictionaries.com:443/api/v1/entries/en/{}'.format(word))
		req = requests.get(url, headers={'app_id': oxdict_appid, 'app_key': oxdict_key})
		if "No entry available" in req.text:
			return 'No entry available for "{}".'.format(word)

		req = req.json()
		result = ''
		i = 0
		for each_result in req['results']:
			for each_lexEntry in each_result['lexicalEntries']:
				for each_entry in each_lexEntry['entries']:
					for each_sense in each_entry['senses']:
						if 'crossReferenceMarkers' in each_sense:
							search = 'crossReferenceMarkers'
						else:
							search = 'definitions'
						for each_def in each_sense[search]:
							i += 1
							result += '\n{}. {}'.format(i, each_def)

		if i == 1:
			result = 'Definition of {}:\n'.format(keyword) + result[4:]
		else:
			result = 'Definitions of {}:'.format(keyword) + result
		return result

	
	def wolfram(query):
		wolfram_appid = ('83L4JP-TWUV8VV7J7')

		url = 'https://api.wolframalpha.com/v2/result?i={}&appid={}'
		return requests.get(url.format(quote(query), wolfram_appid)).text
		
	def wolframs(query):
		wolfram_appid = ('83L4JP-TWUV8VV7J7')

		url = 'https://api.wolframalpha.com/v2/simple?i={}&appid={}'
		return url.format(quote(query), wolfram_appid)
	
	def trans(word):
		sc = 'en'
		to = 'id'
		
		if word[0:].lower().strip().startswith('sc='):
			sc = word.split(', ', 1)[0]
			sc = sc.split('sc=', 1)[-1]
			word = word.split(', ', 1)[1]
	
		if word[0:].lower().strip().startswith('to='):
			to = word.split(', ', 1)[0]
			to = to.split('to=', 1)[-1]
			word = word.split(', ', 1)[1]
			
		if word[0:].lower().strip().startswith('sc='):
			sc = word.split(', ', 1)[0]
			sc = sc.split('sc=', 1)[-1]
			word = word.split(', ', 1)[1]
			
		return translator.translate(word, src=sc, dest=to).text
		
	def wiki_get(keyword, set_id, trim=True):
    
		try:
			wikipedia.set_lang(wiki_settings[set_id])
		except KeyError:
			wikipedia.set_lang('en')

		try:
			result = wikipedia.summary(keyword)

		except wikipedia.exceptions.DisambiguationError:
			articles = wikipedia.search(keyword)
			result = "{} disambiguation:".format(keyword)
			for item in articles:
				result += "\n{}".format(item)
		except wikipedia.exceptions.PageError:
			result = "{} not found!".format(keyword)

		else:
			if trim:
				result = result[:2000]
				if not result.endswith('.'):
					result = result[:result.rfind('.')+1]
		return result
		
	def wiki_lang(lang, set_id):
    
		langs_dict = wikipedia.languages()
		if lang in langs_dict.keys():
			wiki_settings[set_id] = lang
			return ("Language has been changed to {} successfully."
					.format(langs_dict[lang]))

		return ("{} not available!\n"
				"See meta.wikimedia.org/wiki/List_of_Wikipedias for "
				"a list of available languages, and use the prefix "
				"in the Wiki column to set the language."
				.format(lang))	
	
	def find_kbbi(keyword, ex=True):

		try:
			entry = KBBI(keyword)
		except KBBI.TidakDitemukan as e:
			result = str(e)
		else:
			result = "Definisi {}:\n".format(keyword)
			if ex:
				result += '\n'.join(entry.arti_contoh)
			else:
				result += str(entry)
		return result
	
	def urban(keyword, ex=True):
		
		try:
			entry = udtop(keyword)
		except (TypeError, AttributeError, udtop.TermNotFound) :
			result = "{} definition not found in urbandictionary.".format(keyword)
		else:
			result = "{} definition:\n".format(keyword)
			if ex:
				result += str(entry)
			else:
				result += entry.definition
		return result
	
	if text == '/help':
		line_bot_api.reply_message(
			event.reply_token,
			TextSendMessage('I will be here for you'))
	
	elif text == '/leave':
		if isinstance(event.source, SourceGroup):
			line_bot_api.reply_message(
				event.reply_token,
				TextSendMessage('I am leaving the group...'))
			line_bot_api.leave_group(event.source.group_id)
		
		elif isinstance(event.source, SourceRoom):
			line_bot_api.reply_message(
				event.reply_token,
				TextSendMessage('I am leaving the group...'))
			line_bot_api.leave_room(event.source.room_id)
			
		else:
			line_bot_api.reply_message(
				event.reply_token,
				TextSendMessage('>_< cannot do...'))
	
	elif text == '/about':
		line_bot_api.reply_message(
				event.reply_token,
				TextSendMessage("Hello, my name is Aditmadzs\n"
								"Nice to meet you... \n"
								"source code: https://github.com/Aditmadzs"))
	
	elif text == '/cmd':
		line_bot_api.reply_message(
				event.reply_token,
				TextSendMessage("Without parameters: \n"
								"/about, /help, /profile, /leave, /lang \n"
								"/confirm, /buttons, /search image, \n"
								"/manga, /dots, /track, /bet \n"
								"/image_carousel, /imagemap \n"
								"\n"
								"With parameters: \n"
								"/echo, /kbbi, /wolfram, /wolframs, \n"
								"/trans, /wiki, /wikilang, /urban, /ox"))
	
	elif text == '/lang':
		line_bot_api.reply_message(
				event.reply_token,
				TextSendMessage("Language for translation see here \n"
								"https://github.com/Aditmadzs/oalinebot/blob/master/Lang.txt"))
	
	elif text == '/test':
		line_bot_api.reply_message(
				event.reply_token,
				AudioSendMessage(original_content_url='http://commondatastorage.googleapis.com/codeskulptor-assets/week7-brrring.m4a',
									duration=240000))
	
	elif text == '/manga':
		line_bot_api.reply_message(
				event.reply_token,
				TextSendMessage("mangaku.in"))
	
	elif text == '/ig':
		line_bot_api.reply_message(
				event.reply_token,
				TextSendMessage("https://www.instagram.com/aditmadzs1"))
	
	elif text == '/track':
		line_bot_api.reply_message(
				event.reply_token,
				TextSendMessage("http://dota2.prizetrac.kr/international2018"))
	
	elif text == '/bet':
		line_bot_api.reply_message(
				event.reply_token,
				TextSendMessage("dota2.com/predictions"))
	
	elif text == '/search image':
		line_bot_api.reply_message(
				event.reply_token,
				TextSendMessage("Try this up \n"
								"https://reverse.photos/"))
	
	elif text == '/profile':
		if isinstance(event.source, SourceGroup):
			try:
				profile = line_bot_api.get_group_member_profile(event.source.group_id, event.source.user_id)
				result = ("Display name: " + profile.display_name + "\n" +
						  "Profile picture: " + profile.picture_url + "\n" +
						  "User_ID: " + profile.user_id)
			except LineBotApiError:
				pass	
			line_bot_api.reply_message(
				event.reply_token,
				TextSendMessage(result))
			
		
		elif isinstance(event.source, SourceRoom):
			try:
				profile = line_bot_api.get_room_member_profile(event.source.room_id, event.source.user_id)
				result = ("Display name: " + profile.display_name + "\n" +
						  "Profile picture: " + profile.picture_url + "\n" +
						  "User_ID: " + profile.user_id)
			except LineBotApiError:
				pass	
			line_bot_api.reply_message(
				event.reply_token,
				TextSendMessage(result))
			
				
		else:
			try:
				profile = line_bot_api.get_profile(event.source.user_id)
				result = ("Display name: " + profile.display_name + "\n" +
						  "Profile picture: " + profile.picture_url + "\n" +
						  "User_ID: " + profile.user_id)
				if profile.status_message:
					result += "\n" + "Status message: " + profile.status_message
			except LineBotApiError:
				pass
			line_bot_api.reply_message(
				event.reply_token,
				TextSendMessage(result))
	
	elif text=='/kbbi':
		line_bot_api.reply_message(
				event.reply_token,
				TextSendMessage('command /kbbi {input}'))
	
	elif text=='/urban':
		line_bot_api.reply_message(
				event.reply_token,
				TextSendMessage('command /urban {input}'))
	
	elif text=='/ox':
		line_bot_api.reply_message(
				event.reply_token,
				TextSendMessage('command /ox {input}'))
	
	elif text=='/wolfram':
		line_bot_api.reply_message(
				event.reply_token,
				TextSendMessage('command /wolfram {input}'))
				
	elif text=='/trans':
		line_bot_api.reply_message(
				event.reply_token,
				TextSendMessage('command /trans sc={}, to={}, {text}'))
	
	elif text=='/wiki':
		line_bot_api.reply_message(
				event.reply_token,
				TextSendMessage('command /wiki {text}'))
				
	elif text=='/wikilang':
		line_bot_api.reply_message(
				event.reply_token,
				TextSendMessage('command /wikilang {language_id}'))
	
	elif text == '/confirm':
		confirm_template = ConfirmTemplate(text='Do it?', actions=[
			MessageTemplateAction(label='Yes', text='Yes!'),
			MessageTemplateAction(label='No', text='No!'),
			])
		template_message = TemplateSendMessage(
			alt_text='Confirm alt text', template=confirm_template)
		line_bot_api.reply_message(event.reply_token, template_message)
	
	elif text == '/buttons':
		buttons_template = ButtonsTemplate(
			title='My buttons sample', text='Hello, my buttons', actions=[
				URITemplateAction(
					label='Go to line.me', uri='https://line.me'),
				PostbackTemplateAction(label='ping', data='ping'),
				PostbackTemplateAction(
					label='ping with text', data='ping',
					text='ping'),
				MessageTemplateAction(label='Translate Rice', text='米')
			])
		template_message = TemplateSendMessage(
			alt_text='Buttons alt text', template=buttons_template)
		line_bot_api.reply_message(event.reply_token, template_message)
	
	elif text == '/image_carousel':
		image_carousel_template = ImageCarouselTemplate(columns=[
			ImageCarouselColumn(image_url='https://via.placeholder.com/1024x1024',
								action=DatetimePickerTemplateAction(label='datetime',
																	data='datetime_postback',
																	mode='datetime')),
			ImageCarouselColumn(image_url='https://via.placeholder.com/1024x1024',
								action=DatetimePickerTemplateAction(label='date',
																	data='date_postback',
																	mode='date'))
		])
		template_message = TemplateSendMessage(
			alt_text='ImageCarousel alt text', template=image_carousel_template)
		line_bot_api.reply_message(event.reply_token, template_message)
		
	elif text == '/imagemap':
		pass
	
	elif text[0:].lower().strip().startswith('/wolfram '):
		line_bot_api.reply_message(
			event.reply_token,
			TextSendMessage(wolfram(split1(text))))
			
	elif text[0:].lower().strip().startswith('/wolframs '):
		line_bot_api.reply_message(
			event.reply_token,
			ImageSendMessage(original_content_url= wolframs(split4(text)),
								preview_image_url= wolframs(split4(text))))

	elif text[0:].lower().strip().startswith('/kbbi '):
		line_bot_api.reply_message(
			event.reply_token,
			TextSendMessage(find_kbbi(split2(text))))
			
	elif text[0:].lower().strip().startswith('/urban '):
		line_bot_api.reply_message(
			event.reply_token,
			TextSendMessage(urban(split8(text))))
			
	elif text[0:].lower().strip().startswith('/ox '):
		line_bot_api.reply_message(
			event.reply_token,
			TextSendMessage(ox(split9(text))))
			
	elif text[0:].lower().strip().startswith('/echo ') :
		line_bot_api.reply_message(
			event.reply_token,
			TextSendMessage(split3(text)))
			
	elif text[0:].lower().strip().startswith('/trans ') :
		line_bot_api.reply_message(
			event.reply_token,
			TextSendMessage(trans(split5(text))))
	
	elif text[0:].lower().strip().startswith('/wiki ') :
		line_bot_api.reply_message(
			event.reply_token,
			TextSendMessage(wiki_get(split6(text), set_id=set_id)))
			
	elif text[0:].lower().strip().startswith('/wikilang ') :
		line_bot_api.reply_message(
			event.reply_token,
			TextSendMessage(wiki_lang(split7(text), set_id=set_id)))
			
@handler.add(MessageEvent, message=LocationMessage)
def handle_location_message(event):
	line_bot_api.reply_message(
		event.reply_token,
		LocationSendMessage(
			title=event.message.title, address=event.message.address,
			latitude=event.message.latitude, longitude=event.message.longitude
		)
	)

@handler.add(MessageEvent, message=StickerMessage)
def handle_sticker_message(event):
	line_bot_api.reply_message(
		event.reply_token,
		StickerSendMessage(
			package_id=event.message.package_id,
			sticker_id=event.message.sticker_id)
	)
	
# Other Message Type
@handler.add(MessageEvent, message=(ImageMessage, VideoMessage, AudioMessage))
def handle_content_message(event):
	if isinstance(event.message, ImageMessage):
		ext = 'jpg'
	elif isinstance(event.message, VideoMessage):
		ext = 'mp4'
	elif isinstance(event.message, AudioMessage):
		ext = 'm4a'
	else:
		return

	message_content = line_bot_api.get_message_content(event.message.id)
	with tempfile.NamedTemporaryFile(dir=static_tmp_path, prefix=ext + '-', delete=False) as tf:
		for chunk in message_content.iter_content():
			tf.write(chunk)
		tempfile_path = tf.name

	dist_path = tempfile_path + '.' + ext
	dist_name = os.path.basename(dist_path)
	os.rename(tempfile_path, dist_path)
	dist_name = dist_name.replace(" ","_")
	
	line_bot_api.reply_message(
		event.reply_token, [
			TextSendMessage(text='Save content.'),
			TextSendMessage(text=request.host_url + os.path.join('static', 'tmp', dist_name))
		])
		
@handler.add(MessageEvent, message=FileMessage)
def handle_file_message(event):
	message_content = line_bot_api.get_message_content(event.message.id)
	with tempfile.NamedTemporaryFile(dir=static_tmp_path, prefix='file-', delete=False) as tf:
		for chunk in message_content.iter_content():
			tf.write(chunk)
		tempfile_path = tf.name

		
	dist_path = tempfile_path + '-' + event.message.file_name
	dist_name = os.path.basename(dist_path)
	os.rename(tempfile_path, dist_path)
	dist_name = dist_name.replace(" ","_")
	
	line_bot_api.reply_message(
		event.reply_token, [
			TextSendMessage(text='Save file.'),
			TextSendMessage(text=request.host_url + os.path.join('static', 'tmp', dist_name))
		])
		
@handler.add(FollowEvent)
def handle_follow(event):
	line_bot_api.reply_message(
		event.reply_token, TextSendMessage(text='Got follow event'))


@handler.add(UnfollowEvent)
def handle_unfollow():
	app.logger.info("Got Unfollow event")


@handler.add(JoinEvent)
def handle_join(event):
	line_bot_api.reply_message(
		event.reply_token,
		TextSendMessage(text='Hi, my name is Reika. Hope we can make some fun in this ' + event.source.type))
		
@handler.add(LeaveEvent)
def handle_leave():
	app.logger.info("Bye")


@handler.add(PostbackEvent)
def handle_postback(event):
	if event.postback.data == 'ping':
		line_bot_api.reply_message(
			event.reply_token, TextSendMessage(text='pong'))
	elif event.postback.data == 'datetime_postback':
		line_bot_api.reply_message(
			event.reply_token, TextSendMessage(text=event.postback.params['datetime']))
	elif event.postback.data == 'date_postback':
		line_bot_api.reply_message(
			event.reply_token, TextSendMessage(text=event.postback.params['date']))


@handler.add(BeaconEvent)
def handle_beacon(event):
	line_bot_api.reply_message(
		event.reply_token,
		TextSendMessage(
			text='Got beacon event. hwid={}, device_message(hex string)={}'.format(
				event.beacon.hwid, event.beacon.dm)))
	
if __name__ == "__main__":
	port = int(os.environ.get('PORT', 5000))
	make_static_tmp_dir()
app.run(host='0.0.0.0', port=port)
