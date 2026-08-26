import React from 'react';
import {
  AbsoluteFill,
  Audio,
  Img,
  interpolate,
  OffthreadVideo,
  Sequence,
  staticFile,
  useCurrentFrame,
  useVideoConfig,
} from 'remotion';

export type CaptionCue = {
  n: number;
  scene: number;
  text: string;
  start: number;
  end: number;
};

export type V5FinalFilmProps = {
  sceneDurations: number[];
  clipDurations: number[];
  captions: CaptionCue[];
  audioFile: string;
  fontFile: string;
  watermarkFile: string;
  clipDirectory?: string;
  impactCues?: ImpactCue[];
};

export type ImpactCue = {
  scene: number;
  at: number;
  kind: 'punch' | 'shake' | 'punch-shake';
  strength?: number;
};

const clamp = {
  extrapolateLeft: 'clamp' as const,
  extrapolateRight: 'clamp' as const,
};

const SceneVideo: React.FC<{
  scene: number;
  targetSeconds: number;
  sourceSeconds: number;
  clipDirectory: string;
  impactCues: ImpactCue[];
}> = ({scene, targetSeconds, sourceSeconds, clipDirectory, impactCues}) => {
  const {fps} = useVideoConfig();
  const frame = useCurrentFrame();
  const durationInFrames = Math.max(1, Math.round(targetSeconds * fps));
  const file = `${clipDirectory}/${String(scene).padStart(3, '0')}.mp4`;
  let punch = 0;
  let shakeX = 0;
  let shakeY = 0;
  for (const cue of impactCues) {
    const distance = Math.abs(frame - cue.at * fps);
    const envelope = interpolate(distance, [0, 2, 10], [1, 0.62, 0], clamp);
    const strength = cue.strength ?? 1;
    if (cue.kind === 'punch' || cue.kind === 'punch-shake') {
      punch += envelope * strength;
    }
    if (cue.kind === 'shake' || cue.kind === 'punch-shake') {
      shakeX += Math.sin(frame * 2.35) * 8 * envelope * strength;
      shakeY += Math.sin(frame * 3.15 + 1.3) * 4 * envelope * strength;
    }
  }
  const scale = 1.015 + Math.min(0.055, punch * 0.045);

  return (
    <AbsoluteFill style={{backgroundColor: '#080604'}}>
      <OffthreadVideo
        src={staticFile(file)}
        muted
        playbackRate={sourceSeconds / targetSeconds}
        style={{
          width: '100%',
          height: '100%',
          objectFit: 'cover',
          transform: `translate3d(${shakeX}px, ${shakeY}px, 0) scale(${scale})`,
          transformOrigin: 'center center',
        }}
      />
      <AbsoluteFill
        style={{
          pointerEvents: 'none',
          background:
            'linear-gradient(180deg, rgba(0,0,0,.10) 0%, transparent 22%, transparent 68%, rgba(0,0,0,.26) 100%)',
        }}
      />
      <AbsoluteFill
        style={{
          pointerEvents: 'none',
          boxShadow: 'inset 0 0 150px rgba(0,0,0,.22)',
          opacity: interpolate(useCurrentFrame(), [0, 6, durationInFrames - 6, durationInFrames - 1], [0.86, 1, 1, 0.92], clamp),
        }}
      />
    </AbsoluteFill>
  );
};

const AnimatedCaption: React.FC<{cues: CaptionCue[]}> = ({cues}) => {
  const frame = useCurrentFrame();
  const {fps} = useVideoConfig();
  const now = frame / fps;
  const cue = cues.find((item) => now >= item.start && now < item.end);

  if (!cue) return null;

  const startFrame = Math.round(cue.start * fps);
  const endFrame = Math.round(cue.end * fps);
  const enter = interpolate(frame, [startFrame, startFrame + 5], [0, 1], clamp);
  const exit = interpolate(frame, [Math.max(startFrame + 6, endFrame - 4), endFrame], [1, 0], clamp);
  const opacity = Math.min(enter, exit);
  const scale = 0.94 + 0.06 * enter;

  return (
    <div
      style={{
        position: 'absolute',
        left: 52,
        right: 52,
        top: 1120,
        display: 'flex',
        justifyContent: 'center',
        pointerEvents: 'none',
        opacity,
        transform: `translateY(${(1 - enter) * 18}px) scale(${scale})`,
      }}
    >
      <div
        style={{
          maxWidth: 950,
          color: '#fffaf0',
          fontFamily: 'Godeumul Caption, Noto Sans KR, sans-serif',
          fontSize: 72,
          fontWeight: 850,
          lineHeight: 1.14,
          letterSpacing: '-0.055em',
          textAlign: 'center',
          whiteSpace: 'nowrap',
          paintOrder: 'stroke fill',
          WebkitTextStroke: '9px rgba(0,0,0,.92)',
          textShadow: '0 5px 16px rgba(0,0,0,.82)',
        }}
      >
        {cue.text}
      </div>
    </div>
  );
};

const FilmTexture: React.FC = () => {
  const frame = useCurrentFrame();
  const noise = `url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='180' height='180'%3E%3Cfilter id='n'%3E%3CfeTurbulence type='fractalNoise' baseFrequency='.88' numOctaves='2' seed='${frame % 7}'/%3E%3C/filter%3E%3Crect width='180' height='180' filter='url(%23n)' opacity='.42'/%3E%3C/svg%3E")`;
  return (
    <AbsoluteFill
      style={{
        pointerEvents: 'none',
        backgroundImage: noise,
        backgroundSize: '180px 180px',
        opacity: 0.025,
        mixBlendMode: 'soft-light',
      }}
    />
  );
};

export const V5FinalFilm: React.FC<V5FinalFilmProps> = ({
  sceneDurations,
  clipDurations,
  captions,
  audioFile,
  fontFile,
  watermarkFile,
  clipDirectory = 'clips_v5',
  impactCues = [],
}) => {
  const {fps} = useVideoConfig();
  let cursor = 0;

  return (
    <AbsoluteFill style={{backgroundColor: '#080604', overflow: 'hidden'}}>
      <style>{`
        @font-face {
          font-family: 'Godeumul Caption';
          src: url('${staticFile(fontFile)}') format('truetype');
          font-weight: 100 900;
          font-display: block;
        }
      `}</style>

      {sceneDurations.map((seconds, index) => {
        const scene = index + 1;
        const from = cursor;
        const next = Math.round(sceneDurations.slice(0, scene).reduce((sum, value) => sum + value, 0) * fps);
        const durationInFrames = Math.max(1, next - from);
        cursor = next;
        return (
          <Sequence key={scene} from={from} durationInFrames={durationInFrames} premountFor={fps}>
            <SceneVideo
              scene={scene}
              targetSeconds={seconds}
              sourceSeconds={clipDurations[index]}
              clipDirectory={clipDirectory}
              impactCues={impactCues.filter((cue) => cue.scene === scene)}
            />
          </Sequence>
        );
      })}

      <Audio src={staticFile(audioFile)} />
      <FilmTexture />
      <AnimatedCaption cues={captions} />
      <Img
        src={staticFile(watermarkFile)}
        style={{
          position: 'absolute',
          right: 48,
          bottom: 72,
          width: 150,
          height: 150,
          objectFit: 'contain',
          opacity: 0.56,
          filter: 'drop-shadow(0 3px 8px rgba(0,0,0,.45))',
        }}
      />
    </AbsoluteFill>
  );
};
