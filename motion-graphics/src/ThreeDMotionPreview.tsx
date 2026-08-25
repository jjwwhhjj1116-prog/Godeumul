import {ThreeCanvas} from '@remotion/three';
import {useThree} from '@react-three/fiber';
import React, {useLayoutEffect, useMemo} from 'react';
import {
  AbsoluteFill,
  Audio,
  interpolate,
  spring,
  staticFile,
  useCurrentFrame,
  useVideoConfig,
} from 'remotion';
import * as THREE from 'three';
import {theme} from './theme';

const clamp = {
  extrapolateLeft: 'clamp' as const,
  extrapolateRight: 'clamp' as const,
};

const airflowCurve = new THREE.CatmullRomCurve3(
  [
    new THREE.Vector3(-0.9, -2.15, 5.2),
    new THREE.Vector3(-1.15, -1.55, 3.3),
    new THREE.Vector3(-1.15, -0.65, 1.15),
    new THREE.Vector3(-0.2, 0.08, -1.2),
    new THREE.Vector3(0.85, 0.65, -3.9),
    new THREE.Vector3(1.55, 1.08, -6.6),
    new THREE.Vector3(2.05, 1.52, -9.85),
  ],
  false,
  'catmullrom',
  0.45,
);

const makeHelixCurve = (phase: number) => {
  const points = Array.from({length: 36}).map((_, index) => {
    const t = index / 35;
    const point = airflowCurve.getPointAt(t);
    const tangent = airflowCurve.getTangentAt(t).normalize();
    const lateral = new THREE.Vector3(0, 1, 0).cross(tangent).normalize();
    const vertical = tangent.clone().cross(lateral).normalize();
    const angle = t * Math.PI * 5 + phase;
    return point
      .add(lateral.multiplyScalar(Math.cos(angle) * 0.09))
      .add(vertical.multiplyScalar(Math.sin(angle) * 0.09));
  });
  return new THREE.CatmullRomCurve3(points, false, 'catmullrom', 0.42);
};

const airflowHelices = [makeHelixCurve(0), makeHelixCurve(Math.PI)];

const stoneColors = ['#493927', '#59452e', '#3c2e20', '#665039'];

const getCameraState = (frame: number, durationInFrames: number) => {
  const progress = interpolate(frame, [0, durationInFrames], [0, 1], {
    ...clamp,
    easing: theme.ease.inOut,
  });
  const revealNudge = interpolate(frame, [54, 130], [0, 1], {
    ...clamp,
    easing: theme.ease.out,
  });
  return {
    position: new THREE.Vector3(
      -1.8 + progress * 0.68,
      0.7 + Math.sin(progress * Math.PI) * 0.22,
      8.9 - progress * 1.85,
    ),
    target: new THREE.Vector3(
      0.42 + revealNudge * 0.34,
      -0.16 + revealNudge * 0.25,
      -3.0 - progress * 1.3,
    ),
    fov: interpolate(progress, [0, 1], [30, 24], {
      ...clamp,
      easing: theme.ease.inOut,
    }),
    roll: interpolate(progress, [0, 1], [-0.012, 0.009], {
      ...clamp,
      easing: theme.ease.inOut,
    }),
  };
};

const CameraRig: React.FC = () => {
  const frame = useCurrentFrame();
  const {durationInFrames} = useVideoConfig();
  const camera = useThree((state) => state.camera);
  const cameraState = getCameraState(frame, durationInFrames);

  useLayoutEffect(() => {
    camera.position.copy(cameraState.position);
    camera.lookAt(cameraState.target);
    camera.rotateZ(cameraState.roll);

    if (camera instanceof THREE.PerspectiveCamera) {
      camera.fov = cameraState.fov;
      camera.updateProjectionMatrix();
    }
    camera.updateMatrixWorld();
  }, [camera, cameraState.fov, cameraState.position, cameraState.roll, cameraState.target]);

  return null;
};

const RenderSettings: React.FC = () => {
  const gl = useThree((state) => state.gl);
  useLayoutEffect(() => {
    gl.toneMapping = THREE.ACESFilmicToneMapping;
    gl.toneMappingExposure = 1.42;
  }, [gl]);
  return null;
};

const Block: React.FC<{
  position: [number, number, number];
  size: [number, number, number];
  color?: string;
  rotation?: [number, number, number];
}> = ({position, size, color = '#4d3b29', rotation = [0, 0, 0]}) => (
  <mesh position={position} rotation={rotation} castShadow receiveShadow>
    <boxGeometry args={size} />
    <meshStandardMaterial color={color} roughness={0.92} metalness={0.02} />
  </mesh>
);

const StoneCourses: React.FC = () => {
  const blocks = useMemo(() => {
    return Array.from({length: 18}).flatMap((_, row) => {
      const y = -2.55 + row * 0.32;
      const offset = row % 2 === 0 ? 0 : 0.34;
      return Array.from({length: 10}).map((__, column) => ({
        key: `${row}-${column}`,
        x: -3.0 + column * 0.67 + offset,
        y,
        color: stoneColors[(row * 3 + column) % stoneColors.length],
        depth: 0.2 + ((row + column) % 3) * 0.025,
      }));
    });
  }, []);

  return (
    <group position={[0, 0, -10.62]}>
      {blocks.map((block) => (
        <Block
          key={block.key}
          position={[block.x, block.y, 0]}
          size={[0.62, 0.27, block.depth]}
          color={block.color}
        />
      ))}
    </group>
  );
};

const ChamberArchitecture: React.FC = () => {
  const frame = useCurrentFrame();
  const {fps} = useVideoConfig();
  const lightRise = spring({
    frame: frame - Math.round(fps * 0.42),
    fps,
    config: theme.spring.smooth,
  });
  const ventPulse = 0.78 + Math.sin(frame / 8.5) * 0.08 + Math.sin(frame / 21) * 0.06;

  return (
    <>
      <fog attach="fog" args={['#080604', 12, 31]} />
      <ambientLight intensity={0.46} />
      <hemisphereLight args={['#9aaec0', '#241109', 0.9]} />
      <directionalLight
        castShadow
        color="#f0c47f"
        intensity={4.1 * lightRise}
        position={[-4.6, 7.5, 5.5]}
        shadow-mapSize-width={1024}
        shadow-mapSize-height={1024}
        shadow-camera-far={30}
      />
      <pointLight
        color="#e8a33d"
        intensity={13 * ventPulse * lightRise}
        distance={9}
        decay={2}
        position={[2.05, 1.52, -9.25]}
      />
      <pointLight
        color="#ba6d2e"
        intensity={5.5 * lightRise}
        distance={10}
        decay={2}
        position={[-2.2, -1.6, 3.8]}
      />

      <Block position={[0, -3.0, -2.0]} size={[7.6, 0.42, 18.5]} color="#302418" />
      <Block position={[0, 3.05, -2.0]} size={[7.6, 0.34, 18.5]} color="#2b2117" />
      <Block position={[-3.62, 0, -2.0]} size={[0.58, 6.35, 18.5]} color="#493725" />
      <Block position={[3.62, 0, -2.0]} size={[0.58, 6.35, 18.5]} color="#3f3021" />
      <Block position={[0, 0, -10.88]} size={[7.55, 6.25, 0.38]} color="#493725" />
      <StoneCourses />

      <Block position={[-2.67, -0.05, 1.75]} size={[0.92, 5.75, 1.2]} color="#5a432b" />
      <Block position={[2.72, -0.05, 1.2]} size={[0.96, 5.75, 1.35]} color="#4a3624" />
      <Block position={[-2.5, -0.1, -4.15]} size={[0.78, 5.65, 0.92]} color="#443121" />
      <Block position={[2.85, -0.15, -4.8]} size={[0.72, 5.55, 0.9]} color="#3d2d20" />

      <mesh position={[2.05, 1.52, -10.38]} rotation={[Math.PI / 2, 0, 0]} castShadow receiveShadow>
        <cylinderGeometry args={[0.78, 0.78, 0.72, 48]} />
        <meshStandardMaterial color="#2a211a" roughness={0.8} metalness={0.06} />
      </mesh>
      <mesh position={[2.05, 1.52, -9.99]} castShadow>
        <torusGeometry args={[0.63, 0.15, 22, 56]} />
        <meshStandardMaterial color="#8b6c3e" roughness={0.66} metalness={0.18} />
      </mesh>
      <mesh position={[2.05, 1.52, -9.96]}>
        <circleGeometry args={[0.54, 48]} />
        <meshStandardMaterial color="#1b1108" emissive="#e8a33d" emissiveIntensity={0.28 * ventPulse} />
      </mesh>

      {Array.from({length: 8}).map((_, index) => (
        <Block
          key={index}
          position={[-3.25 + index * 0.92, -2.73, -0.5 - index * 0.7]}
          size={[0.8, 0.12, 1.45]}
          color={stoneColors[index % stoneColors.length]}
          rotation={[0, 0.03 * ((index % 3) - 1), 0]}
        />
      ))}
    </>
  );
};

const AirflowPulse: React.FC<{index: number}> = ({index}) => {
  const frame = useCurrentFrame();
  const {fps, durationInFrames} = useVideoConfig();
  const delay = Math.round(fps * 0.48) + index * Math.round(fps * 0.12);
  const localFrame = frame - delay;
  const travelFrames = Math.round(fps * 2.05);
  const rawProgress = ((Math.max(0, localFrame) + index * 9) % travelFrames) / travelFrames;
  const progress = theme.ease.inOut(rawProgress);
  const point = airflowCurve.getPointAt(progress);
  const tangent = airflowCurve.getTangentAt(progress).normalize();
  const lateral = new THREE.Vector3(0, 1, 0).cross(tangent).normalize();
  point.add(lateral.multiplyScalar(((index % 3) - 1) * 0.07));
  const quaternion = new THREE.Quaternion().setFromUnitVectors(
    new THREE.Vector3(0, 1, 0),
    tangent,
  );
  const enter = spring({
    frame: Math.max(0, localFrame),
    fps,
    config: theme.spring.snappy,
  });
  const exit = interpolate(frame, [durationInFrames - 15, durationInFrames], [1, 0], {
    ...clamp,
    easing: theme.ease.in,
  });
  const shimmer = 0.72 + Math.sin(frame / 4 + index * 1.7) * 0.18;
  const opacity = (localFrame < 0 ? 0 : enter) * exit * shimmer;

  return (
    <group position={point} quaternion={quaternion} scale={0.56 + enter * 0.16}>
      <mesh position={[0, -0.12, 0]} castShadow>
        <cylinderGeometry args={[0.03, 0.06, 0.28, 10]} />
        <meshStandardMaterial
          color="#ffd98c"
          emissive="#e8a33d"
          emissiveIntensity={3.8}
          transparent
          opacity={opacity}
          depthWrite={false}
          blending={THREE.AdditiveBlending}
        />
      </mesh>
      <mesh position={[0, 0.14, 0]} castShadow>
        <coneGeometry args={[0.085, 0.21, 12]} />
        <meshStandardMaterial
          color="#fff0bf"
          emissive="#e8a33d"
          emissiveIntensity={4.4}
          transparent
          opacity={opacity}
          depthWrite={false}
          blending={THREE.AdditiveBlending}
        />
      </mesh>
    </group>
  );
};

const AirMotes: React.FC = () => {
  const frame = useCurrentFrame();
  const {fps} = useVideoConfig();
  return (
    <group>
      {Array.from({length: 22}).map((_, index) => {
        const cycle = Math.round(fps * (2.3 + (index % 5) * 0.18));
        const progress = ((frame + index * 13) % cycle) / cycle;
        const t = theme.ease.inOut(progress);
        const point = airflowCurve.getPointAt(t);
        const tangent = airflowCurve.getTangentAt(t).normalize();
        const lateral = new THREE.Vector3(0, 1, 0).cross(tangent).normalize();
        point.add(lateral.multiplyScalar(Math.sin(index * 2.11) * (0.12 + (index % 4) * 0.045)));
        point.y += Math.cos(index * 1.37 + frame / 19) * 0.08;
        const opacity = Math.sin(progress * Math.PI) * 0.48;
        return (
          <mesh key={index} position={point} scale={0.018 + (index % 3) * 0.006}>
            <sphereGeometry args={[1, 8, 8]} />
            <meshBasicMaterial color="#ffe7ae" transparent opacity={opacity} depthWrite={false} />
          </mesh>
        );
      })}
    </group>
  );
};

const AirflowVolume: React.FC = () => {
  const frame = useCurrentFrame();
  const {fps, durationInFrames} = useVideoConfig();
  const enter = spring({
    frame: frame - Math.round(fps * 0.25),
    fps,
    config: theme.spring.smooth,
  });
  const exit = interpolate(frame, [durationInFrames - 15, durationInFrames], [1, 0], {
    ...clamp,
    easing: theme.ease.in,
  });

  return (
    <group>
      <mesh>
        <tubeGeometry args={[airflowCurve, 128, 0.095, 12, false]} />
        <meshStandardMaterial
          color="#e8a33d"
          emissive="#e8a33d"
          emissiveIntensity={1.8}
          transparent
          opacity={0.09 * enter * exit}
          depthWrite={false}
          blending={THREE.AdditiveBlending}
        />
      </mesh>
      <mesh>
        <tubeGeometry args={[airflowCurve, 128, 0.024, 10, false]} />
        <meshStandardMaterial
          color="#ffe2a0"
          emissive="#e8a33d"
          emissiveIntensity={3.2}
          transparent
          opacity={0.48 * enter * exit}
          depthWrite={false}
          blending={THREE.AdditiveBlending}
        />
      </mesh>
      {airflowHelices.map((curve, index) => (
        <mesh key={index}>
          <tubeGeometry args={[curve, 112, 0.013, 8, false]} />
          <meshBasicMaterial
            color={index === 0 ? '#ffd17b' : '#f4e9da'}
            transparent
            opacity={0.2 * enter * exit}
            depthWrite={false}
            blending={THREE.AdditiveBlending}
          />
        </mesh>
      ))}
      {Array.from({length: 9}).map((_, index) => (
        <AirflowPulse key={index} index={index} />
      ))}
      <AirMotes />
    </group>
  );
};

const CylinderBetween: React.FC<{
  start: THREE.Vector3;
  end: THREE.Vector3;
  radius?: number;
  opacity: number;
}> = ({start, end, radius = 0.018, opacity}) => {
  const midpoint = start.clone().add(end).multiplyScalar(0.5);
  const direction = end.clone().sub(start);
  const length = direction.length();
  const quaternion = new THREE.Quaternion().setFromUnitVectors(
    new THREE.Vector3(0, 1, 0),
    direction.normalize(),
  );
  return (
    <mesh position={midpoint} quaternion={quaternion}>
      <cylinderGeometry args={[radius, radius, length, 10]} />
      <meshStandardMaterial
        color="#f4e9da"
        emissive="#e8a33d"
        emissiveIntensity={1.4}
        transparent
        opacity={opacity}
        depthWrite={false}
      />
    </mesh>
  );
};

const DimensionGeometry: React.FC = () => {
  const frame = useCurrentFrame();
  const {fps, durationInFrames} = useVideoConfig();
  const startFrame = Math.round(fps * 3.32);
  const reveal = spring({frame: frame - startFrame, fps, config: theme.spring.snappy});
  const tickReveal = spring({
    frame: frame - startFrame - Math.round(fps * 0.12),
    fps,
    config: theme.spring.smooth,
  });
  const exit = interpolate(frame, [durationInFrames - 14, durationInFrames - 3], [1, 0], {
    ...clamp,
    easing: theme.ease.in,
  });
  const start = new THREE.Vector3(1.34, 0.57, -9.72);
  const target = new THREE.Vector3(2.76, 0.57, -9.72);
  const currentEnd = start.clone().lerp(target, reveal);
  const opacity = interpolate(reveal, [0, 1], [0, 0.9], {
    ...clamp,
    easing: theme.ease.out,
  });

  return (
    <group>
      <CylinderBetween start={start} end={currentEnd} opacity={opacity * exit} />
      <CylinderBetween
        start={new THREE.Vector3(1.34, 0.38, -9.72)}
        end={new THREE.Vector3(1.34, 0.76, -9.72)}
        opacity={tickReveal * exit * 0.9}
      />
      <CylinderBetween
        start={new THREE.Vector3(2.76, 0.38, -9.72)}
        end={new THREE.Vector3(2.76, 0.76, -9.72)}
        opacity={tickReveal * exit * 0.9}
      />
      <mesh position={[1.42, 0.57, -9.72]} rotation={[0, 0, -Math.PI / 2]} scale={tickReveal * exit}>
        <coneGeometry args={[0.06, 0.16, 10]} />
        <meshStandardMaterial color="#f4e9da" emissive="#e8a33d" emissiveIntensity={1.3} />
      </mesh>
      <mesh position={[2.68, 0.57, -9.72]} rotation={[0, 0, Math.PI / 2]} scale={tickReveal * exit}>
        <coneGeometry args={[0.06, 0.16, 10]} />
        <meshStandardMaterial color="#f4e9da" emissive="#e8a33d" emissiveIntensity={1.3} />
      </mesh>
    </group>
  );
};

const DimensionReadout: React.FC = () => {
  const frame = useCurrentFrame();
  const {fps, width, height, durationInFrames} = useVideoConfig();
  const start = Math.round(fps * 3.48);
  const enter = spring({frame: frame - start, fps, config: theme.spring.smooth});
  const exit = interpolate(frame, [durationInFrames - 14, durationInFrames - 3], [1, 0], {
    ...clamp,
    easing: theme.ease.in,
  });
  const cameraState = getCameraState(frame, durationInFrames);
  const projectionCamera = new THREE.PerspectiveCamera(
    cameraState.fov,
    width / height,
    0.1,
    80,
  );
  projectionCamera.position.copy(cameraState.position);
  projectionCamera.lookAt(cameraState.target);
  projectionCamera.rotateZ(cameraState.roll);
  projectionCamera.updateMatrixWorld();
  projectionCamera.updateProjectionMatrix();
  const projected = new THREE.Vector3(2.76, 0.76, -9.72).project(projectionCamera);
  const x = (projected.x * 0.5 + 0.5) * width + 14;
  const y = (-projected.y * 0.5 + 0.5) * height - 12;

  return (
    <div style={{
      position: 'absolute', left: x, top: y,
      opacity: enter * exit,
      transform: `translateY(${(1 - enter) * 12}px) scale(${0.96 + enter * 0.04})`,
      transformOrigin: 'left center',
      color: theme.colors.accent,
      fontFamily: theme.fonts.mono,
      fontSize: 28,
      fontWeight: 700,
      letterSpacing: '0.01em',
      textShadow: `0 0 18px ${theme.colors.glow}`,
    }}>
      0.8 m
    </div>
  );
};

const Grade: React.FC = () => (
  <AbsoluteFill style={{pointerEvents: 'none'}}>
    <AbsoluteFill style={{background: '#8a5520', mixBlendMode: 'soft-light', opacity: 0.13}} />
    <AbsoluteFill style={{background: 'linear-gradient(180deg, rgba(0,0,0,.18), transparent 28%, transparent 70%, rgba(0,0,0,.38))'}} />
  </AbsoluteFill>
);

const Grain: React.FC = () => {
  const frame = useCurrentFrame();
  const noise = `url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='220' height='220'%3E%3Cfilter id='n'%3E%3CfeTurbulence type='fractalNoise' baseFrequency='.86' numOctaves='2'/%3E%3C/filter%3E%3Crect width='220' height='220' filter='url(%23n)' opacity='.48'/%3E%3C/svg%3E")`;
  return <AbsoluteFill style={{pointerEvents: 'none', backgroundImage: noise, backgroundSize: 220,
    backgroundPosition: `${(frame * 7) % 220}px ${(frame * 13) % 220}px`, opacity: 0.04, mixBlendMode: 'overlay'}} />;
};

export const ThreeDMotionPreview: React.FC = () => {
  const {width, height} = useVideoConfig();
  return (
    <AbsoluteFill style={{background: theme.colors.bg, overflow: 'hidden'}}>
      <AbsoluteFill style={{background: 'radial-gradient(circle at 58% 29%, #2d2114 0%, #0c0906 52%, #050403 100%)'}} />
      <ThreeCanvas
        width={width}
        height={height}
        shadows
        dpr={1.25}
        camera={{position: [-1.8, 0.7, 8.9], fov: 30, near: 0.1, far: 80}}
        gl={{antialias: true, alpha: true, preserveDrawingBuffer: true}}
      >
        <RenderSettings />
        <CameraRig />
        <ChamberArchitecture />
        <AirflowVolume />
        <DimensionGeometry />
      </ThreeCanvas>
      <DimensionReadout />
      <Grade />
      <Grain />
      <AbsoluteFill style={{pointerEvents: 'none', background: 'radial-gradient(ellipse at center, transparent 48%, rgba(0,0,0,.48) 100%)'}} />
      <Audio src={staticFile('sfx/wind-bed.wav')} volume={0.24} />
    </AbsoluteFill>
  );
};
