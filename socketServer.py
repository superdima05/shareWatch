import youtube_dl as ytdl
from urllib.parse import unquote
import eventlet
import socketio
import configparser
import time
import threading
import os

lastState = 0 # 0 - not init (0 sec and pause), 1 - pause, 2 - play
lastPlayed = 0
lastPaused = 0
pausedIndex = 0

sio = socketio.Server(cors_allowed_origins='*')
app = socketio.WSGIApp(sio, static_files={
	'/': {'content_type': 'text/html', 'filename': 'index.html'}
})

@sio.event
def connect(sid, environ):
	print('connect ', sid)

@sio.event
def video(sid):
	if allowWatch == True:
		if videoURL != "":
			sio.emit("video", videoURL, room = sid)
		sio.emit("audio", audioURL, room = sid)
		if youtubeURL != "":
			sio.emit("youtube", formats, room = sid)
			sio.emit("youtubeFormat", defaultFormat, room = sid)
	else:
		sio.emit("message", "Please wait till the administrator starts the movie.", room=sid)

@sio.event
def state(sid):
	global lastState
	sio.emit("state", lastState, room=sid)

@sio.event
def progress(sid):
	global lastPlayed, lastPaused, lastState

	if lastPaused == 0:
		progressNow = int(time.time() - lastPlayed)
	if lastPaused != 0:
		progressNow = int(lastPaused - lastPlayed)

	if lastState == 0:
		progressNow = 0

	sio.emit("time", progressNow, room=sid)

@sio.event
def setState(sid, state):
	global lastState, lastPlayed, lastPaused, pausedIndex

	if lastState == 0 and state != 0:
		lastPlayed = time.time()

	lastState = state
	if lastState == 2:
		pausedIndex = 0
		if lastPaused != 0:
			pausedIndex = pausedIndex + (time.time() - lastPaused)
		lastPlayed = lastPlayed + pausedIndex
		lastPaused = 0

	if lastState == 1:
		lastPaused = time.time()

	sio.emit("state", lastState, broadcast=True, include_self=False)

@sio.event
def buffering(sid, start):
	global lastState, lastPlayed, lastPaused, pausedIndex

	if int(start) == 1:
		lastState = 1
		sio.emit("message", "Buffering", broadcast=True, include_self=False)
	if int(start) == 0:
		lastState = 2
		sio.emit("message", "Playing", broadcast=True, include_self=False)

	if lastState == 2:
		pausedIndex = 0
		if lastPaused != 0:
			pausedIndex = pausedIndex + (time.time() - lastPaused)
		lastPlayed = lastPlayed + pausedIndex
		lastPaused = 0

	if lastState == 1:
		lastPaused = time.time()

	sio.emit("state", lastState, broadcast=True, include_self=False)


@sio.event
def setTime(sid, timeS):
	global lastPlayed, lastPaused

	if int(timeS) == 0:
		lastPlayed = time.time()
		sio.emit("time", 0, broadcast=True, include_self=False)
	else:
		if lastPaused == 0:
			progressNow = int(time.time() - lastPlayed)
		if lastPaused != 0:
			progressNow = int(lastPaused - lastPlayed)

		progressV = timeS - progressNow
		lastPlayed = lastPlayed - progressV

		sio.emit("time", timeS, broadcast=True, include_self=False)

@sio.event
def disconnect(sid):
	print('disconnect ', sid)

def watchdog():
	global initStamp, sio, videoURL, youtubeURL, allowWatch, lastState, lastPlayed, lastPaused, pausedIndex
	while True:
		if os.stat("settings.ini").st_mtime != initStamp:
			oldVideo = videoURL
			oldAllowed = allowWatch
			oldYoutube = youtubeURL		

			readConfig()
			if oldVideo != videoURL or oldAllowed != allowWatch or oldYoutube != youtubeURL:
				lastPlayed = 0
				lastState = 0
				lastPaused = 0
				pausedIndex = 0

			sio.emit("newInfo", broadcast = True)
			initStamp = os.stat("settings.ini").st_mtime
		time.sleep(.5)

def parseYoutube(url):
	global audioURL, formats, defaultFormat

	defaultFormat = "1080p (FHD)"
	formats = {
		"720p (HD)": None,
		"1080p (FHD)": None,
		"1440p (2K)": None,
		"2160p (4K)": None
	}

	yt = ytdl.YoutubeDL()
	try:
		_formats = yt.extract_info(url, download = False)['formats']
		for i in _formats:
			if i['acodec'] == "none":
				if i['ext'] == "webm":
					for x in formats.keys():
						if i['format_note'].replace("60", "") in x:
							formats[x] = unquote(i['url'])
			else:
				if i['vcodec'] == "none" and i['ext'] == "m4a":
					audioURL = unquote(i['url'])

		if formats[defaultFormat] == None:
			print("drop default")
			defaultFormat = "720p (HD)"

		for i in formats.copy().keys():
			if formats[i] == None:
				del formats[i]
	except Exception as e:
		raise ValueError("invalid url")

def readConfig():
	global audioURL, videoURL, youtubeURL, allowWatch, useSSL, certfile, privkey, port
	config = configparser.ConfigParser()
	config.read("settings.ini")

	videoURL = config.get("general", "videoURL")
	audioURL = config.get('general', 'audioURL')
	youtubeURL = config.get('general', 'youtubeURL')

	if youtubeURL != "":
		videoURL = ""
		audioURL = ""
		parseYoutube(youtubeURL)

	allowWatch = False
	if config.get("general", "allowWatch") == "yes":
		allowWatch = True

	useSSL = True
	if config.get("ssl", "enable") == "no":
		useSSL = False

	certfile = config.get("ssl", "certfile")
	privkey = config.get("ssl", "privkey")

	port = int(config.get('socket', 'port'))

if __name__ == '__main__':


	defaultFormat = "1080p (FHD)"
	formats = {
		"720p (HD)": None,
		"1080p (FHD)": None,
		"1440p (2K)": None,
		"2160p (4K)": None
	}

	initStamp = 0
	videoURL = None
	audioURL = None
	youtubeURL = None

	allowWatch = False
	useSSL = False
	certfile = None
	privkey = None
	port = 0

	initStamp = os.stat("settings.ini").st_mtime
	readConfig()

	eventlet.monkey_patch()
	eventlet.spawn(watchdog)

	if useSSL == True:
		eventlet.wsgi.server(eventlet.wrap_ssl(eventlet.listen(('', port)), certfile=certfile, keyfile=privkey, server_side=True), app)
	else:
		eventlet.wsgi.server(eventlet.listen(('', port)), app)
