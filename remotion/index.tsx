import { Composition, registerRoot } from 'remotion';
import { CognistrationShort } from './Composition';

const FPS = 30;

registerRoot(() => {
  return (
    <Composition
      id="CognistrationShort"
      component={CognistrationShort}
      fps={FPS}
      width={1080}
      height={1920}
      durationInFrames={65 * FPS}
      defaultProps={{
        brainState: 'theta',
        audioPath: 'audio/theta.mp3',
        backgroundPath: 'backgrounds/2026-08-09-vertical-04-curl-field-weave.mp4',
        carrierHz: 200,
        durationSec: 65,
      }}
      // Each queue item carries its own length (45s-75s), so the composition
      // duration comes from the props instead of being hard-coded.
      calculateMetadata={({ props }) => {
        const seconds = Number((props as { durationSec?: number }).durationSec) || 65;
        return { durationInFrames: Math.round(seconds * FPS) };
      }}
    />
  );
});