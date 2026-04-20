// WebRTC Peer Connection for ISL Connect
// Usage: initPeer(myId, targetId, onConnect, onSign)

class ISLPeer {
  constructor(myId, targetId, onVideoReady, onSignData) {
    this.myId = myId;
    this.targetId = targetId;
    this.onVideoReady = onVideoReady;
    this.onSignData = onSignData;
    this.pc = new RTCPeerConnection({
      iceServers: [{urls: 'stun:stun.l.google.com:19302'}]
    });
    this.init();
  }

  init() {
    // Local media
    navigator.mediaDevices.getUserMedia({video: true, audio: true}).then(stream => {
      this.localStream = stream;
      stream.getTracks().forEach(track => this.pc.addTrack(track, stream));
      document.getElementById('localVideo').srcObject = stream;
    }).catch(e => console.error('Media error:', e));

    // Data channel for signs
    this.dataChannel = this.pc.createDataChannel('isl-signs');
    this.dataChannel.onmessage = e => this.onSignData(JSON.parse(e.data));

    // Remote video
    this.pc.ontrack = e => {
      document.getElementById('remoteVideo').srcObject = e.streams[0];
      this.onVideoReady();
    };

    // Signaling
    this.pc.onicecandidate = e => {
      if (e.candidate) socket.emit('ice-candidate', {
        targetId: this.targetId,
        candidate: e.candidate
      });
    };
  }

  async startCall() {
    const offer = await this.pc.createOffer();
    await this.pc.setLocalDescription(offer);
    socket.emit('call-offer', {
      targetId: this.targetId,
      offer: offer
    });
  }

  async acceptCall(offer) {
    await this.pc.setRemoteDescription(offer);
    const answer = await this.pc.createAnswer();
    await this.pc.setLocalDescription(answer);
    socket.emit('call-answer', {
      callerId: this.callerId,
      answer: answer
    });
  }

  addIceCandidate(candidate) {
    this.pc.addIceCandidate(candidate);
  }

  sendSignData(signs) {
    if (this.dataChannel.readyState === 'open') {
      this.dataChannel.send(JSON.stringify(signs));
    }
  }

  close() {
    this.pc.close();
  }
}

// Global peer
let peer = null;

// Init call
function initCall(myId, targetId) {
  peer = new ISLPeer(myId, targetId, () => {
    console.log('Video ready');
  }, (data) => {
    // Update remote signs display
    updateRemoteSigns(data);
  });
  peer.startCall();
}

function acceptIncomingCall(callerId, offer) {
  peer = new ISLPeer(session.user_id, callerId, () => {}, updateRemoteSigns);
  peer.acceptCall(offer);
}

// Update signs from data channel
function updateRemoteSigns(signData) {
  const display = document.getElementById('remoteSignDisplay');
  display.innerHTML = signData.map(s => `<div class="sign-box"><img src="${s.img}" class="sign-img"><div class="sign-label">${s.label}</div></div>`).join('');
}
