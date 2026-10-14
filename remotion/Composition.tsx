import { useCurrentFrame, useVideoConfig, AbsoluteFill, Audio, Img, interpolate, staticFile } from 'remotion';

// ---------------------------------------------------------------------------
// Brain state config — matches the Cognistration machine palette
// ---------------------------------------------------------------------------
const STATE_INFO: Record<string, { label: string; hz: number; range: string; outcome: string; leftColor: string; rightColor: string; beatColor: string; glowColor: string }> = {
  delta:  { label: 'Delta',   hz: 2.5,  range: '0.5–4 Hz',  outcome: 'Deep sleep, inner restoration', leftColor: '#e2e8f0', rightColor: '#cbd5e1', beatColor: '#f1f5f9', glowColor: 'rgba(226,232,240,0.45)' },
  theta:  { label: 'Theta',   hz: 6.0,  range: '4–8 Hz',    outcome: 'Meditation, creative flow, inner voice', leftColor: '#b6ddcc', rightColor: '#d7c7aa', beatColor: '#d7eadf', glowColor: 'rgba(182,221,204,0.55)' },
  alpha:  { label: 'Alpha',   hz: 10.0, range: '8–13 Hz',   outcome: 'Calm awareness, quiet the noise', leftColor: '#b6ddcc', rightColor: '#d7c7aa', beatColor: '#d7eadf', glowColor: 'rgba(182,221,204,0.55)' },
  smr:    { label: 'SMR',     hz: 13.0, range: '12–15 Hz',  outcome: 'Still body, sharp mind', leftColor: '#a2d8d0', rightColor: '#d7c7aa', beatColor: '#c8f0e8', glowColor: 'rgba(162,216,208,0.45)' },
  beta:   { label: 'Beta',    hz: 18.0, range: '13–30 Hz',  outcome: 'Active focus, mental clarity', leftColor: '#e0b493', rightColor: '#d7c7aa', beatColor: '#f0d4b8', glowColor: 'rgba(224,180,147,0.45)' },
  gamma:  { label: 'Gamma',   hz: 38.0, range: '30–45 Hz',  outcome: 'Higher awareness, connected consciousness', leftColor: '#d7c7aa', rightColor: '#e0b493', beatColor: '#efe0c8', glowColor: 'rgba(215,199,170,0.45)' },
};

interface CognistrationShortProps {
  brainState: string;
  audioPath: string;
  carrierHz?: number;
}

// SVG wave helpers — match the machine's getSinePath / getEntrainmentPath
function sinePath(freq: number, amp: number, time: number, speed: number, w: number, h: number): string {
  const pts: string[] = [];
  const visualFreq = freq * 0.05;
  for (let x = 0; x <= w; x += 4) {
    const y = h / 2 + Math.sin(x * visualFreq * 0.5 - time * speed * 1.5) * amp;
    pts.push(`${x},${(y * 0.8 + h * 0.1).toFixed(1)}`);
  }
  return `M ${pts.join(' L ')}`;
}

function beatPath(freq: number, amp: number, time: number, speed: number, w: number, h: number): string {
  const pts: string[] = [];
  for (let x = 0; x <= w; x += 4) {
    const envelope = Math.sin(x * 0.015);
    const y = h / 2 + Math.sin(x * freq * 0.08 - time * speed * 1.2) * amp * envelope;
    pts.push(`${x},${(y * 0.8 + h * 0.1).toFixed(1)}`);
  }
  return `M ${pts.join(' L ')}`;
}

export const CognistrationShort: React.FC<CognistrationShortProps> = ({
  brainState,
  audioPath,
  carrierHz = 200,
}) => {
  const frame = useCurrentFrame();
  const { durationInFrames, fps, width, height } = useVideoConfig();
  const time = frame / fps;
  const state = STATE_INFO[brainState] || STATE_INFO.theta;
  const rightHz = carrierHz + state.hz;

  const introFade = interpolate(frame, [0, 20], [0, 1], { extrapolateRight: 'clamp' });
  const contentFade = interpolate(frame, [15, 40], [0, 1], { extrapolateRight: 'clamp' });
  const ctaStart = durationInFrames - 150;
  const ctaFade = interpolate(frame, [ctaStart, ctaStart + 50], [0, 1], { extrapolateLeft: 'clamp', extrapolateRight: 'clamp' });
  const outroFade = interpolate(frame, [durationInFrames - 15, durationInFrames - 1], [1, 0], { extrapolateLeft: 'clamp', extrapolateRight: 'clamp' });
  const fade = introFade * outroFade;

  const waveW = width - 104;  // account for 32px outer margins + 20px inner container padding on each side
  const waveH = 140;

  return (
    <AbsoluteFill style={{ backgroundColor: '#070811' }}>
      <Audio src={staticFile(audioPath)} />

      {/* Background — dark with subtle radial glow matching the brain state */}
      <AbsoluteFill style={{
        background: `
          radial-gradient(ellipse at 50% 30%, ${state.glowColor.replace(/0\.\d+/, '0.10')} 0%, transparent 65%),
          radial-gradient(ellipse at 50% 80%, rgba(7,8,17,0.98) 0%, #070811 100%)
        `
      }} />

      <AbsoluteFill style={{ opacity: fade }}>

        {/* App logo — top right */}
        <div style={{ position: 'absolute', top: 32, right: 28, zIndex: 10 }}>
          <Img src={staticFile('images/cognistration-mark.png')} style={{ width: 48, height: 48, opacity: 0.85 }} />
        </div>

        {/* Brain state label — top left */}
        <div style={{ position: 'absolute', top: 38, left: 32, zIndex: 10 }}>
          <span style={{
            fontFamily: 'ui-monospace, SFMono-Regular, Menlo, monospace',
            fontSize: 13, letterSpacing: '0.12em', textTransform: 'uppercase',
            color: 'rgba(255,255,255,0.45)',
          }}>{state.label} · {state.range}</span>
        </div>

        {/* CENTER — Large frequency display + expected outcome */}
        <div style={{
          position: 'absolute', top: '23%', left: 0, right: 0,
          display: 'flex', flexDirection: 'column', alignItems: 'center', gap: 8,
          opacity: contentFade,
        }}>
          <div style={{ display: 'flex', alignItems: 'baseline', gap: 16 }}>
            <span style={{ fontFamily: 'ui-monospace, SFMono-Regular, Menlo, monospace', fontSize: 72, fontWeight: 300, color: state.leftColor, letterSpacing: '-0.02em', lineHeight: 1 }}>{carrierHz}</span>
            <span style={{ fontFamily: 'ui-monospace, SFMono-Regular, Menlo, monospace', fontSize: 28, fontWeight: 300, color: 'rgba(255,255,255,0.25)' }}>Hz</span>
            <span style={{ fontFamily: 'ui-monospace, SFMono-Regular, Menlo, monospace', fontSize: 72, fontWeight: 300, color: state.rightColor, letterSpacing: '-0.02em', lineHeight: 1 }}>{rightHz.toFixed(1)}</span>
            <span style={{ fontFamily: 'ui-monospace, SFMono-Regular, Menlo, monospace', fontSize: 28, fontWeight: 300, color: 'rgba(255,255,255,0.25)' }}>Hz</span>
          </div>
          <div style={{ fontFamily: 'ui-monospace, SFMono-Regular, Menlo, monospace', fontSize: 18, fontWeight: 400, color: 'rgba(255,255,255,0.5)', letterSpacing: '0.06em' }}>
            {state.hz.toFixed(1)} Hz beat
          </div>
          <div style={{ fontFamily: 'system-ui, -apple-system, sans-serif', fontSize: 28, fontWeight: 300, color: 'rgba(255,255,255,0.8)', letterSpacing: '-0.01em', marginTop: 8, textAlign: 'center', padding: '0 40px' }}>
            {state.outcome}
          </div>
        </div>

        {/* THREE WAVES — matching the machine's layout */}
        <div style={{
          position: 'absolute', bottom: '22%', left: 32, right: 32,
          display: 'flex', flexDirection: 'column', gap: 20, opacity: contentFade,
        }}>
          {/* Left channel */}
          <div style={{ background: 'rgba(255,255,255,0.03)', border: `1px solid ${state.leftColor}15`, borderRadius: 20, padding: '12px 20px 8px' }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 4 }}>
              <span style={{ fontFamily: 'ui-monospace, SFMono-Regular, Menlo, monospace', fontSize: 11, color: state.leftColor, letterSpacing: '0.06em' }}>Left channel</span>
              <span style={{ fontFamily: 'ui-monospace, SFMono-Regular, Menlo, monospace', fontSize: 11, color: state.leftColor }}>{carrierHz} Hz</span>
            </div>
            <svg width={waveW} height={waveH} viewBox={`0 0 ${waveW} ${waveH}`} style={{ overflow: 'hidden' }}>
              <path d={sinePath(carrierHz, 30, time, 1.2, waveW, waveH)} fill="none" stroke={state.leftColor} strokeWidth={1.5} opacity={0.8} />
            </svg>
          </div>

          {/* Right channel */}
          <div style={{ background: 'rgba(255,255,255,0.03)', border: `1px solid ${state.rightColor}15`, borderRadius: 20, padding: '12px 20px 8px' }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 4 }}>
              <span style={{ fontFamily: 'ui-monospace, SFMono-Regular, Menlo, monospace', fontSize: 11, color: state.rightColor, letterSpacing: '0.06em' }}>Right channel</span>
              <span style={{ fontFamily: 'ui-monospace, SFMono-Regular, Menlo, monospace', fontSize: 11, color: state.rightColor }}>{rightHz.toFixed(1)} Hz</span>
            </div>
            <svg width={waveW} height={waveH} viewBox={`0 0 ${waveW} ${waveH}`} style={{ overflow: 'hidden' }}>
              <path d={sinePath(rightHz, 30, time, 1.3, waveW, waveH)} fill="none" stroke={state.rightColor} strokeWidth={1.5} opacity={0.75} />
            </svg>
          </div>

          {/* Beat wave with glow filter */}
          <div style={{ background: 'rgba(255,255,255,0.03)', border: `1px solid ${state.beatColor}18`, borderRadius: 20, padding: '12px 20px 8px' }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 4 }}>
              <span style={{ fontFamily: 'ui-monospace, SFMono-Regular, Menlo, monospace', fontSize: 11, color: 'rgba(255,255,255,0.6)', letterSpacing: '0.06em' }}>Perceived rhythm</span>
              <span style={{ fontFamily: 'ui-monospace, SFMono-Regular, Menlo, monospace', fontSize: 11, color: 'rgba(255,255,255,0.7)' }}>{state.hz.toFixed(1)} Hz · {state.label}</span>
            </div>
            <svg width={waveW} height={waveH} viewBox={`0 0 ${waveW} ${waveH}`} style={{ overflow: 'hidden' }}>
              <defs>
                <filter id="glow-wave">
                  <feGaussianBlur stdDeviation="3" result="blur" />
                  <feMerge><feMergeNode in="blur" /><feMergeNode in="SourceGraphic" /></feMerge>
                </filter>
              </defs>
              <path d={beatPath(state.hz, 40, time, 0.4, waveW, waveH)} fill="none" stroke={state.beatColor} strokeWidth={2.5} filter="url(#glow-wave)" opacity={0.9} />
            </svg>
          </div>
        </div>

        {/* CTA — last 5 seconds */}
        <div style={{
          position: 'absolute', bottom: '8%', left: 0, right: 0,
          display: 'flex', flexDirection: 'column', alignItems: 'center', gap: 14,
          opacity: ctaFade,
        }}>
          <div style={{ fontFamily: 'system-ui, -apple-system, sans-serif', fontSize: 26, fontWeight: 300, color: 'rgba(255,255,255,0.9)', letterSpacing: '-0.01em' }}>
            Connect with your higher self
          </div>
          <div style={{ background: 'rgba(255,255,255,0.06)', border: '1px solid rgba(182,221,204,0.15)', borderRadius: 14, padding: '12px 32px', backdropFilter: 'blur(12px)' }}>
            <span style={{ fontFamily: 'ui-monospace, SFMono-Regular, Menlo, monospace', fontSize: 18, fontWeight: 500, color: '#b6ddcc', letterSpacing: '0.03em' }}>
              cognistration.com/machine
            </span>
          </div>
        </div>

      </AbsoluteFill>
    </AbsoluteFill>
  );
};