import {Easing} from 'remotion';

export const theme = {
  colors: {
    bg: '#0C0906',
    bgAlt: '#18110B',
    primary: '#E8A33D',
    accent: '#F4E9DA',
    text: '#FFF9EF',
    textDim: '#C8B9A7',
    glow: 'rgba(232, 163, 61, 0.42)',
  },
  fonts: {
    display: 'Gmarket Sans',
    body: 'Noto Sans KR',
    mono: 'Noto Sans KR',
  },
  ease: {
    out: Easing.bezier(0.16, 1, 0.3, 1),
    inOut: Easing.bezier(0.83, 0, 0.17, 1),
    in: Easing.bezier(0.7, 0, 0.84, 0),
  },
  spring: {
    snappy: {damping: 14, stiffness: 160, mass: 0.6},
    smooth: {damping: 20, stiffness: 90, mass: 1},
    bouncy: {damping: 11, stiffness: 170, mass: 0.7},
  },
} as const;
