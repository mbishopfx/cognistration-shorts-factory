import {
  useCurrentFrame,
  useVideoConfig,
  AbsoluteFill,
  Audio,
  Img,
  OffthreadVideo,
  interpolate,
  staticFile,
} from 'remotion';

// ---------------------------------------------------------------------------
// Brain state config — matches the Cognistration machine palette
// ---------------------------------------------------------------------------
type StateInfo = {
  label: string;
  hz: number;
  range: string;
  outcome: string;
  leftColor: string;
  rightColor: string;
  beatColor: string;
  glowColor: string;
};

const STATE_INFO: Record<string, StateInfo> = {
  delta:  { label: 'Delta', hz: 2.5,  range: '0.5–4 Hz',  outcome: 'Deep sleep, inner restoration', leftColor: '#e2e8f0', rightColor: '#cbd5e1', beatColor: '#f1f5f9', glowColor: 'rgba(226,232,240,0.45)' },
  theta:  { label: 'Theta', hz: 6.0,  range: '4–8 Hz',    outcome: 'Meditation, creative flow, inner voice', leftColor: '#b6ddcc', rightColor: '#d7c7aa', beatColor: '#d7eadf', glowColor: 'rgba(182,221,204,0.55)' },
  alpha:  { label: 'Alpha', hz: 10.0, range: '8–13 Hz',   outcome: 'Calm awareness, quiet the noise', leftColor: '#b6ddcc', rightColor: '#d7c7aa', beatColor: '#d7eadf', glowColor: 'rgba(182,221,204,0.55)' },
  smr:    { label: 'SMR',   hz: 13.0, range: '12–15 Hz',  outcome: 'Still body, sharp mind', leftColor: '#a2d8d0', rightColor: '#d7c7aa', beatColor: '#c8f0e8', glowColor: 'rgba(162,216,208,0.45)' },
  beta:   { label: 'Beta',  hz: 18.0, range: '13–30 Hz',  outcome: 'Active focus, mental clarity', leftColor: '#e0b493', rightColor: '#d7c7aa', beatColor: '#f0d4b8', glowColor: 'rgba(224,180,147,0.45)' },
  gamma:  { label: 'Gamma', hz: 38.0, range: '30–45 Hz',  outcome: 'Higher awareness, connected consciousness', leftColor: '#d7c7aa', rightColor: '#e0b493', beatColor: '#efe0c8', glowColor: 'rgba(215,199,170,0.45)' },
};

export interface CognistrationShortProps {
  brainState: string;
  audioPath: string;
  backgroundPath?: string;
  carrierHz?: number;
  durationSec?: number;
}

const MONO = 'ui-monospace, SFMono-Regular, Menlo, monospace';
const SANS = 'system-ui, -apple-system, "Segoe UI", sans-serif';

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

function WaveCard({
  label,
  readout,
  color,
  border,
  path,
  waveW,
  waveH,
  glow,
}: {
  label: string;
  readout: string;
  color: string;
  border: string;
  path: string;
  waveW: number;
  waveH: number;
  glow?: boolean;
}) {
  return (
    <div
      style={{
        background: 'rgba(6,8,14,0.42)',
        border: `1px solid ${border}`,
        borderRadius: 20,
        padding: '12px 20px 8px',
        backdropFilter: 'blur(6px)',
      }}
    >
      <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 4 }}>
        <span style={{ fontFamily: MONO, fontSize: 12, color, letterSpacing: '0.06em' }}>{label}</span>
        <span style={{ fontFamily: MONO, fontSize: 12, color }}>{readout}</span>
      </div>
      <svg width={waveW} height={waveH} viewBox={`0 0 ${waveW} ${waveH}`} style={{ overflow: 'hidden', display: 'block' }}>
        {glow && (
          <defs>
            <filter id="glow-wave">
              <feGaussianBlur stdDeviation="3" result="blur" />
              <feMerge>
                <feMergeNode in="blur" />
                <feMergeNode in="SourceGraphic" />
              </feMerge>
            </filter>
          </defs>
        )}
        <path
          d={path}
          fill="none"
          stroke={color}
          strokeWidth={glow ? 2.5 : 1.5}
          filter={glow ? 'url(#glow-wave)' : undefined}
          opacity={0.9}
        />
      </svg>
    </div>
  );
}

export const CognistrationShort: React.FC<CognistrationShortProps> = ({
  brainState,
  audioPath,
  backgroundPath,
  carrierHz = 200,
}) => {
  const frame = useCurrentFrame();
  const { durationInFrames, fps, width } = useVideoConfig();
  const time = frame / fps;
  const state = STATE_INFO[brainState] || STATE_INFO.theta;
  const rightHz = carrierHz + state.hz;

  const introFade = interpolate(frame, [0, 22], [0, 1], { extrapolateRight: 'clamp' });
  const contentFade = interpolate(frame, [16, 44], [0, 1], { extrapolateRight: 'clamp' });

  // Last five seconds: the machine fades away and the app CTA takes over.
  const ctaStart = durationInFrames - 150;
  const machineOut = interpolate(frame, [ctaStart, ctaStart + 55], [1, 0], {
    extrapolateLeft: 'clamp',
    extrapolateRight: 'clamp',
  });
  const ctaFade = interpolate(frame, [ctaStart + 20, ctaStart + 70], [0, 1], {
    extrapolateLeft: 'clamp',
    extrapolateRight: 'clamp',
  });
  const outroFade = interpolate(frame, [durationInFrames - 12, durationInFrames - 1], [1, 0], {
    extrapolateLeft: 'clamp',
    extrapolateRight: 'clamp',
  });
  const fade = introFade * outroFade;

  const waveW = width - 104; // 32px outer margins + 20px inner padding per side
  const waveH = 130;

  return (
    <AbsoluteFill style={{ backgroundColor: '#070811' }}>
      <Audio src={staticFile(audioPath)} />

      {/* ── LAYER 1: the HTML animation, running behind everything ──
          Optional: a sandbox without a working Chromium can render without it. */}
      {backgroundPath ? (
        <AbsoluteFill style={{ opacity: 0.62 }}>
          <OffthreadVideo
            src={staticFile(backgroundPath)}
            muted
            style={{ width: '100%', height: '100%', objectFit: 'cover' }}
          />
        </AbsoluteFill>
      ) : null}

      {/* ── LAYER 2: scrim so the machine UI and copy stay readable ── */}
      <AbsoluteFill
        style={{
          background: `linear-gradient(180deg,
            rgba(7,8,17,0.72) 0%,
            rgba(7,8,17,0.34) 26%,
            rgba(7,8,17,0.30) 62%,
            rgba(7,8,17,0.86) 100%)`,
        }}
      />
      <AbsoluteFill
        style={{
          background: `radial-gradient(ellipse at 50% 34%, ${state.glowColor.replace(/0\.\d+/, '0.12')} 0%, transparent 62%)`,
        }}
      />

      <AbsoluteFill style={{ opacity: fade }}>

        {/* ── Top bar: state label (left) + app icon (right) ── */}
        <div style={{ position: 'absolute', top: 40, left: 34, zIndex: 20 }}>
          <span style={{
            fontFamily: MONO,
            fontSize: 14,
            letterSpacing: '0.16em',
            textTransform: 'uppercase',
            color: 'rgba(255,255,255,0.62)',
            textShadow: '0 1px 10px rgba(7,8,17,0.9)',
          }}>
            {state.label} · {state.range}
          </span>
        </div>

        <div style={{
          position: 'absolute', top: 30, right: 30, zIndex: 20,
          display: 'flex', flexDirection: 'column', alignItems: 'center', gap: 6,
        }}>
          <div style={{
            padding: 6,
            borderRadius: 20,
            background: 'rgba(6,8,14,0.45)',
            border: '1px solid rgba(255,255,255,0.16)',
            backdropFilter: 'blur(8px)',
          }}>
            <Img
              src={staticFile('images/cognistration-app-icon.png')}
              style={{ width: 78, height: 78, borderRadius: 15, display: 'block' }}
            />
          </div>
          <span style={{
            fontFamily: MONO,
            fontSize: 10,
            letterSpacing: '0.14em',
            textTransform: 'uppercase',
            color: 'rgba(255,255,255,0.55)',
          }}>
            App Store
          </span>
        </div>

        {/* ── Machine readout: frequencies + expected state ── */}
        <div style={{
          position: 'absolute', top: '20%', left: 0, right: 0,
          display: 'flex', flexDirection: 'column', alignItems: 'center', gap: 10,
          opacity: contentFade * machineOut,
        }}>
          <span style={{
            fontFamily: MONO, fontSize: 12, letterSpacing: '0.22em',
            textTransform: 'uppercase', color: 'rgba(255,255,255,0.45)',
          }}>
            Cognistration session
          </span>
          <div style={{ display: 'flex', alignItems: 'baseline', gap: 14 }}>
            <span style={{ fontFamily: MONO, fontSize: 76, fontWeight: 300, color: state.leftColor, letterSpacing: '-0.02em', lineHeight: 1, textShadow: '0 2px 24px rgba(7,8,17,0.9)' }}>{carrierHz}</span>
            <span style={{ fontFamily: MONO, fontSize: 26, fontWeight: 300, color: 'rgba(255,255,255,0.32)' }}>Hz</span>
            <span style={{ fontFamily: MONO, fontSize: 76, fontWeight: 300, color: state.rightColor, letterSpacing: '-0.02em', lineHeight: 1, textShadow: '0 2px 24px rgba(7,8,17,0.9)' }}>{rightHz.toFixed(1)}</span>
            <span style={{ fontFamily: MONO, fontSize: 26, fontWeight: 300, color: 'rgba(255,255,255,0.32)' }}>Hz</span>
          </div>
          <div style={{ fontFamily: MONO, fontSize: 20, color: 'rgba(255,255,255,0.62)', letterSpacing: '0.08em' }}>
            {state.hz.toFixed(1)} Hz binaural beat
          </div>
          <div style={{
            fontFamily: SANS, fontSize: 32, fontWeight: 300, color: 'rgba(255,255,255,0.94)',
            letterSpacing: '-0.01em', marginTop: 6, textAlign: 'center', padding: '0 44px',
            textShadow: '0 2px 20px rgba(7,8,17,0.95)',
          }}>
            {state.outcome}
          </div>
        </div>

        {/* ── Machine waves: two carriers + the perceived beat ── */}
        <div style={{
          position: 'absolute', bottom: '19%', left: 32, right: 32,
          display: 'flex', flexDirection: 'column', gap: 18,
          opacity: contentFade * machineOut,
        }}>
          <WaveCard
            label="Left ear carrier"
            readout={`${carrierHz} Hz`}
            color={state.leftColor}
            border={`${state.leftColor}2e`}
            path={sinePath(carrierHz, 30, time, 1.2, waveW, waveH)}
            waveW={waveW}
            waveH={waveH}
          />
          <WaveCard
            label="Right ear carrier"
            readout={`${rightHz.toFixed(1)} Hz`}
            color={state.rightColor}
            border={`${state.rightColor}2e`}
            path={sinePath(rightHz, 30, time, 1.3, waveW, waveH)}
            waveW={waveW}
            waveH={waveH}
          />
          <WaveCard
            label="Perceived beat"
            readout={`${state.hz.toFixed(1)} Hz · ${state.label}`}
            color={state.beatColor}
            border={`${state.beatColor}33`}
            path={beatPath(state.hz, 40, time, 0.4, waveW, waveH)}
            waveW={waveW}
            waveH={waveH}
            glow
          />
        </div>

        {/* ── Closing CTA to the mobile app ── */}
        <AbsoluteFill style={{
          opacity: ctaFade,
          display: 'flex',
          flexDirection: 'column',
          alignItems: 'center',
          justifyContent: 'center',
          gap: 26,
          padding: '0 60px',
        }}>
          <Img
            src={staticFile('images/cognistration-app-icon.png')}
            style={{ width: 132, height: 132, borderRadius: 30, boxShadow: '0 12px 48px rgba(0,0,0,0.55)' }}
          />
          <div style={{
            fontFamily: SANS, fontSize: 40, fontWeight: 300, color: '#ffffff',
            letterSpacing: '-0.02em', textAlign: 'center', lineHeight: 1.25,
            textShadow: '0 2px 24px rgba(7,8,17,0.95)',
          }}>
            Connect with your higher self
          </div>
          <div style={{
            fontFamily: SANS, fontSize: 22, color: 'rgba(255,255,255,0.72)',
            textAlign: 'center', letterSpacing: '0.01em',
          }}>
            Guide your own brain states with the Cognistration app
          </div>
          <Img
            src={staticFile('images/download-on-the-app-store.svg')}
            style={{ width: 250, height: 'auto', display: 'block' }}
          />
          <div style={{
            fontFamily: MONO, fontSize: 17, color: '#b6ddcc', letterSpacing: '0.05em',
            border: '1px solid rgba(182,221,204,0.28)', borderRadius: 14,
            padding: '12px 28px', background: 'rgba(255,255,255,0.05)',
          }}>
            cognistration.com/machine
          </div>
        </AbsoluteFill>

      </AbsoluteFill>
    </AbsoluteFill>
  );
};
