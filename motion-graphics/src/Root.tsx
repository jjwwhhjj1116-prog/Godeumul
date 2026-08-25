import React from 'react';
import {Composition} from 'remotion';
import {AncientArtifactFilm} from './AncientArtifactFilm';
import {ThreeDMotionPreview} from './ThreeDMotionPreview';

export const Root: React.FC = () => (
  <>
    <Composition
      id="MotionLanguagePreview"
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
  </>
);
