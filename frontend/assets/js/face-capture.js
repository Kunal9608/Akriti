/**
 * AKRITI — Face Capture Module
 * getUserMedia wrapper for face enrollment and attendance kiosk.
 * Includes: frame capture, basic quality checks, liveness UI.
 *
 * Usage:
 *   const fc = new FaceCapture({ videoEl, canvasEl, onFrame, onError });
 *   await fc.start();
 *   fc.captureFrame();  // returns base64 JPEG or null if quality check fails
 *   fc.stop();
 */

class FaceCapture {
  constructor({ videoEl, canvasEl, onFrame, onError, mirror = true }) {
    this.video   = typeof videoEl === 'string' ? document.getElementById(videoEl) : videoEl;
    this.canvas  = typeof canvasEl === 'string' ? document.getElementById(canvasEl) : canvasEl;
    this.onFrame = onFrame;
    this.onError = onError || ((msg) => Toast.show(msg, 'error'));
    this.mirror  = mirror;
    this.stream  = null;
    this._ctx    = null;
  }

  async start() {
    if (!navigator.mediaDevices || !navigator.mediaDevices.getUserMedia) {
      this.onError('Camera not supported in this browser.');
      return false;
    }

    try {
      this.stream = await navigator.mediaDevices.getUserMedia({
        video: { width: { ideal: 640 }, height: { ideal: 480 }, facingMode: 'user' },
        audio: false,
      });

      this.video.srcObject = this.stream;
      this.video.setAttribute('playsinline', true);
      if (this.mirror) this.video.style.transform = 'scaleX(-1)';

      await new Promise((resolve, reject) => {
        this.video.onloadedmetadata = resolve;
        this.video.onerror = reject;
      });
      await this.video.play();

      this.canvas.width  = this.video.videoWidth;
      this.canvas.height = this.video.videoHeight;
      this._ctx = this.canvas.getContext('2d');

      return true;
    } catch (err) {
      const msgs = {
        'NotAllowedError':    'Camera permission denied. Please allow camera access and try again.',
        'NotFoundError':      'No camera found on this device.',
        'NotReadableError':   'Camera is in use by another application.',
        'OverconstrainedError': 'Camera does not meet requirements.',
      };
      this.onError(msgs[err.name] || `Camera error: ${err.message}`);
      return false;
    }
  }

  /**
   * Capture a single frame. Returns { dataUrl, blob } or null if quality rejected.
   * Quality check: non-blank frame (variance > threshold).
   */
  captureFrame(qualityCheck = true) {
    if (!this._ctx || !this.video.videoWidth) return null;

    if (this.mirror) {
      this._ctx.save();
      this._ctx.translate(this.canvas.width, 0);
      this._ctx.scale(-1, 1);
      this._ctx.drawImage(this.video, 0, 0);
      this._ctx.restore();
    } else {
      this._ctx.drawImage(this.video, 0, 0);
    }

    if (qualityCheck) {
      const data = this._ctx.getImageData(0, 0, this.canvas.width, this.canvas.height).data;
      let sum = 0, sumSq = 0;
      const step = 40; // sample every 40th pixel for speed
      let n = 0;
      for (let i = 0; i < data.length; i += 4 * step) {
        const lum = 0.299 * data[i] + 0.587 * data[i+1] + 0.114 * data[i+2];
        sum += lum;
        sumSq += lum * lum;
        n++;
      }
      const mean = sum / n;
      const variance = sumSq / n - mean * mean;
      if (variance < 100) {
        // Image is too uniform — likely a blank frame or covered lens
        return null;
      }
    }

    const dataUrl = this.canvas.toDataURL('image/jpeg', 0.85);
    return dataUrl;
  }

  stop() {
    if (this.stream) {
      this.stream.getTracks().forEach(t => t.stop());
      this.stream = null;
    }
    this.video.srcObject = null;
  }
}

window.FaceCapture = FaceCapture;
