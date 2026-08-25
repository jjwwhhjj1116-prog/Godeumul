import React from 'react';
import {Composition} from 'remotion';
import {AncientArtifactFilm} from './AncientArtifactFilm';

export const Root: React.FC = () => (
  <Composition
    id="AncientArtifactFilm"
    component={AncientArtifactFilm}
    durationInFrames={3916}
    fps={30}
    width={1080}
    height={1920}
  />
);
