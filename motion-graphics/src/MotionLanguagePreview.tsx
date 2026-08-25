import React from 'react';
import {
  AbsoluteFill,
  interpolate,
  useCurrentFrame,
  useVideoConfig,
} from 'remotion';
import {FlowPath, TrackedDimension} from './components/IntegratedMotion';
import {theme} from './theme';

const clamp = {
  extrapolateLeft: 'clamp' as const,
  extrapolateRight: 'clamp' as const,
};

const BgMesh: React.FC = () => {
  const frame = useCurrentFrame();
  return (
    <AbsoluteFill style={{background: theme.colors.bg}}>
      <div style={{
        position: 'absolute', width: 1120, height: 1120, borderRadius: '50%',
        left: -420 + Math.sin(frame / 58) * 38, top: -390,
        background: `radial-gradient(circle, ${theme.colors.primary}2B, transparent 65%)`,
        filter: 'blur(58px)',
      }} />
      <div style={{
        position: 'absolute', width: 980, height: 980, borderRadius: '50%',
        right: -380 + Math.cos(frame / 73) * 32, bottom: -360,
        background: 'radial-gradient(circle, rgba(130,103,69,.18), transparent 68%)',
        filter: 'blur(72px)',
      }} />
    </AbsoluteFill>
  );
};

const Corridor: React.FC<{foreground?: boolean}> = ({foreground = false}) => {
  if (foreground) {
    return (
      <svg viewBox="0 0 1080 1920" style={{position: 'absolute', inset: 0, width: '100%', height: '100%'}}>
        <defs>
          <linearGradient id="pillar-face" x1="0" x2="1">
            <stop offset="0" stopColor="#241A10" />
            <stop offset="0.55" stopColor="#765834" />
            <stop offset="1" stopColor="#171008" />
          </linearGradient>
        </defs>
        <path d="M65 430 L210 390 L245 1510 L82 1620 Z" fill="url(#pillar-face)" />
        <path d="M835 350 L1000 430 L1015 1600 L820 1500 Z" fill="url(#pillar-face)" />
        <path d="M83 1620 L245 1510 L350 1538 L220 1710 Z" fill="#100C08" opacity=".9" />
        <path d="M820 1500 L1015 1600 L920 1715 L735 1540 Z" fill="#100C08" opacity=".9" />
      </svg>
    );
  }

  return (
    <svg viewBox="0 0 1080 1920" style={{position: 'absolute', inset: 0, width: '100%', height: '100%'}}>
      <defs>
        <linearGradient id="rear-wall" x1="0" y1="0" x2="0" y2="1">
          <stop offset="0" stopColor="#4A3925" />
          <stop offset="1" stopColor="#17110B" />
        </linearGradient>
        <linearGradient id="floor" x1="0" y1="0" x2="0" y2="1">
          <stop offset="0" stopColor="#2D2115" />
          <stop offset="1" stopColor="#090705" />
        </linearGradient>
        <radialGradient id="vent-light">
          <stop offset="0" stopColor="#F1C36F" stopOpacity=".85" />
          <stop offset="1" stopColor="#E8A33D" stopOpacity="0" />
        </radialGradient>
      </defs>
      <rect width="1080" height="1920" fill="#0D0A07" />
      <path d="M105 305 L975 305 L865 1540 L215 1540 Z" fill="url(#rear-wall)" />
      <path d="M215 1540 L865 1540 L1080 1920 L0 1920 Z" fill="url(#floor)" />
      <path d="M0 0 H1080 V310 H0 Z" fill="#080604" />
      <path d="M390 305 Q540 150 690 305 L650 1180 Q540 1260 430 1180 Z" fill="#110D09" />
      <ellipse cx="870" cy="440" rx="190" ry="210" fill="url(#vent-light)" />
      <ellipse cx="875" cy="435" rx="54" ry="82" fill="#E7B962" opacity=".62" />
      {Array.from({length: 9}).map((_, index) => (
        <line key={index} x1={160 + index * 95} y1="480" x2={250 + index * 73} y2="1540"
          stroke="rgba(244,233,218,.055)" strokeWidth="3" />
      ))}
      {Array.from({length: 6}).map((_, index) => (
        <path key={index} d={`M180 ${620 + index * 150} Q540 ${570 + index * 162} 900 ${620 + index * 150}`}
          fill="none" stroke="rgba(244,233,218,.06)" strokeWidth="3" />
      ))}
    </svg>
  );
};

const Dust: React.FC = () => {
  const frame = useCurrentFrame();
  const {fps} = useVideoConfig();
  return (
    <svg viewBox="0 0 1080 1920" style={{position: 'absolute', inset: 0, width: '100%', height: '100%'}}>
      {Array.from({length: 26}).map((_, index) => {
        const cycle = Math.round(fps * (2.8 + (index % 5) * 0.24));
        const local = (frame + index * 17) % cycle;
        const rise = interpolate(local, [0, cycle], [0, 1], {
          ...clamp,
          easing: theme.ease.inOut,
        });
        const x = 180 + ((index * 139) % 720) + Math.sin((frame + index * 19) / 27) * 18;
        const y = 1510 - rise * (430 + (index % 4) * 80);
        const opacity = Math.sin(rise * Math.PI) * (0.16 + (index % 3) * 0.06);
        return <circle key={index} cx={x} cy={y} r={2 + (index % 3)} fill="#F4E9DA" opacity={opacity} />;
      })}
    </svg>
  );
};

const Grade: React.FC = () => (
  <AbsoluteFill style={{pointerEvents: 'none'}}>
    <AbsoluteFill style={{background: '#8A5520', mixBlendMode: 'soft-light', opacity: 0.13}} />
    <AbsoluteFill style={{background: 'linear-gradient(180deg, rgba(0,0,0,.18), transparent 30%, transparent 68%, rgba(0,0,0,.30))'}} />
  </AbsoluteFill>
);

const Grain: React.FC = () => {
  const frame = useCurrentFrame();
  const noise = `url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='220' height='220'%3E%3Cfilter id='n'%3E%3CfeTurbulence type='fractalNoise' baseFrequency='.86' numOctaves='2'/%3E%3C/filter%3E%3Crect width='220' height='220' filter='url(%23n)' opacity='.48'/%3E%3C/svg%3E")`;
  return <AbsoluteFill style={{pointerEvents: 'none', backgroundImage: noise, backgroundSize: 220,
    backgroundPosition: `${(frame * 7) % 220}px ${(frame * 13) % 220}px`, opacity: 0.045, mixBlendMode: 'overlay'}} />;
};

const Vignette: React.FC = () => (
  <AbsoluteFill style={{pointerEvents: 'none', background: 'radial-gradient(ellipse at center, transparent 54%, rgba(0,0,0,.35) 100%)'}} />
);

export const MotionLanguagePreview: React.FC = () => {
  const frame = useCurrentFrame();
  const {fps, durationInFrames} = useVideoConfig();
  const scale = interpolate(frame, [0, durationInFrames], [1, 1.045], {
    ...clamp,
    easing: theme.ease.inOut,
  });
  const translateY = interpolate(frame, [0, durationInFrames], [10, -22], {
    ...clamp,
    easing: theme.ease.inOut,
  });
  const sceneTransform = `translateY(${translateY}px) scale(${scale})`;
  const flowPoints = [
    {x: 155, y: 1410}, {x: 285, y: 1320}, {x: 390, y: 1190},
    {x: 520, y: 1040}, {x: 660, y: 880}, {x: 760, y: 700}, {x: 875, y: 470},
  ];

  return (
    <AbsoluteFill style={{background: theme.colors.bg, overflow: 'hidden'}}>
      <BgMesh />
      <AbsoluteFill style={{transform: sceneTransform}}>
        <Corridor />
        <Dust />
        <FlowPath
          points={flowPoints}
          duration={durationInFrames}
          delay={Math.round(fps * 0.18)}
          pulseCount={7}
          travelFrames={Math.round(fps * 2.25)}
          width={5}
        />
        <Corridor foreground />
        <TrackedDimension
          start={[
            {frame: 0, x: 820, y: 512},
            {frame: durationInFrames / 2, x: 826, y: 502},
            {frame: durationInFrames, x: 834, y: 490},
          ]}
          end={[
            {frame: 0, x: 930, y: 512},
            {frame: durationInFrames / 2, x: 938, y: 502},
            {frame: durationInFrames, x: 946, y: 490},
          ]}
          label="환기구 폭 0.8 m"
          duration={durationInFrames}
          delay={Math.round(fps * 3.35)}
        />
      </AbsoluteFill>
      <Grade />
      <Grain />
      <Vignette />
    </AbsoluteFill>
  );
};
