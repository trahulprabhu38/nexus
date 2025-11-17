import React from 'react';
import { useParams, useNavigate } from 'react-router-dom';

function SectionDetail() {
  const { section } = useParams();
  const navigate = useNavigate();

  const sectionData = {
    'attendance': {
      title: 'Attendance Records',
      content: 'Your attendance for AIML courses is 85%. You have attended 17 out of 20 classes this semester.'
    },
    'timetable': {
      title: 'Class Timetable',
      content: 'Monday: Machine Learning (9:00-10:30), Deep Learning (11:00-12:30)\nTuesday: Data Structures (9:00-10:30), AI Ethics (11:00-12:30)\nWednesday: Neural Networks (9:00-10:30), Computer Vision (11:00-12:30)\nThursday: Natural Language Processing (9:00-10:30), Big Data Analytics (11:00-12:30)\nFriday: Project Work (9:00-12:00)'
    },
    'results': {
      title: 'Academic Results',
      content: 'Semester 1: GPA 8.5\nSemester 2: GPA 8.7\nSemester 3: GPA 9.0\nOverall GPA: 8.7'
    },
    'academic-details': {
      title: 'Academic Details',
      content: 'Program: B.Tech in Artificial Intelligence and Machine Learning\nYear: 3rd Year\nSpecialization: Deep Learning and Computer Vision\nCredits Completed: 120/160\nExpected Graduation: 2025'
    },
    'fees-structure': {
      title: 'Fees Structure',
      content: 'Tuition Fee: ₹1,50,000 per year\nHostel Fee: ₹80,000 per year\nMess Fee: ₹40,000 per year\nTotal Annual Fee: ₹2,70,000\nScholarship Available: ₹50,000 (based on merit)\nNet Payable: ₹2,20,000'
    }
  };

  const data = sectionData[section];

  if (!data) {
    return <div>Section not found</div>;
  }

  return (
    <div style={{
      minHeight: '100vh',
      background: 'linear-gradient(to bottom, #0f3460, #16213e)',
      padding: '20px',
      color: 'white'
    }}>
      <button
        onClick={() => navigate('/dashboard')}
        style={{
          padding: '10px 20px',
          backgroundColor: '#4CAF50',
          color: 'white',
          border: 'none',
          borderRadius: '5px',
          cursor: 'pointer',
          marginBottom: '20px'
        }}
      >
        Back to Dashboard
      </button>
      <h1 style={{ textAlign: 'center', marginBottom: '30px' }}>{data.title}</h1>
      <div style={{
        maxWidth: '800px',
        margin: '0 auto',
        backgroundColor: 'rgba(255, 255, 255, 0.1)',
        padding: '30px',
        borderRadius: '10px',
        whiteSpace: 'pre-line'
      }}>
        {data.content}
      </div>
    </div>
  );
}

export default SectionDetail;
