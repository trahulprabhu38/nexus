import React from 'react';
import { useNavigate } from 'react-router-dom';

function Dashboard() {
  const navigate = useNavigate();

  const sections = [
    { name: 'Attendance', description: 'View your attendance records' },
    { name: 'Timetable', description: 'Check your class schedule' },
    { name: 'Results', description: 'View your academic results' },
    { name: 'Academic Details', description: 'Access your academic information' },
    { name: 'Fees Structure', description: 'Check fees and payment details' }
  ];

  const handleSectionClick = (section) => {
    navigate(`/dashboard/${section.toLowerCase().replace(' ', '-')}`);
  };

  return (
    <div style={{
      minHeight: '100vh',
      background: 'linear-gradient(to bottom, #16213e, #0f3460)',
      padding: '20px'
    }}>
      <h1 style={{
        color: 'white',
        textAlign: 'center',
        marginBottom: '40px',
        fontSize: '2.5rem'
      }}>
        AIML Department Dashboard
      </h1>
      <div style={{
        display: 'grid',
        gridTemplateColumns: 'repeat(auto-fit, minmax(300px, 1fr))',
        gap: '20px',
        maxWidth: '1200px',
        margin: '0 auto'
      }}>
        {sections.map((section, index) => (
          <div
            key={index}
            onClick={() => handleSectionClick(section.name)}
            style={{
              backgroundColor: 'rgba(255, 255, 255, 0.1)',
              padding: '30px',
              borderRadius: '10px',
              cursor: 'pointer',
              transition: 'transform 0.3s, box-shadow 0.3s',
              boxShadow: '0 4px 8px rgba(0, 0, 0, 0.3)',
              border: '1px solid rgba(255, 255, 255, 0.2)'
            }}
            onMouseOver={(e) => {
              e.target.style.transform = 'translateY(-5px)';
              e.target.style.boxShadow = '0 8px 16px rgba(0, 0, 0, 0.4)';
            }}
            onMouseOut={(e) => {
              e.target.style.transform = 'translateY(0)';
              e.target.style.boxShadow = '0 4px 8px rgba(0, 0, 0, 0.3)';
            }}
          >
            <h3 style={{ color: 'white', marginBottom: '10px' }}>{section.name}</h3>
            <p style={{ color: '#cccccc' }}>{section.description}</p>
          </div>
        ))}
      </div>
    </div>
  );
}

export default Dashboard;
