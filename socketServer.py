import eventlet
import socketio
import configparser
import time


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
		sio.emit("video", videoURL, room=sid)
	else:
		sio.emit("message", "Please wait for administrator to start movie.", room=sid)

@sio.event
def state(sid):
	global lastState
	print("send state")
	sio.emit("state", lastState, room=sid)

@sio.event
def progress(sid):
	global lastPlayed, lastPaused

	if lastPaused == 0:
		progressNow = int(time.time() - lastPlayed)
	if lastPaused != 0:
		progressNow = int(lastPaused - lastPlayed)

	print("send progress", progressNow)
	sio.emit("time", progressNow, room=sid)

@sio.event
def setState(sid, state):
	global lastState, lastPlayed, lastPaused, pausedIndex

	print("got state", state)

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
def setTime(sid, timeS):
	global lastPlayed, lastPaused

	print(timeS)
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

if __name__ == '__main__':
	config = configparser.ConfigParser()
	config.read("settings.ini")

	videoURL = config.get("general", "videoURL")
	allowWatch = False
	if config.get("general", "allowWatch") == "yes":
		allowWatch = True

	useSSL = True
	if config.get("ssl", "enable") == "no":
		useSSL = False

	certfile = config.get("ssl", "certfile")
	privkey = config.get("ssl", "privkey")

	port = int(config.get('socket', 'port'))

	if useSSL == True:
		eventlet.wsgi.server(eventlet.wrap_ssl(eventlet.listen(('', port)), certfile=certfile, keyfile=privkey, server_side=True), app)
	else:
		eventlet.wsgi.server(eventlet.listen(('', port)), app)
