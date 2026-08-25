import React from 'react';
import {
  AbsoluteFill,
  interpolate,
  OffthreadVideo,
  Sequence,
  spring,
  staticFile,
  useCurrentFrame,
  useVideoConfig,
} from 'remotion';
import {sceneTimings} from './scene-data';
import {theme} from './theme';

const clamp = {
  extrapolateLeft: 'clamp' as const,
  extrapolateRight: 'clamp' as const,
};

const useMotion = (duration: number, delay = 0) => {
  const frame = useCurrentFrame();
  const enter = interpolate(frame, [delay, delay + 18], [0, 1], {
    ...clamp,
    easing: theme.ease.out,
  });
  const exit = interpolate(frame, [Math.max(delay + 19, duration - 12), duration - 2], [1, 0], {
    ...clamp,
    easing: theme.ease.in,
  });
  return {frame, enter, exit, visible: enter * exit};
};

const glass: React.CSSProperties = {
  background: 'linear-gradient(135deg, rgba(12,9,6,.82), rgba(24,17,11,.58))',
  border: '1px solid rgba(244,233,218,.24)',
  boxShadow: '0 22px 70px rgba(0,0,0,.34)',
  backdropFilter: 'blur(12px)',
};

const Header: React.FC<{eyebrow: string; title: string; duration: number; delay?: number}> = ({
  eyebrow,
  title,
  duration,
  delay = 0,
}) => {
  const {enter, exit, visible} = useMotion(duration, delay);
  return (
    <div
      style={{
        position: 'absolute',
        left: 72,
        top: 196,
        opacity: visible,
        transform: `translateY(${(1 - enter) * 42 - (1 - exit) * 28}px) scale(${0.96 + enter * 0.04})`,
      }}
    >
      <div style={{fontFamily: theme.fonts.mono, fontSize: 25, letterSpacing: 5, color: theme.colors.primary}}>
        {eyebrow}
      </div>
      <div
        style={{
          marginTop: 10,
          fontFamily: theme.fonts.display,
          fontWeight: 800,
          fontSize: 70,
          letterSpacing: '-0.04em',
          lineHeight: 1.05,
          color: theme.colors.text,
          textShadow: '0 3px 24px rgba(0,0,0,.82)',
        }}
      >
        {title}
      </div>
    </div>
  );
};

type DimensionProps = {
  duration: number;
  x1: number;
  y1: number;
  x2: number;
  y2: number;
  label: string;
  delay?: number;
  labelX?: number;
  labelY?: number;
};

const DimensionLine: React.FC<DimensionProps> = ({duration, x1, y1, x2, y2, label, delay = 8, labelX, labelY}) => {
  const {enter, exit, visible} = useMotion(duration, delay);
  const length = Math.hypot(x2 - x1, y2 - y1);
  return (
    <svg style={{position: 'absolute', inset: 0, width: '100%', height: '100%', opacity: visible}} viewBox="0 0 1080 1920">
      <defs>
        <marker id="dimension-arrow" markerWidth="7" markerHeight="7" refX="3.5" refY="3.5" orient="auto-start-reverse">
          <path d="M 0.5 3.5 L 6.5 0.5 L 5 3.5 L 6.5 6.5 Z" fill={theme.colors.primary} />
        </marker>
      </defs>
      <line x1={x1} y1={y1} x2={x2} y2={y2} stroke="rgba(255,249,239,.45)" strokeWidth="2" strokeDasharray="7 11" />
      <line
        x1={x1}
        y1={y1}
        x2={x2}
        y2={y2}
        stroke={theme.colors.primary}
        strokeWidth="5"
        strokeLinecap="round"
        markerStart="url(#dimension-arrow)"
        markerEnd="url(#dimension-arrow)"
        pathLength="1"
        strokeDasharray="1"
        strokeDashoffset={1 - enter}
        style={{filter: `drop-shadow(0 0 12px ${theme.colors.glow})`}}
      />
      <g transform={`translate(${labelX ?? (x1 + x2) / 2}, ${labelY ?? (y1 + y2) / 2}) scale(${0.88 + enter * 0.12})`}>
        <rect x="-108" y="-29" width="216" height="58" rx="12" fill="rgba(12,9,6,.86)" stroke="rgba(244,233,218,.28)" />
        <text textAnchor="middle" dominantBaseline="central" fill={theme.colors.text} fontFamily={theme.fonts.display} fontSize="31" fontWeight="700">
          {label}
        </text>
      </g>
      <text x="83" y="1810" fill="rgba(244,233,218,.58)" fontFamily={theme.fonts.mono} fontSize="20" letterSpacing="3">
        TECHNICAL RECONSTRUCTION · NOT TO SCALE
      </text>
    </svg>
  );
};

const MetricCard: React.FC<{
  duration: number;
  value: string;
  caption: string;
  x: number;
  y: number;
  delay?: number;
  width?: number;
}> = ({duration, value, caption, x, y, delay = 10, width = 360}) => {
  const {enter, exit, visible} = useMotion(duration, delay);
  const breathe = 1 + Math.sin(useCurrentFrame() / 24) * 0.008;
  return (
    <div
      style={{
        ...glass,
        position: 'absolute',
        left: x,
        top: y,
        width,
        padding: '25px 30px 28px',
        borderRadius: 24,
        opacity: visible,
        transform: `translateY(${(1 - enter) * 54 - (1 - exit) * 34}px) scale(${(0.94 + enter * 0.06) * breathe})`,
      }}
    >
      <div style={{fontFamily: theme.fonts.display, fontSize: 66, fontWeight: 800, letterSpacing: '-0.045em', color: theme.colors.primary}}>
        {value}
      </div>
      <div style={{marginTop: 7, fontFamily: theme.fonts.body, fontSize: 27, color: theme.colors.textDim, letterSpacing: '-0.02em'}}>
        {caption}
      </div>
    </div>
  );
};

const PathOverlay: React.FC<{duration: number}> = ({duration}) => {
  const {enter, exit, visible} = useMotion(duration, 8);
  const points = '155,895 360,895 475,760 680,760 815,565 910,565';
  const labels: Array<[number, number, string]> = [
    [155, 895, '바닥 감지선'],
    [475, 760, '벽면 통로'],
    [910, 565, '방아쇠'],
  ];
  return (
    <svg viewBox="0 0 1080 1920" style={{position: 'absolute', inset: 0, width: '100%', height: '100%', opacity: visible}}>
      <polyline points={points} fill="none" stroke="rgba(12,9,6,.9)" strokeWidth="15" strokeLinecap="round" strokeLinejoin="round" />
      <polyline
        points={points}
        fill="none"
        stroke={theme.colors.primary}
        strokeWidth="6"
        strokeLinecap="round"
        strokeLinejoin="round"
        pathLength="1"
        strokeDasharray="1"
        strokeDashoffset={1 - enter}
        style={{filter: `drop-shadow(0 0 14px ${theme.colors.glow})`}}
      />
      {labels.map(([x, y, text], index) => {
        const p = Math.max(0, Math.min(1, (enter * 1.35) - index * 0.18));
        return (
          <g key={String(text)} opacity={p} transform={`translate(${x},${y - 30})`}>
            <circle r="11" fill={theme.colors.primary} />
            <rect x="18" y="-27" width={String(text).length * 31 + 42} height="54" rx="11" fill="rgba(12,9,6,.86)" />
            <text x="39" y="8" fill={theme.colors.text} fontFamily={theme.fonts.body} fontSize="27" fontWeight="700">{text}</text>
          </g>
        );
      })}
    </svg>
  );
};

const ExplodedOverlay: React.FC<{duration: number}> = ({duration}) => {
  const {frame, exit} = useMotion(duration, 0);
  const labels = [
    {n: '01', name: '걸쇠', x: 155, y: 455},
    {n: '03', name: '지렛대', x: 155, y: 850},
    {n: '02', name: '방아쇠', x: 695, y: 1250, targetX: 770, targetY: 1155},
  ];
  return (
    <>
      <Header eyebrow="TRIGGER · EXPLODED" title="부품은 단 3개" duration={duration} />
      <svg viewBox="0 0 1080 1920" style={{position: 'absolute', inset: 0, width: '100%', height: '100%', opacity: exit}}>
        <line x1="540" y1="410" x2="540" y2="1010" stroke="rgba(244,233,218,.42)" strokeWidth="3" strokeDasharray="10 14" />
        {labels.map((item, i) => {
          const p = spring({frame: frame - 15 - i * 7, fps: 30, config: theme.spring.snappy});
          const tx = (1 - p) * (i % 2 === 0 ? -70 : 70);
          const targetX = 'targetX' in item ? item.targetX : 540;
          const targetY = 'targetY' in item ? item.targetY : item.y + 35;
          const lineStartX = item.x > 540 ? item.x : item.x + 210;
          return (
            <g key={item.n} opacity={p} transform={`translate(${tx},0)`}>
              <line x1={lineStartX} y1={item.y + 35} x2={targetX} y2={targetY} stroke={theme.colors.primary} strokeWidth="4" />
              <circle cx={targetX} cy={targetY} r="9" fill={theme.colors.primary} />
              <rect x={item.x} y={item.y} width="210" height="70" rx="17" fill="rgba(12,9,6,.86)" stroke="rgba(244,233,218,.28)" />
              <text x={item.x + 25} y={item.y + 45} fill={theme.colors.primary} fontFamily={theme.fonts.mono} fontSize="24" fontWeight="700">{item.n}</text>
              <text x={item.x + 75} y={item.y + 47} fill={theme.colors.text} fontFamily={theme.fonts.display} fontSize="34" fontWeight="700">{item.name}</text>
            </g>
          );
        })}
      </svg>
    </>
  );
};

const ForceOverlay: React.FC<{duration: number; release?: boolean}> = ({duration, release = false}) => {
  const {frame, enter, exit, visible} = useMotion(duration, 5);
  const pulse = 1 + Math.sin(frame / 7) * 0.035;
  const arrowEnd = release ? 965 : 820;
  return (
    <>
      <Header eyebrow={release ? 'ENERGY RELEASE' : 'LOAD PATH'} title={release ? '저장된 힘 → 화살' : '200 kg 장력'} duration={duration} />
      <svg viewBox="0 0 1080 1920" style={{position: 'absolute', inset: 0, width: '100%', height: '100%', opacity: visible}}>
        <defs>
          <marker id={release ? 'force-release' : 'force-load'} markerWidth="18" markerHeight="18" refX="12" refY="6" orient="auto">
            <path d="M0,0 L12,6 L0,12 Z" fill={theme.colors.primary} />
          </marker>
        </defs>
        <path
          d={release ? `M145 805 C390 690 650 705 ${arrowEnd} 610` : `M155 790 C350 700 590 720 ${arrowEnd} 585`}
          fill="none"
          stroke="rgba(12,9,6,.9)"
          strokeWidth="22"
          strokeLinecap="round"
        />
        <path
          d={release ? `M145 805 C390 690 650 705 ${arrowEnd} 610` : `M155 790 C350 700 590 720 ${arrowEnd} 585`}
          fill="none"
          stroke={theme.colors.primary}
          strokeWidth={release ? 11 : 8}
          strokeLinecap="round"
          markerEnd={`url(#${release ? 'force-release' : 'force-load'})`}
          pathLength="1"
          strokeDasharray="1"
          strokeDashoffset={1 - enter}
          style={{filter: `drop-shadow(0 0 18px ${theme.colors.glow})`, transform: `scale(${pulse})`, transformOrigin: '540px 700px'}}
        />
      </svg>
      <div style={{position: 'absolute', left: 74, top: 1040, opacity: exit, color: theme.colors.textDim, fontFamily: theme.fonts.mono, fontSize: 22, letterSpacing: 3}}>
        {release ? 'POTENTIAL → KINETIC' : 'STRING → CATCH → LEVER'}
      </div>
    </>
  );
};

const MercuryOverlay: React.FC<{duration: number}> = ({duration}) => {
  const {frame, enter, exit, visible} = useMotion(duration, 6);
  const mistY = 850 - enter * 150 + Math.sin(frame / 18) * 10;
  return (
    <>
      <Header eyebrow="SECOND DEFENCE LAYER" title="수은 증기층" duration={duration} />
      <svg viewBox="0 0 1080 1920" style={{position: 'absolute', inset: 0, width: '100%', height: '100%', opacity: visible}}>
        {[0, 1, 2].map((i) => (
          <path
            key={i}
            d={`M60 ${mistY + i * 66} C260 ${mistY - 30 + i * 66}, 410 ${mistY + 36 + i * 66}, 610 ${mistY + i * 66} S900 ${mistY - 22 + i * 66}, 1030 ${mistY + i * 66}`}
            fill="none"
            stroke={i === 1 ? theme.colors.primary : 'rgba(244,233,218,.48)'}
            strokeWidth={i === 1 ? 6 : 3}
            strokeDasharray={i === 1 ? undefined : '9 14'}
          />
        ))}
        {Array.from({length: 9}).map((_, i) => {
          const y = 1050 - ((frame * (1.1 + (i % 3) * 0.18) + i * 71) % 470);
          const x = 120 + i * 105 + Math.sin((frame + i * 17) / 20) * 26;
          return <circle key={i} cx={x} cy={y} r={5 + (i % 3) * 2} fill="rgba(244,233,218,.5)" />;
        })}
      </svg>
      <MetricCard duration={duration} value="Hg" caption="기계가 놓치면 공기가 막는다" x={675} y={820} delay={18} width={330} />
      <div style={{position: 'absolute', inset: 0, opacity: (1 - exit) * 0.14, background: theme.colors.primary, mixBlendMode: 'screen'}} />
    </>
  );
};

const LayerOverlay: React.FC<{duration: number}> = ({duration}) => {
  const frame = useCurrentFrame();
  const {exit} = useMotion(duration, 0);
  const layers = [
    {n: '01', label: '기계식 석궁', y: 470},
    {n: '02', label: '수은 증기', y: 630},
    {n: '03', label: '봉쇄 구조', y: 790},
  ];
  return (
    <>
      <Header eyebrow="DEFENCE SYSTEM" title="3중 방어 구조" duration={duration} />
      {layers.map((layer, i) => {
        const p = spring({frame: frame - 12 - i * 8, fps: 30, config: theme.spring.smooth});
        return (
          <div
            key={layer.n}
            style={{
              ...glass,
              position: 'absolute',
              left: 92 + i * 34,
              top: layer.y,
              width: 680,
              height: 112,
              borderRadius: 22,
              opacity: p * exit,
              transform: `translateX(${(1 - p) * 100}px) scale(${0.96 + p * 0.04})`,
              display: 'flex',
              alignItems: 'center',
              gap: 28,
              padding: '0 34px',
            }}
          >
            <div style={{fontFamily: theme.fonts.mono, fontSize: 30, color: theme.colors.primary, fontWeight: 800}}>{layer.n}</div>
            <div style={{height: 44, width: 2, background: 'rgba(244,233,218,.24)'}} />
            <div style={{fontFamily: theme.fonts.display, fontSize: 39, color: theme.colors.text, fontWeight: 700}}>{layer.label}</div>
          </div>
        );
      })}
    </>
  );
};

const ScanOverlay: React.FC<{duration: number}> = ({duration}) => {
  const {frame, exit} = useMotion(duration, 0);
  const sweep = interpolate(frame, [4, duration - 12], [260, 1130], {...clamp, easing: theme.ease.inOut});
  return (
    <>
      <Header eyebrow="NON-INVASIVE SURVEY" title="발굴하지 않고 관측한다" duration={duration} />
      <div
        style={{
          position: 'absolute', left: 90, right: 90, top: sweep, height: 4,
          opacity: exit,
          background: theme.colors.primary,
          boxShadow: `0 0 45px 16px ${theme.colors.glow}`,
        }}
      />
      <div style={{...glass, position: 'absolute', left: 90, top: 930, width: 470, borderRadius: 20, padding: '24px 28px', opacity: exit}}>
        <div style={{fontFamily: theme.fonts.mono, fontSize: 22, color: theme.colors.primary, letterSpacing: 3}}>CENTRAL CORE</div>
        <div style={{fontFamily: theme.fonts.display, fontSize: 43, color: theme.colors.text, fontWeight: 800, marginTop: 8}}>미발굴 중심부</div>
      </div>
    </>
  );
};

const SceneOverlay: React.FC<{seq: number; duration: number}> = ({seq, duration}) => {
  if (seq === 1) return <><Header eyebrow="MAUSOLEUM SCALE" title="봉토 외형" duration={duration} /><DimensionLine duration={duration} x1={155} y1={790} x2={925} y2={790} label="약 350 m" labelY={740} /><DimensionLine duration={duration} x1={880} y1={360} x2={880} y2={770} label="높이 약 50 m" delay={16} labelX={760} /></>;
  if (seq === 2) return <><Header eyebrow="CUTAWAY · DEPTH" title="도굴 흔적은 가장자리" duration={duration} /><DimensionLine duration={duration} x1={850} y1={350} x2={850} y2={930} label="중심부" delay={11} labelX={730} /><DimensionLine duration={duration} x1={160} y1={650} x2={565} y2={830} label="우회 갱도" delay={20} labelY={690} /></>;
  if (seq === 5) return <><Header eyebrow="CONSTRUCTION BEGINS" title="즉위와 동시에 착공" duration={duration} /><MetricCard duration={duration} value="기원전 246년" caption="진시황릉 조성 시작" x={90} y={440} width={520} /><DimensionLine duration={duration} x1={810} y1={500} x2={810} y2={980} label="지하 궁전" delay={20} labelX={690} /></>;
  if (seq === 6) return <><Header eyebrow="MEGAPROJECT" title="수도 하나의 규모" duration={duration} /><MetricCard duration={duration} value="38년" caption="공사 기간" x={88} y={480} /><MetricCard duration={duration} value="700,000명" caption="동원된 인력" x={590} y={710} delay={19} width={400} /></>;
  if (seq === 12) return <><Header eyebrow="PORTCULLIS" title="수 톤짜리 낙하식 돌문" duration={duration} /><DimensionLine duration={duration} x1={790} y1={350} x2={790} y2={970} label="낙하 방향" delay={8} labelX={670} /><MetricCard duration={duration} value="수 톤" caption="중력으로 통로 봉쇄" x={92} y={810} delay={18} /></>;
  if (seq === 18) return <ExplodedOverlay duration={duration} />;
  if (seq === 19) return <ForceOverlay duration={duration} />;
  if (seq === 20) return <><Header eyebrow="TRIP CORD PATH" title="바닥에서 방아쇠까지" duration={duration} /><PathOverlay duration={duration} /></>;
  if (seq === 21) return <ForceOverlay duration={duration} release />;
  if (seq === 22) return <MercuryOverlay duration={duration} />;
  if (seq === 23) return <LayerOverlay duration={duration} />;
  if (seq === 24) return <ScanOverlay duration={duration} />;
  if (seq === 25) return <><Header eyebrow="UNEXCAVATED CORE" title="진시황릉의 비밀" duration={duration} /><DimensionLine duration={duration} x1={175} y1={825} x2={905} y2={825} label="2,000년의 봉인" delay={13} labelY={770} /></>;
  return null;
};

const BgMesh: React.FC = () => {
  const frame = useCurrentFrame();
  const driftA = Math.sin(frame / 55) * 44;
  const driftB = Math.cos(frame / 70) * 38;
  return (
    <AbsoluteFill style={{background: theme.colors.bg}}>
      <div style={{position: 'absolute', width: 1200, height: 1200, borderRadius: '50%', top: -480, left: -380 + driftA, filter: 'blur(54px)', background: `radial-gradient(circle, ${theme.colors.primary}30, transparent 64%)`}} />
      <div style={{position: 'absolute', width: 980, height: 980, borderRadius: '50%', bottom: -410, right: -330 - driftB, filter: 'blur(72px)', background: 'radial-gradient(circle, rgba(98,76,51,.20), transparent 66%)'}} />
    </AbsoluteFill>
  );
};

const Grade: React.FC = () => (
  <AbsoluteFill style={{pointerEvents: 'none'}}>
    <AbsoluteFill style={{backgroundColor: '#8A5520', mixBlendMode: 'soft-light', opacity: 0.16}} />
    <AbsoluteFill style={{background: 'linear-gradient(180deg, rgba(0,0,0,.15), transparent 25%, transparent 72%, rgba(0,0,0,.24))'}} />
  </AbsoluteFill>
);

const Grain: React.FC = () => {
  const frame = useCurrentFrame();
  const noise = `url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='220' height='220'%3E%3Cfilter id='n'%3E%3CfeTurbulence type='fractalNoise' baseFrequency='.9' numOctaves='2'/%3E%3C/filter%3E%3Crect width='220' height='220' filter='url(%23n)' opacity='.5'/%3E%3C/svg%3E")`;
  return <AbsoluteFill style={{pointerEvents: 'none', backgroundImage: noise, backgroundSize: '220px', backgroundPosition: `${(frame * 7) % 220}px ${(frame * 13) % 220}px`, opacity: 0.045, mixBlendMode: 'overlay'}} />;
};

const Vignette: React.FC = () => (
  <AbsoluteFill style={{pointerEvents: 'none', background: 'radial-gradient(ellipse at center, transparent 54%, rgba(0,0,0,.30) 100%)'}} />
);

export const AncientArtifactFilm: React.FC = () => (
  <AbsoluteFill style={{background: theme.colors.bg, overflow: 'hidden'}}>
    <style>{`
      @font-face { font-family: 'Gmarket Sans'; src: url('${staticFile('fonts/GmarketSansBold.otf')}'); font-weight: 700 900; }
      @font-face { font-family: 'Noto Sans KR'; src: url('${staticFile('fonts/NotoSansKR-VF.ttf')}'); font-weight: 100 900; }
    `}</style>
    <BgMesh />
    <AbsoluteFill style={{overflow: 'hidden'}}>
      <OffthreadVideo src={staticFile('base.mp4')} style={{width: '100%', height: '100%', objectFit: 'cover'}} />
    </AbsoluteFill>
    {sceneTimings.map((scene) => (
      <Sequence key={scene.seq} from={scene.startFrame} durationInFrames={scene.durationFrames} premountFor={30}>
        <SceneOverlay seq={scene.seq} duration={scene.durationFrames} />
      </Sequence>
    ))}
    <Grade />
    <Grain />
    <Vignette />
  </AbsoluteFill>
);
