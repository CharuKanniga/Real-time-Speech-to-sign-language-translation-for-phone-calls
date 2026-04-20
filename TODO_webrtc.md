# WebRTC Real Calls TODO

**Goal:** Real P2P video calls + live signs overlay.

**Steps:**
- [x] Step 1: requirements.txt + flask-socketio ✅
- [x] Step 2: app.py SocketIO signaling ✅
- [ ] Step 3: templates/home.html online users/call
- [x] Step 4: static/js/webrtc.js peer logic ✅
- [ ] Step 5: templates/call.html video + signs
- [ ] Step 6: Test multi-tab/devices

**Architecture:**
Caller → signaling offer → Receiver accept → P2P video/audio/data (signs JSON).

