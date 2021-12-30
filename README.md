# shareWatch

# Requirements
- python-socketio
- eventlet

# Installation
1. Replace `DOMAIN_NAME` with your domain name, where you will host python server.
2. Specify SSL certificate and key in `socketServer.py`
3. Specify videoURL in `socketServer.py` and change `allowWatch` to `True`, if you want to start watching after you setup everything. If you will specify videoURL, but `allowWatch` will be `False`, clients will get `Please wait for administrator to start movie.`.
4. Server `socketClient` folder, using web server (e.g. nginx)
5. Run socketServer.py.
6. Open `socketClient` in your browser and enjoy watching
