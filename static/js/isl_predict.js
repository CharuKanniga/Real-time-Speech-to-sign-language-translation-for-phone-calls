// ISL Voice-to-Sign ML Predictor (TensorFlow.js)
class ISLPredictor {
  constructor() {
    this.model = null;
    this.classNames = [];
    this.isReady = false;
    this.loadModel();
  }

  async loadModel() {
    try {
      const modelResponse = await fetch('/static/model/isl_model.h5');
      const modelBlob = await modelResponse.blob();
      const modelArrayBuffer = await modelBlob.arrayBuffer();
      
      this.model = await tf.loadLayersModel(tf.io.browserHTTPRequest(
        '/static/model/isl_model.h5',
        { method: 'GET' }
      ));
      const classResponse = await fetch('/static/model/class_names.json');
      this.classNames = await classResponse.json();
      this.isReady = true;
      console.log('✅ ISL Model loaded:', this.classNames.length, 'classes');
    } catch (e) {
      console.error('❌ Model load failed:', e);
    }
  }

  async predictImage(imgElement) {
    if (!this.isReady) return null;

    const tensor = tf.browser.fromPixels(imgElement)
      .resizeNearestNeighbor([64, 64])
      .toFloat()
      .div(255.0)
      .expandDims();
    
    const predictions = this.model.predict(tensor);
    const top5 = Array.from(predictions.dataSync())
      .map((p, i) => ({ score: p, className: this.classNames[i] }))
      .sort((a, b) => b.score - a.score)
      .slice(0, 5);

    tensor.dispose();
    predictions.dispose();

    return top5[0]; // Best match
  }

  async predictFromSpeech(transcript) {
    // STT text → predict likely letters/words → sign sequence
    const words = transcript.toUpperCase().match(/[A-Z1-9]+/g) || [];
    const signs = [];
    
    for (let word of words.slice(0, 10)) { // Limit 10 chars
      for (let char of word.slice(0, 5)) { // 5 chars/word
        const pred = await this.predictImage(document.getElementById(`sign-ref-${char}`) || getDummySign(char));
        if (pred && pred.score > 0.3) {
          signs.push(pred.className);
        }
      }
    }
    return signs.slice(0, 20); // Limit display
  }
}

// Global predictor
const predictor = new ISLPredictor();

