# shareWatch

# Requirements
- python-socketio
- eventlet

# Installation
1. Replace `DOMAIN_NAME` with your domain name where you will host your Python server.
2. Specify the SSL certificate and key in `socketServer.py`.
3. Specify `videoURL` in `socketServer.py` and change `allowWatch` to `True`, if you want to start watching after you setup everything. If you specify `videoURL`, but `allowWatch` is set to `False`, clients will get the `Please wait for administrator to start movie...` message.
4. Serve the `socketClient` folder using a web server (e.g. nginx).
5. Run `socketServer.py`.
6. Access the newly configured `socketClient` in your browser and enjoy watching.

# Where will `socketClient` work?
Any browser, which supports HTML5 (video tag) and JS, will work.

## Tested on:
  - Firefox 95.0.2 on Windows 11 (22000.376)
  - Firefox 95.0.2 on Arch Linux
  - Microsoft Edge 96.0.1054.62
  - webOS (version unknown)
  - iPhone 12 Pro Max (iOS 15.2)
  - Pixel 6 Pro (Android 12, Google Chrome 96.0.4664.104)
