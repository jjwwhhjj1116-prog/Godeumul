import React from 'react';
import {Composition} from 'remotion';
import {AncientArtifactFilm} from './AncientArtifactFilm';
import {ThreeDMotionPreview} from './ThreeDMotionPreview';
import {V5FinalFilm, V5FinalFilmProps} from './V5FinalFilm';

const v5Defaults: V5FinalFilmProps = {
  sceneDurations: [7.059, 7.616, 7.152, 7.895, 9.474, 7.523, 6.92, 6.037, 2.694, 3.204, 4.876, 6.084, 5.201, 7.384, 6.409, 5.851, 7.616, 5.805, 6.873, 5.944, 5.294, 4.83, 5.944, 7.523, 6.362, 7.802, 4.737],
  clipDurations: [8, 8, 8, 10.005, 10.005, 8, 8, 8, 4.01, 4.01, 6.016, 8, 6.016, 8, 8, 8, 8, 8, 8, 8, 6.016, 6.016, 8, 8, 8, 10.005, 6.016],
  captions: [],
  audioFile: 'audio_v5/EP01_진시황릉_TTS검수본_v5.mp3',
  fontFile: 'NotoSansKR-VF.ttf',
  watermarkFile: 'watermark.png',
};

export const Root: React.FC = () => (
  <>
    <Composition
      id="Legacy3DPrototype"
      component={ThreeDMotionPreview}
      durationInFrames={180}
      fps={30}
      width={1080}
      height={1920}
    />
    <Composition
      id="LegacyEP01Blocked"
      component={AncientArtifactFilm}
      durationInFrames={3916}
      fps={30}
      width={1080}
      height={1920}
    />
    <Composition
      id="V5Final"
      component={V5FinalFilm}
      durationInFrames={5104}
      fps={30}
      width={1080}
      height={1920}
      defaultProps={v5Defaults}
      calculateMetadata={({props}) => ({
        durationInFrames: Math.ceil(props.sceneDurations.reduce((sum, value) => sum + value, 0) * 30),
      })}
    />
  </>
);
