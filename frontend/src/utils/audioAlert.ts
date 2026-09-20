// AquaGuard AI - Web Audio API Siren & Alert Synthesizer (Phase 9)
// Generates emergency audio alarms directly in-browser without external MP3 assets

class AlertAudioSynthesizer {
  private ctx: AudioContext | null = null;
  private sirenOsc: OscillatorNode | null = null;
  private lfoOsc: OscillatorNode | null = null;
  private gainNode: GainNode | null = null;
  private isPlaying = false;
  private muted = false;

  constructor() {
    this.muted = localStorage.getItem('aquaguard_audio_muted') === 'true';
  }

  private initContext() {
    if (!this.ctx) {
      const AudioCtx = window.AudioContext || (window as unknown as { webkitAudioContext: typeof AudioContext }).webkitAudioContext;
      this.ctx = new AudioCtx();
    }
    if (this.ctx.state === 'suspended') {
      this.ctx.resume();
    }
  }

  public isMuted(): boolean {
    return this.muted;
  }

  public setMuted(muted: boolean) {
    this.muted = muted;
    localStorage.setItem('aquaguard_audio_muted', String(muted));
    if (muted && this.isPlaying) {
      this.stopSiren();
    }
  }

  public toggleMute(): boolean {
    this.setMuted(!this.muted);
    return this.muted;
  }

  public playCriticalSiren() {
    if (this.muted || this.isPlaying) return;
    try {
      this.initContext();
      if (!this.ctx) return;

      const now = this.ctx.currentTime;

      // Master gain
      this.gainNode = this.ctx.createGain();
      this.gainNode.gain.setValueAtTime(0.15, now);
      this.gainNode.connect(this.ctx.destination);

      // Carrier oscillator (alarm tone)
      this.sirenOsc = this.ctx.createOscillator();
      this.sirenOsc.type = 'sawtooth';
      this.sirenOsc.frequency.setValueAtTime(880, now); // A5

      // LFO for frequency modulation (siren warble effect)
      this.lfoOsc = this.ctx.createOscillator();
      this.lfoOsc.type = 'sine';
      this.lfoOsc.frequency.setValueAtTime(3.5, now); // 3.5 Hz oscillation

      const lfoGain = this.ctx.createGain();
      lfoGain.gain.setValueAtTime(300, now); // +/- 300Hz sweep (580Hz to 1180Hz)

      this.lfoOsc.connect(lfoGain);
      lfoGain.connect(this.sirenOsc.frequency);

      this.sirenOsc.connect(this.gainNode);

      this.lfoOsc.start(now);
      this.sirenOsc.start(now);
      this.isPlaying = true;
    } catch {
      // Audio autoplay policy or browser restriction
    }
  }

  public stopSiren() {
    if (!this.isPlaying) return;
    try {
      if (this.gainNode && this.ctx) {
        this.gainNode.gain.linearRampToValueAtTime(0.001, this.ctx.currentTime + 0.1);
      }
      setTimeout(() => {
        try {
          this.sirenOsc?.stop();
          this.lfoOsc?.stop();
          this.sirenOsc?.disconnect();
          this.lfoOsc?.disconnect();
          this.gainNode?.disconnect();
        } catch {
          // Ignore cleanup errors
        }
        this.isPlaying = false;
        this.sirenOsc = null;
        this.lfoOsc = null;
        this.gainNode = null;
      }, 120);
    } catch {
      this.isPlaying = false;
    }
  }

  public playWarningChime() {
    if (this.muted) return;
    try {
      this.initContext();
      if (!this.ctx) return;

      const now = this.ctx.currentTime;
      const osc = this.ctx.createOscillator();
      const gain = this.ctx.createGain();

      osc.type = 'sine';
      osc.frequency.setValueAtTime(587.33, now); // D5
      osc.frequency.exponentialRampToValueAtTime(880, now + 0.15); // ramp to A5

      gain.gain.setValueAtTime(0.12, now);
      gain.gain.exponentialRampToValueAtTime(0.001, now + 0.4);

      osc.connect(gain);
      gain.connect(this.ctx.destination);

      osc.start(now);
      osc.stop(now + 0.4);
    } catch {
      // Audio policy safe
    }
  }
}

export const alertAudio = new AlertAudioSynthesizer();
