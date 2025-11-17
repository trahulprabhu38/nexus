import React, { useState, useEffect, useRef } from 'react';
import { useNavigate } from 'react-router-dom';
import SpeechRecognition, { useSpeechRecognition } from 'react-speech-recognition';

function Chatbot() {
  const [messages, setMessages] = useState([
    { text: 'Hello! I am your AIML Nexus assistant. How can I help you today? You can ask about your results, timetable, attendance, or fees.', sender: 'bot' }
  ]);
  const [input, setInput] = useState('');
  const [chatHistory, setChatHistory] = useState([]);
  const [currentChatId, setCurrentChatId] = useState(null);
  const [isListening, setIsListening] = useState(false);
  const navigate = useNavigate();
  const messagesEndRef = useRef(null);

  const {
    transcript,
    listening,
    resetTranscript,
    browserSupportsSpeechRecognition
  } = useSpeechRecognition();

  const mockResults = {
    1: [
      { subject: 'Mathematics', grade: 'A', marks: 85 },
      { subject: 'Physics', grade: 'B+', marks: 78 },
      { subject: 'Chemistry', grade: 'A-', marks: 82 },
      { subject: 'Computer Science', grade: 'A', marks: 88 }
    ],
    2: [
      { subject: 'Data Structures', grade: 'A', marks: 90 },
      { subject: 'Algorithms', grade: 'A-', marks: 85 },
      { subject: 'Machine Learning', grade: 'B+', marks: 80 },
      { subject: 'Statistics', grade: 'A', marks: 87 }
    ],
    3: [
      { subject: 'Deep Learning', grade: 'A', marks: 92 },
      { subject: 'Computer Vision', grade: 'A-', marks: 88 },
      { subject: 'NLP', grade: 'B+', marks: 82 },
      { subject: 'AI Ethics', grade: 'A', marks: 89 }
    ],
    4: [
      { subject: 'Advanced ML', grade: 'A', marks: 95 },
      { subject: 'Big Data', grade: 'A-', marks: 90 },
      { subject: 'Project', grade: 'A', marks: 96 },
      { subject: 'Internship', grade: 'A', marks: 93 }
    ]
  };

  const mockTimetable = {
    Monday: ['ML 9-11', 'DL 11-1', 'CV 2-4'],
    Tuesday: ['NLP 9-11', 'AI Ethics 11-1', 'Project 2-4'],
    Wednesday: ['Data Mining 9-11', 'Big Data 11-1', 'Seminar 2-4'],
    Thursday: ['Advanced ML 9-11', 'Research 11-1', 'Lab 2-4'],
    Friday: ['Review 9-11', 'Presentation 11-1']
  };

  const mockAttendance = {
    '2021-2024': {
      subjects: {
        'Machine Learning': { attended: 45, total: 50, percentage: 90 },
        'Deep Learning': { attended: 42, total: 48, percentage: 87.5 },
        'Computer Vision': { attended: 38, total: 45, percentage: 84.4 },
        'NLP': { attended: 40, total: 46, percentage: 87 },
        'AI Ethics': { attended: 44, total: 48, percentage: 91.7 }
      },
      overall: { attended: 209, total: 237, percentage: 88.2 }
    },
    '2022-2025': {
      subjects: {
        'Data Structures': { attended: 43, total: 48, percentage: 89.6 },
        'Algorithms': { attended: 41, total: 46, percentage: 89.1 },
        'Machine Learning': { attended: 44, total: 50, percentage: 88 },
        'Statistics': { attended: 39, total: 44, percentage: 88.6 },
        'Big Data': { attended: 42, total: 48, percentage: 87.5 }
      },
      overall: { attended: 209, total: 236, percentage: 88.6 }
    },
    '2023-2026': {
      subjects: {
        'Mathematics': { attended: 46, total: 50, percentage: 92 },
        'Physics': { attended: 44, total: 48, percentage: 91.7 },
        'Chemistry': { attended: 42, total: 46, percentage: 91.3 },
        'Computer Science': { attended: 45, total: 48, percentage: 93.8 },
        'Data Structures': { attended: 43, total: 46, percentage: 93.5 }
      },
      overall: { attended: 220, total: 238, percentage: 92.4 }
    }
  };

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(scrollToBottom, [messages]);

  useEffect(() => {
    if (transcript) {
      setInput(transcript);
    }
  }, [transcript]);

  const handleVoiceInput = () => {
    if (!browserSupportsSpeechRecognition) {
      alert('Browser does not support speech recognition.');
      return;
    }
    if (listening) {
      SpeechRecognition.stopListening();
      setIsListening(false);
      // Automatically send the recognized speech
      if (input.trim()) {
        handleSend();
      }
    } else {
      resetTranscript();
      SpeechRecognition.startListening({ continuous: true });
      setIsListening(true);
    }
  };

  const handleSend = () => {
    if (input.trim()) {
      const userMessage = { text: input, sender: 'user' };
      const newMessages = [...messages, userMessage];
      setMessages(newMessages);
      setInput('');

      // Reset voice assistant to initial position
      if (isListening) {
        SpeechRecognition.stopListening();
        setIsListening(false);
        resetTranscript();
      }

      // Save to history if new chat
      if (!currentChatId) {
        const chatId = Date.now().toString();
        setCurrentChatId(chatId);
        const newChat = {
          id: chatId,
          title: input.slice(0, 30) + (input.length > 30 ? '...' : ''),
          messages: newMessages,
          timestamp: new Date()
        };
        setChatHistory(prev => [newChat, ...prev]);
      } else {
        // Update existing chat
        setChatHistory(prev => prev.map(chat =>
          chat.id === currentChatId ? { ...chat, messages: newMessages } : chat
        ));
      }

      // Simulate bot response
      setTimeout(() => {
        const response = generateResponse(input.toLowerCase());
        const botMessage = { text: response, sender: 'bot' };
        const finalMessages = [...newMessages, botMessage];
        setMessages(finalMessages);

        // Update history with bot response
        setChatHistory(prev => prev.map(chat =>
          chat.id === currentChatId ? { ...chat, messages: finalMessages } : chat
        ));
      }, 1000);
    }
  };

  const startNewChat = () => {
    setCurrentChatId(null);
    setMessages([
      { text: 'Hello! I am your AIML Nexus assistant. How can I help you today? You can ask about your results, timetable, attendance, or fees.', sender: 'bot' }
    ]);
  };

  const loadChat = (chatId) => {
    const chat = chatHistory.find(c => c.id === chatId);
    if (chat) {
      setCurrentChatId(chatId);
      setMessages(chat.messages);
    }
  };

  const generateResponse = (query) => {
    // Enhanced responses with real-world AIML department context
    if (query.includes('result') || query.includes('grade') || query.includes('marks')) {
      const year = query.match(/year (\d)/)?.[1] || '1';
      const results = mockResults[year];
      return `Here are your Year ${year} results for AIML Department at Dayananda Sagar College:\n${results.map(r => `${r.subject}: ${r.grade} (${r.marks}%)`).join('\n')}\n\nFor detailed grade analysis or revaluation, please contact the department office.`;
    } else if (query.includes('timetable') || query.includes('schedule') || query.includes('class')) {
      const day = Object.keys(mockTimetable).find(d => query.includes(d.toLowerCase())) || 'Monday';
      return `Your ${day} timetable for AIML Department:\n${mockTimetable[day].join('\n')}\n\nNote: Timetables are subject to change. Check the college portal for updates.`;
    } else if (query.includes('attendance') || query.includes('present')) {
      // Extract batch year from query (e.g., "2021-2024 batch", "2022-2025", etc.)
      const batchMatch = query.match(/(\d{4}-\d{4})/);
      const batch = batchMatch ? batchMatch[1] : '2021-2024'; // Default to first batch if not specified

      if (mockAttendance[batch]) {
        const attendance = mockAttendance[batch];
        const subjectDetails = Object.entries(attendance.subjects)
          .map(([subject, data]) => `${subject}: ${data.attended}/${data.total} (${data.percentage}%)`)
          .join('\n');

        return `Attendance Records for AIML Department - Batch ${batch}:\n\nSubject-wise Attendance:\n${subjectDetails}\n\nOverall Attendance: ${attendance.overall.attended}/${attendance.overall.total} (${attendance.overall.percentage}%)\n\nMinimum required attendance: 75%\nCurrent status: ${attendance.overall.percentage >= 75 ? 'Safe' : 'At Risk'}\n\nFor attendance regularization, contact your class coordinator.`;
      } else {
        const availableBatches = Object.keys(mockAttendance).join(', ');
        return `Available attendance records for batches: ${availableBatches}\n\nPlease specify a valid batch year (e.g., "attendance for 2021-2024 batch").`;
      }
    } else if (query.includes('fees') || query.includes('payment') || query.includes('tuition')) {
      return 'AIML Department Fee Structure at Dayananda Sagar College:\n• Tuition Fee: ₹2,00,000 per year\n• Lab Fee: ₹30,000 per year\n• Library Fee: ₹10,000 per year\n• Total Annual Fee: ₹2,40,000\n• Outstanding Balance: ₹50,000\n\nPayment deadline: End of current semester. Late fees apply after due date.';
    } else if (query.includes('faculty') || query.includes('teacher') || query.includes('professor')) {
      return 'AIML Department Faculty at Dayananda Sagar College:\n• Dr. Rajesh Kumar - HOD, Machine Learning\n• Prof. Priya Sharma - Deep Learning\n• Dr. Amit Singh - Computer Vision\n• Asst. Prof. Meera Patel - NLP\n\nFor faculty consultation hours, check department notice board.';
    } else if (query.includes('placement') || query.includes('job') || query.includes('career')) {
      return 'AIML Department Placement Highlights:\n• Average Package: ₹8.5 LPA\n• Highest Package: ₹15 LPA\n• Companies: Google, Microsoft, Amazon, Infosys\n• Placement Rate: 95%\n\nUpcoming placement drives: Check placement portal regularly.';
    } else if (query.includes('project') || query.includes('internship') || query.includes('practical')) {
      return 'AIML Department Project Guidelines:\n• Final Year Project: Mandatory\n• Internship: 6 months required\n• Technologies: Python, TensorFlow, PyTorch\n• Domains: ML, DL, CV, NLP\n\nProject submission deadline: End of semester.';
    } else if (query.includes('exam') || query.includes('test') || query.includes('assessment')) {
      return 'AIML Department Examination Schedule:\n• Mid-term Exams: March 15-25\n• End-term Exams: May 10-25\n• Practical Exams: June 1-10\n\nHall tickets available on college portal. Best of luck!';
    } else if (query.includes('library') || query.includes('book') || query.includes('resource')) {
      return 'AIML Department Library Resources:\n• Books: 500+ AI/ML titles\n• Journals: IEEE, ACM subscriptions\n• Online Databases: IEEE Xplore, ACM Digital Library\n• Lab Access: 24/7 for students\n\nIssue limit: 5 books per semester.';
    } else if (query.includes('event') || query.includes('workshop') || query.includes('seminar')) {
      return 'Upcoming AIML Department Events:\n• AI Workshop: March 20\n• ML Hackathon: April 5-7\n• Industry Seminar: April 15\n• Project Showcase: May 10\n\nRegister through department portal.';
    } else if (query.includes('contact') || query.includes('phone') || query.includes('email')) {
      return 'AIML Department Contact Information:\n• Phone: +91-80-42161750\n• Email: aiml@dsc.edu.in\n• Office Hours: 9 AM - 5 PM\n• Location: Block A, 3rd Floor\n\nFor urgent matters, contact HOD directly.';
    } else if (query.includes('admission') || query.includes('eligibility') || query.includes('requirement')) {
      return 'AIML Department Admission Requirements:\n• Eligibility: 60% in 12th (PCM)\n• Entrance: CET/KCET/JEE\n• Fee: ₹2,40,000 per year\n• Duration: 4 years\n• Intake: 60 students\n\nApply through college admission portal.';
    } else {
      return 'I am your AIML Nexus assistant for Dayananda Sagar College. I can help with:\n• Academic results and grades\n• Class timetable and schedule\n• Attendance records\n• Fee structure and payments\n• Faculty information\n• Placement details\n• Project guidelines\n• Exam schedules\n• Library resources\n• Department events\n• Contact information\n\nPlease ask about any of these topics!';
    }
  };

  return (
    <div style={{
      height: '100vh',
      display: 'flex',
      background: 'linear-gradient(to bottom, #16213e, #0f3460)',
      color: 'white'
    }}>
      {/* Sidebar for chat history */}
      <div style={{
        width: '300px',
        backgroundColor: 'rgba(0,0,0,0.2)',
        borderRight: '1px solid rgba(255,255,255,0.1)',
        display: 'flex',
        flexDirection: 'column'
      }}>
        <div style={{
          padding: '20px',
          borderBottom: '1px solid rgba(255,255,255,0.1)'
        }}>
          <button
            onClick={startNewChat}
            style={{
              width: '100%',
              padding: '10px',
              backgroundColor: '#4CAF50',
              color: 'white',
              border: 'none',
              borderRadius: '5px',
              cursor: 'pointer',
              marginBottom: '10px'
            }}
          >
            New Chat
          </button>
          <h3>Chat History</h3>
        </div>
        <div style={{ flex: 1, overflowY: 'auto' }}>
          {chatHistory.map(chat => (
            <div
              key={chat.id}
              onClick={() => loadChat(chat.id)}
              style={{
                padding: '10px 20px',
                cursor: 'pointer',
                borderBottom: '1px solid rgba(255,255,255,0.05)',
                backgroundColor: currentChatId === chat.id ? 'rgba(76,175,80,0.2)' : 'transparent'
              }}
            >
              <div style={{ fontWeight: 'bold', marginBottom: '5px' }}>{chat.title}</div>
              <div style={{ fontSize: '12px', color: '#cccccc' }}>
                {chat.timestamp.toLocaleDateString()}
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* Main chat area */}
      <div style={{
        flex: 1,
        display: 'flex',
        flexDirection: 'column'
      }}>
        <div style={{
          display: 'flex',
          justifyContent: 'space-between',
          alignItems: 'center',
          padding: '10px 20px',
          backgroundColor: 'rgba(0,0,0,0.3)',
          borderBottom: '1px solid rgba(255,255,255,0.1)'
        }}>
          <h2>AIML NEXUS ASSISTANT</h2>
          <button
            onClick={() => navigate('/')}
            style={{
              padding: '8px 16px',
              backgroundColor: '#4CAF50',
              color: 'white',
              border: 'none',
              borderRadius: '5px',
              cursor: 'pointer'
            }}
          >
            Logout
          </button>
        </div>

        <div style={{ flex: 1, padding: '20px', display: 'flex', flexDirection: 'column' }}>
          <div style={{ flex: 1, overflowY: 'auto', marginBottom: '20px' }}>
            {messages.map((msg, idx) => (
              <div
                key={idx}
                style={{
                  marginBottom: '10px',
                  textAlign: msg.sender === 'user' ? 'right' : 'left'
                }}
              >
                <div
                  style={{
                    display: 'inline-block',
                    padding: '10px 15px',
                    borderRadius: '20px',
                    backgroundColor: msg.sender === 'user' ? '#4CAF50' : 'rgba(255,255,255,0.1)',
                    maxWidth: '70%',
                    whiteSpace: 'pre-line'
                  }}
                >
                  {msg.text}
                </div>
              </div>
            ))}
            <div ref={messagesEndRef} />
          </div>
          <div style={{ display: 'flex', alignItems: 'center' }}>
            <input
              value={input}
              onChange={(e) => setInput(e.target.value)}
              onKeyPress={(e) => e.key === 'Enter' && handleSend()}
              placeholder="Ask about results, timetable, attendance, fees..."
              style={{
                flex: 1,
                padding: '10px',
                borderRadius: '20px',
                border: 'none',
                marginRight: '10px',
                backgroundColor: '#E8F5E8',
                color: '#333'
              }}
            />
            <button
              onClick={handleVoiceInput}
              style={{
                padding: '10px',
                backgroundColor: isListening ? '#FF5722' : '#2196F3',
                color: 'white',
                border: 'none',
                borderRadius: '50%',
                cursor: 'pointer',
                width: '40px',
                height: '40px',
                marginRight: '10px',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center'
              }}
              title={isListening ? 'Stop Listening' : 'Start Voice Input'}
            >
              {isListening ? '⏹️' : '🎤'}
            </button>
            <button
              onClick={handleSend}
              style={{
                padding: '10px 20px',
                backgroundColor: '#4CAF50',
                color: 'white',
                border: 'none',
                borderRadius: '20px',
                cursor: 'pointer'
              }}
            >
              Send
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}

export default Chatbot;
