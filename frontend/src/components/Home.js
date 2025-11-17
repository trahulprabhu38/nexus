import React from 'react';
import { Canvas } from '@react-three/fiber';
import { OrbitControls, Stars, Text } from '@react-three/drei';
import { useNavigate } from 'react-router-dom';



function Home() {
  const navigate = useNavigate();

  return (
    <div style={{ height: '100vh', background: 'linear-gradient(to bottom, #000000, #1a1a2e)', position: 'relative' }}>
      <Canvas style={{ height: '100%' }}>
        <ambientLight intensity={0.5} />
        <pointLight position={[10, 10, 10]} />
        <Stars radius={300} depth={60} count={20000} factor={7} saturation={0} fade />
        <OrbitControls enableZoom={true} enablePan={false} />
        <Text
          fontSize={0.8}
          color="white"
          anchorX="center"
          anchorY="middle"
          position={[0, 0, 0]}
        >
          AIML NEXUS
        </Text>
      </Canvas>
      <div style={{
        position: 'absolute',
        top: '10px',
        left: '10px',
        zIndex: 1
      }}>
        <img src="/logo1.png" alt="Dayananda Sagar College Logo" style={{ width: '85px' }} />
      </div>
      <div style={{
        position: 'absolute',
        top: '10px',
        right: '10px',
        zIndex: 1
      }}>
        <img src="/logo2.png" alt="Tech Team Logo" style={{ width: '120px' }} />
      </div>
      <div style={{
        position: 'absolute',
        bottom: '20%',
        left: '50%',
        transform: 'translateX(-50%)',
        zIndex: 1
      }}>
        <button
          onClick={() => navigate('/login')}
          style={{
            padding: '15px 30px',
            fontSize: '1.2rem',
            backgroundColor: '#4CAF50',
            color: 'white',
            border: 'none',
            borderRadius: '5px',
            cursor: 'pointer',
            transition: 'background-color 0.3s'
          }}
          onMouseOver={(e) => e.target.style.backgroundColor = '#45a049'}
          onMouseOut={(e) => e.target.style.backgroundColor = '#4CAF50'}
        >
          Start
        </button>
      </div>
    </div>
  );
}

export default Home;
