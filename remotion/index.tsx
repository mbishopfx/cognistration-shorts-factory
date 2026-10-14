import { Composition, registerRoot } from 'remotion';
import { CognistrationShort } from './Composition';

registerRoot(() => {
  return (
    <Composition
      id="CognistrationShort"
      component={CognistrationShort}
      durationInFrames={1950}
      fps={30}
      width={1080}
      height={1920}
      defaultProps={{
        brainState: 'theta',
        audioPath: 'output/audio/theta-6hz-binaural.mp3',
        carrierHz: 200,
      }}
    />
  );
});