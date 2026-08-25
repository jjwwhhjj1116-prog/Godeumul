import React from 'react';
import {
  interpolate,
  spring,
  useCurrentFrame,
  useVideoConfig,
} from 'remotion';
import {theme} from '../theme';

export type Point = {x: number; y: number};
export type TrackKey = Point & {frame: number};

const clamp = {
  extrapolateLeft: 'clamp' as const,
  extrapolateRight: 'clamp' as const,
};

const pathData = (points: Point[]) =>
  points.map((point, index) => `${index === 0 ? 'M' : 'L'} ${point.x} ${point.y}`).join(' ');

const smoothPolyline = (points: Point[], samplesPerSegment = 14): Point[] => {
  if (points.length < 3) return points;
  const result: Point[] = [];
  for (let index = 0; index < points.length - 1; index++) {
    const p0 = points[Math.max(0, index - 1)];
    const p1 = points[index];
    const p2 = points[index + 1];
    const p3 = points[Math.min(points.length - 1, index + 2)];
    for (let sample = 0; sample < samplesPerSegment; sample++) {
      const t = sample / samplesPerSegment;
      const t2 = t * t;
      const t3 = t2 * t;
      result.push({
        x: 0.5 * ((2 * p1.x) + (-p0.x + p2.x) * t
          + (2 * p0.x - 5 * p1.x + 4 * p2.x - p3.x) * t2
          + (-p0.x + 3 * p1.x - 3 * p2.x + p3.x) * t3),
        y: 0.5 * ((2 * p1.y) + (-p0.y + p2.y) * t
          + (2 * p0.y - 5 * p1.y + 4 * p2.y - p3.y) * t2
          + (-p0.y + 3 * p1.y - 3 * p2.y + p3.y) * t3),
      });
    }
  }
  result.push(points[points.length - 1]);
  return result;
};

const pointOnPolyline = (points: Point[], progress: number) => {
  if (points.length < 2) {
    return {...(points[0] ?? {x: 0, y: 0}), angle: 0};
  }

  const segments = points.slice(1).map((point, index) => {
    const previous = points[index];
    return {
      from: previous,
      to: point,
      length: Math.hypot(point.x - previous.x, point.y - previous.y),
    };
  });
  const total = segments.reduce((sum, segment) => sum + segment.length, 0);
  let remaining = Math.max(0, Math.min(1, progress)) * total;

  for (const segment of segments) {
    if (remaining <= segment.length) {
      const ratio = segment.length === 0 ? 0 : remaining / segment.length;
      return {
        x: segment.from.x + (segment.to.x - segment.from.x) * ratio,
        y: segment.from.y + (segment.to.y - segment.from.y) * ratio,
        angle: Math.atan2(segment.to.y - segment.from.y, segment.to.x - segment.from.x) * 180 / Math.PI,
      };
    }
    remaining -= segment.length;
  }

  const last = segments[segments.length - 1];
  return {
    x: last.to.x,
    y: last.to.y,
    angle: Math.atan2(last.to.y - last.from.y, last.to.x - last.from.x) * 180 / Math.PI,
  };
};

const trackedPoint = (frame: number, keys: TrackKey[]): Point => {
  if (keys.length === 0) return {x: 0, y: 0};
  if (keys.length === 1) return keys[0];

  const right = keys.findIndex((key) => key.frame >= frame);
  if (right <= 0) return right === 0 ? keys[0] : keys[keys.length - 1];
  const from = keys[right - 1];
  const to = keys[right];
  return {
    x: interpolate(frame, [from.frame, to.frame], [from.x, to.x], {
      ...clamp,
      easing: theme.ease.inOut,
    }),
    y: interpolate(frame, [from.frame, to.frame], [from.y, to.y], {
      ...clamp,
      easing: theme.ease.inOut,
    }),
  };
};

type FlowPathProps = {
  points: Point[];
  duration: number;
  delay?: number;
  pulseCount?: number;
  travelFrames?: number;
  color?: string;
  width?: number;
  opacity?: number;
};

export const FlowPath: React.FC<FlowPathProps> = ({
  points,
  duration,
  delay = 0,
  pulseCount = 6,
  travelFrames,
  color = theme.colors.primary,
  width = 5,
  opacity = 0.78,
}) => {
  const frame = useCurrentFrame();
  const {fps} = useVideoConfig();
  const travel = travelFrames ?? Math.round(fps * 2.1);
  const stagger = Math.round(fps * 0.18);
  const smoothPoints = smoothPolyline(points);
  const reveal = spring({frame: frame - delay, fps, config: theme.spring.smooth});
  const exit = interpolate(frame, [duration - Math.round(fps * 0.34), duration - 2], [1, 0], {
    ...clamp,
    easing: theme.ease.in,
  });
  const route = pathData(smoothPoints);
  const destination = pointOnPolyline(smoothPoints, 1);
  const arrival = spring({frame: frame - delay - travel, fps, config: theme.spring.snappy});

  return (
    <svg
      viewBox="0 0 1080 1920"
      style={{position: 'absolute', inset: 0, width: '100%', height: '100%', opacity: exit}}
    >
      <defs>
        <filter id="flow-soft-glow" x="-60%" y="-60%" width="220%" height="220%">
          <feGaussianBlur stdDeviation="7" result="blur" />
          <feMerge><feMergeNode in="blur" /><feMergeNode in="SourceGraphic" /></feMerge>
        </filter>
        <radialGradient id="arrival-glow">
          <stop offset="0%" stopColor={color} stopOpacity="0.72" />
          <stop offset="100%" stopColor={color} stopOpacity="0" />
        </radialGradient>
      </defs>

      <path
        d={route}
        fill="none"
        stroke={color}
        strokeWidth={2}
        strokeLinecap="round"
        strokeLinejoin="round"
        pathLength={1}
        strokeDasharray="0.025 0.04"
        strokeDashoffset={1 - reveal}
        opacity={0.2 * reveal}
      />

      {Array.from({length: pulseCount}).map((_, index) => {
        const localFrame = frame - delay - index * stagger;
        if (localFrame < 0) return null;
        const raw = (localFrame % travel) / travel;
        const progress = theme.ease.inOut(raw);
        const head = pointOnPolyline(smoothPoints, progress);
        const tail = pointOnPolyline(smoothPoints, Math.max(0, progress - 0.055));
        const drift = Math.sin((frame + index * 13) / (fps * 0.12)) * 4;
        const radians = head.angle * Math.PI / 180;
        const dx = -Math.sin(radians) * drift;
        const dy = Math.cos(radians) * drift;
        const pulseIn = spring({frame: localFrame, fps, config: theme.spring.snappy});
        return (
          <g key={index} opacity={pulseIn * opacity} filter="url(#flow-soft-glow)">
            <line
              x1={tail.x + dx}
              y1={tail.y + dy}
              x2={head.x + dx}
              y2={head.y + dy}
              stroke={color}
              strokeWidth={width}
              strokeLinecap="round"
            />
            <circle cx={head.x + dx} cy={head.y + dy} r={width * 0.75} fill={color} />
          </g>
        );
      })}

      <circle
        cx={destination.x}
        cy={destination.y}
        r={interpolate(arrival, [0, 1], [8, 62], {...clamp, easing: theme.ease.out})}
        fill="url(#arrival-glow)"
        opacity={interpolate(arrival, [0, 0.65, 1], [0, 0.52, 0.12], {
          ...clamp,
          easing: theme.ease.out,
        })}
      />
    </svg>
  );
};

type TrackedDimensionProps = {
  start: TrackKey[];
  end: TrackKey[];
  label: string;
  duration: number;
  delay?: number;
};

export const TrackedDimension: React.FC<TrackedDimensionProps> = ({
  start,
  end,
  label,
  duration,
  delay = 0,
}) => {
  const frame = useCurrentFrame();
  const {fps} = useVideoConfig();
  const from = trackedPoint(frame, start);
  const to = trackedPoint(frame, end);
  const enter = spring({frame: frame - delay, fps, config: theme.spring.smooth});
  const exit = interpolate(frame, [duration - Math.round(fps * 0.34), duration - 2], [1, 0], {
    ...clamp,
    easing: theme.ease.in,
  });
  const angle = Math.atan2(to.y - from.y, to.x - from.x) * 180 / Math.PI;
  const middle = {x: (from.x + to.x) / 2, y: (from.y + to.y) / 2};
  const labelY = middle.y - 34 - Math.sin(angle * Math.PI / 180) * 16;

  return (
    <svg viewBox="0 0 1080 1920" style={{position: 'absolute', inset: 0, width: '100%', height: '100%', opacity: exit}}>
      <g opacity={enter}>
        <line x1={from.x} y1={from.y} x2={to.x} y2={to.y}
          stroke={theme.colors.accent} strokeWidth={2} pathLength={1}
          strokeDasharray={1} strokeDashoffset={1 - enter} />
        {[from, to].map((point, index) => (
          <line key={index} x1={point.x} y1={point.y - 15 * enter} x2={point.x} y2={point.y + 15 * enter}
            stroke={theme.colors.primary} strokeWidth={4} strokeLinecap="round" />
        ))}
        <text x={middle.x} y={labelY} textAnchor="middle"
          fill={theme.colors.text} fontFamily={theme.fonts.body} fontSize={27}
          fontWeight={700} letterSpacing="-0.02em"
          style={{paintOrder: 'stroke', stroke: 'rgba(12,9,6,.76)', strokeWidth: 8}}>
          {label}
        </text>
      </g>
    </svg>
  );
};
