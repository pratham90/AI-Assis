import React, { useState, useRef, useEffect } from 'react';
import './App.css';



const BACKEND_URL = process.env.REACT_APP_BACKEND_URL || 'http://localhost:5000';

function App() {
  // Logout handler (must be defined before use)
  function handleLogout() {
  setLoggedIn(false);
  setEmail('');
  setPassword('');
  setCredits(0);
  setQuestions([]);
  setAnswers([]);
  setAiResponse('');
  setResume(null);
  setResumeFile(null);
  setResumeError('');
  setSmartMode(false);
  localStorage.removeItem('email');
  localStorage.removeItem('password');
  localStorage.setItem('loggedIn', 'false');
  setAuthMode('login');
  setAuthError('');
  // Optionally, call backend logout endpoint
  fetch(`${BACKEND_URL}/logout`, { method: 'POST', credentials: 'include' }).catch(()=>{});
  // Always set credits to 0 on logout
  setCredits(0);
  }
  const [drag, setDrag] = useState(false);
  const [pos, setPos] = useState({ x: 20, y: 20 }); // Smaller default position
  const [offset, setOffset] = useState({ x: 0, y: 0 });
  const [questions, setQuestions] = useState([]);
  const [answers, setAnswers] = useState([]);
  const [aiResponse, setAiResponse] = useState('');
  const [listening, setListening] = useState(false);
  const [speechError, setSpeechError] = useState('');
  const [resume, setResume] = useState(null); // resume text
  const [resumeFile, setResumeFile] = useState(null); // uploaded file
  const [resumeError, setResumeError] = useState('');
  const [smartMode, setSmartMode] = useState(false);
  // Auth & credits
  const [email, setEmail] = useState(() => localStorage.getItem('email') || '');
  const [password, setPassword] = useState(() => localStorage.getItem('password') || '');
  const [loggedIn, setLoggedIn] = useState(() => {
    return localStorage.getItem('loggedIn') === 'true';
  });
  const [credits, setCredits] = useState(0);
  const [authMode, setAuthMode] = useState('login'); // 'login' or 'signup'
  const [authError, setAuthError] = useState('');
  // Privacy features
  const [compactMode, setCompactMode] = useState(false);
  const [opacity, setOpacity] = useState(0.95);
  const [isMinimized, setIsMinimized] = useState(false);


  // Always reset Smart mode and resume state on page load to prevent stale state after refresh
  useEffect(() => {
    setSmartMode(false);
    setResume(null);
    setResumeFile(null);
    // On mount, if logged in, fetch credits from backend
    const storedEmail = localStorage.getItem('email');
    const storedPassword = localStorage.getItem('password');
    const storedLoggedIn = localStorage.getItem('loggedIn') === 'true';
    if (storedLoggedIn && storedEmail && storedPassword) {
      fetch(`${BACKEND_URL}/get_credits`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ email: storedEmail, password: storedPassword })
      })
        .then(res => res.json())
        .then(data => {
          setCredits(data.credits || 0);
        })
        .catch(() => setCredits(0));
    }
  }, []);

  // Ensure Smart mode is OFF if resumeFile is missing (e.g., after refresh)
  useEffect(() => {
    if (!resumeFile && smartMode) {
      setSmartMode(false);
    }
  }, [resumeFile, smartMode]);
  const recognitionRef = useRef(null);
  const widgetRef = useRef(null);
  const questionPanelRef = useRef(null);
  const answerPanelRef = useRef(null);

  // Drag handlers
  const onMouseDown = (e) => {
    // Only drag if clicking header
    if (e.target.className !== 'cluely-header') return;
    setDrag(true);
    setOffset({
      x: e.clientX - pos.x,
      y: e.clientY - pos.y
    });
  };
  // Removed unused: listening, resume
  const onMouseMove = (e) => {
    if (drag) {
      setPos({
        x: e.clientX - offset.x,
        y: e.clientY - offset.y
      });
    }
  };
  const onMouseUp = () => setDrag(false);

  useEffect(() => {
    if (drag) {
    // Removed unused: isMinimized
      window.addEventListener('mouseup', onMouseUp);
    } else {
      window.removeEventListener('mousemove', onMouseMove);
      window.removeEventListener('mouseup', onMouseUp);
    }
    return () => {
      window.removeEventListener('mousemove', onMouseMove);
      window.removeEventListener('mouseup', onMouseUp);
    };
    // eslint-disable-next-line
  }, [drag, offset]);

  // Hotkeys (Alt+Shift + letter) to avoid browser conflicts
  useEffect(() => {
      function handleHotkey(e) {
        // Only trigger hotkeys if focus is NOT on an input, textarea, or contenteditable
        const active = document.activeElement;
        if (
          active && (
            active.tagName === 'INPUT' ||
            active.tagName === 'TEXTAREA' ||
            active.isContentEditable
          )
        ) {
          return;
        }
        if (!e.altKey || !e.shiftKey) return;
        const k = (e.key || '').toLowerCase();
  switch (k) {
          case 'l': // Logout
            handleLogout();
            break;
  // Logout handler
  function handleLogout() {
    setLoggedIn(false);
    setEmail('');
    setPassword('');
    setCredits(0);
    localStorage.removeItem('email');
    localStorage.removeItem('password');
    localStorage.setItem('loggedIn', 'false');
    setAuthMode('login');
    setAuthError('');
    // Optionally, call backend logout endpoint
    fetch(`${BACKEND_URL}/logout`, { method: 'POST', credentials: 'include' }).catch(()=>{});
    // Always set credits to 0 on logout
    setCredits(0);
  }
          case 's': // Toggle smart mode
            if (!resumeFile) {
              alert('Please upload a resume before enabling Smart mode.');
              setSmartMode(false);
              return;
            }
            setSmartMode((prev) => !prev);
            break;
          case 'r': // Upload resume
            let fileInput = document.getElementById('resume-upload-input');
            if (!fileInput) {
              // If not found, try to querySelector for input[type="file"]
              fileInput = document.querySelector('input[type="file"]');
            }
            if (fileInput) {
              fileInput.click();
            } else {
              alert('Resume upload input not found.');
            }
            break;
          case 'c': // Clear answers
            setAnswers([]);
            break;
          case 'h': // Hide widget
            if (widgetRef.current) {
              widgetRef.current.style.display = 'none';
              setIsMinimized(true);
            }
            break;
          case 'u': // Unhide widget
            if (widgetRef.current) {
              widgetRef.current.style.display = '';
              setIsMinimized(false);
            }
            break;
          case 'm': // Toggle compact mode
            setCompactMode(prev => !prev);
            break;
          case 'o': // Toggle opacity (low/high)
            setOpacity(prev => prev > 0.7 ? 0.5 : 0.92);
            break;
          case 'x': // Quick minimize (very low opacity)
            setOpacity(0.25);
            break;
          case 'q': // Quit application (Alt+Shift+Q)
            if (window.pywebview && window.pywebview.api && typeof window.pywebview.api.quit === 'function') {
              window.pywebview.api.quit();
            } else {
              // Show a notification for debugging if quit is not available
              alert('Quit hotkey: PyWebView API not available. If you are running the EXE and this message appears, please ensure the EXE is built with the latest code.');
              console.warn('Quit hotkey: PyWebView API not available.', window.pywebview);
              window.close();
            }
            break;
          default:
            break;
        }
      }
      window.addEventListener('keydown', handleHotkey);
      return () => window.removeEventListener('keydown', handleHotkey);
  }, [resumeFile]);

  // Speech recognition setup
  useEffect(() => {
    setSpeechError('');
    if (!('webkitSpeechRecognition' in window || 'SpeechRecognition' in window)) {
      setSpeechError('Speech recognition is not supported in this browser. Use Chrome or Edge.');
      return;
    }
    const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
    const recognition = new SpeechRecognition();
    recognition.continuous = true;
    recognition.interimResults = false;
    recognition.lang = 'en-US';
    recognitionRef.current = recognition;

    let stopRequested = false;

    recognition.onresult = (event) => {
      const lastResult = event.results[event.results.length - 1];
      if (lastResult.isFinal) {
        setAnswers([]); // Clear previous answer
        setQuestions((q) => [...q, lastResult[0].transcript.trim()]);
        (async () => {
          await askAI(lastResult[0].transcript.trim());
        })();
      }
    };
    recognition.onerror = (event) => {
      if (event.error === 'not-allowed' || event.error === 'denied') {
        setSpeechError('Microphone access denied. Please allow microphone permission.');
      } else {
        setSpeechError('Speech recognition error: ' + event.error);
      }
      setListening(false);
      stopRequested = true;
      recognition.stop();
    };
    recognition.onend = () => {
      if (listening && !stopRequested) {
        try { recognition.start(); } catch {}
      }
    };
    if (listening) {
      stopRequested = false;
      try {
        recognition.start();
      } catch (e) {
        setSpeechError('Could not start speech recognition: ' + e.message);
        setListening(false);
      }
    } else {
      stopRequested = true;
      recognition.stop();
      if (typeof recognition.abort === 'function') recognition.abort();
    }
    return () => {
      stopRequested = true;
      recognition.stop();
      if (typeof recognition.abort === 'function') recognition.abort();
    };
    // eslint-disable-next-line
  }, [listening]);

  // Auto-scroll to latest question/answer
  useEffect(() => {
    if (questionPanelRef.current) {
      questionPanelRef.current.scrollTop = 0;
    }
  }, [questions]);
  useEffect(() => {
    if (answerPanelRef.current) {
      answerPanelRef.current.scrollTop = 0;
    }
  }, [answers, aiResponse]);

  // (deductCredit is defined later, only keep the robust version)

  // Move askAI to top-level inside App, after hooks
  async function askAI(question) {
    // Only block if not logged in and no valid credentials
    if (!loggedIn && (!email || !password)) {
      setAiResponse('Please log in first.');
      return;
    }
    if (credits <= 0) {
      setAiResponse('No credits left.');
      return;
    }
    setAnswers([]); // Clear previous answer
    setAiResponse('Thinking...');
    // Build conversation history for context chaining
    const history = questions.map((q, i) => ({
      role: 'user', content: q
    })).concat(
      answers.map((a, i) => ({
        role: 'assistant', content: a
      }))
    );
    let res, data;
    try {
      if (smartMode) {
        if (!resumeFile) {
          setAiResponse('');
          setAnswers(['Error: Please upload a valid resume before using Smart mode.']);
          return;
        }
        // Use FormData for file upload in Smart mode
        const formData = new FormData();
        formData.append('question', question);
        formData.append('mode', 'resume');
        formData.append('history', JSON.stringify(history));
        formData.append('resume', resumeFile); // Always send resume file
        if (email) formData.append('email', email);
        if (password) formData.append('password', password);
        res = await fetch(`${BACKEND_URL}/ask`, {
          method: 'POST',
          body: formData
        });
        data = await res.json();
        // If backend extracted resume text, update resume state
        if (data.resume_text) {
          setResume(data.resume_text);
        }
        if (data.answer && data.answer.includes('Could not extract any text from the uploaded resume')) {
          setResumeError(data.answer);
          setAiResponse('');
          setAnswers([data.answer]);
          setSmartMode(false);
          return;
        }
        if (data.answer && !data.answer.includes('No relevant information found')) {
          setAiResponse('');
          setAnswers([data.answer]);
          setResumeError('');
          // Deduct credit only after successful answer
          if (typeof deductCredit === 'function') {
            await deductCredit();
          }
        } else {
          // If no relevant info found, fallback to general answer
          const generalRes = await fetch(`${BACKEND_URL}/ask`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
              question,
              resume: '',
              mode: 'global',
              history
            }),
          });
          const generalData = await generalRes.json();
          setAiResponse('');
          setAnswers([generalData.answer || 'No response.']);
          setResumeError('');
          if (typeof deductCredit === 'function') {
            await deductCredit();
          }
        }
      } else {
        // Only use global mode if Smart mode is off
        res = await fetch(`${BACKEND_URL}/ask`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            question,
            resume: '',
            mode: 'global',
            history // send conversation history for context
          }),
        });
        data = await res.json();
        setAiResponse('');
        setAnswers([data.answer || 'No response.']);
        setResumeError('');
        if (typeof deductCredit === 'function') {
          await deductCredit();
        }
      }
    } catch (e) {
      setAiResponse('');
      setAnswers(['Error connecting to backend.']);
      setResumeError('');
    }
  }

  // Resume upload handler
  const handleResumeUpload = (e) => {
    const file = e.target.files[0];
    if (!file) return;
    setResumeFile(file);
    setResume(null);
    setResumeError('');
    setAnswers([]);
    setQuestions([]); // Always clear previous questions as well
    setAiResponse('');
    // Optionally clear Smart mode to force user to re-enable if needed
    // setSmartMode(false);
    console.log('Resume file set:', file);
    if (file.name.endsWith('.pdf')) {
      // For PDF, let backend extract text and set resume after first askAI call
      setResume(null);
    } else {
      const reader = new FileReader();
      reader.onload = (ev) => {
        setResume(ev.target.result);
      };
      reader.readAsText(file);
    }
  };

  // Auth API calls
  const handleAuth = async (e) => {
    e.preventDefault();
    setAuthError('');
    try {
      const endpoint = authMode === 'login' ? '/login' : '/signup';
      const res = await fetch(`${BACKEND_URL}${endpoint}`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ email, password })
      });
      const data = await res.json();
      if (data.success) {
        setLoggedIn(true);
        setAuthError('');
        setQuestions([]);
        setAnswers([]);
        setAiResponse('');
        localStorage.setItem('email', email);
        localStorage.setItem('password', password);
        localStorage.setItem('loggedIn', 'true');
        // Always fetch credits after login/signup
        const credRes = await fetch(`${BACKEND_URL}/get_credits`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ email, password })
        });
        const credData = await credRes.json();
        setCredits(credData.credits || 0);
      } else {
        setAuthError(data.message || 'Authentication failed');
        setLoggedIn(false);
        setCredits(0);
        setQuestions([]);
        setAnswers([]);
        setAiResponse('');
        localStorage.removeItem('email');
        localStorage.removeItem('password');
        localStorage.setItem('loggedIn', 'false');
      }
    } catch (err) {
      setAuthError('Error connecting to backend.');
      setLoggedIn(false);
      setCredits(0);
      setQuestions([]);
      setAnswers([]);
      setAiResponse('');
      localStorage.removeItem('email');
      localStorage.removeItem('password');
      localStorage.setItem('loggedIn', 'false');
    }
  };

  // Always update credits after using a credit
  const deductCredit = async () => {
    try {
      const res = await fetch(`${BACKEND_URL}/use_credit`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ email, password })
      });
      const data = await res.json();
      if (data.success && typeof data.credits === 'number') {
        setCredits(data.credits);
        return true;
      } else if (data.credits === 0) {
        setCredits(0);
        return false;
      } else {
        // Always fetch credits from backend if uncertain
        const credRes = await fetch(`${BACKEND_URL}/get_credits`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ email, password })
        });
        const credData = await credRes.json();
        setCredits(credData.credits || 0);
        return false;
      }
    } catch {
      // On error, try to fetch credits as fallback
      try {
        const credRes = await fetch(`${BACKEND_URL}/get_credits`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ email, password })
        });
        const credData = await credRes.json();
        setCredits(credData.credits || 0);
      } catch {}
      return false;
    }
  };

  // UI
  if (!loggedIn) {
    return (
      <div className="cluely-widget" style={{ left: pos.x, top: pos.y, opacity, width: 340, minWidth: 260, maxWidth: 400 }}>
        <div className="cluely-header" onMouseDown={onMouseDown}>
          <span role="img" aria-label="insights">🔒</span> Login / Signup
        </div>
        <form onSubmit={handleAuth} style={{ padding: 20 }}>
          <div style={{ marginBottom: 10 }}>
            <input
              type="email"
              placeholder="Email"
              value={email}
              onChange={e => setEmail(e.target.value)}
              required
              style={{
                padding: 8,
                width: '100%',
                color: '#fff',
                background: 'rgba(24,24,24,0.95)',
                border: '1px solid #333',
                borderRadius: 6,
                fontSize: '1em',
                '::placeholder': { color: '#fff' }
              }}
              className="white-placeholder"
            />
          </div>
          <div style={{ marginBottom: 10 }}>
            <input
              type="password"
              placeholder="Password"
              value={password}
              onChange={e => setPassword(e.target.value)}
              required
              style={{
                padding: 8,
                width: '100%',
                color: '#fff',
                background: 'rgba(24,24,24,0.95)',
                border: '1px solid #333',
                borderRadius: 6,
                fontSize: '1em',
                '::placeholder': { color: '#fff' }
              }}
              className="white-placeholder"
            />
          </div>
          <button type="submit" className="cluely-action-btn" style={{ width: '100%' }}>{authMode === 'login' ? 'Login' : 'Sign Up'}</button>
          <div style={{ marginTop: 10, textAlign: 'center' }}>
            <span style={{ cursor: 'pointer', color: '#2563eb' }} onClick={() => setAuthMode(authMode === 'login' ? 'signup' : 'login')}>
              {authMode === 'login' ? 'New user? Sign up' : 'Already have an account? Login'}
            </span>
          </div>
          {authError && <div style={{ color: 'red', marginTop: 10 }}>{authError}</div>}
        </form>
      </div>
    );
  }

  // Main UI layout
  // Two-panel layout: left for questions, right for answers
  return (
    <div
      className="cluely-widget"
      ref={widgetRef}
      style={{
        left: pos.x,
        top: pos.y,
        opacity: opacity,
        transition: 'opacity 0.3s ease',
        width: '900px',
        minWidth: '600px',
        maxWidth: '98vw',
        height: '480px',
        minHeight: '320px',
      
        color: '#fff',
        borderRadius: 16,
        boxShadow: '0 2px 24px rgba(0,0,0,0.35)',
        padding: 0,
        overflow: 'hidden',
        display: 'flex',
        flexDirection: 'column',
        alignItems: 'stretch',
        justifyContent: 'flex-start',
      }}
    >
      {/* Hidden file input for resume upload, triggered by hotkey and button */}
      <input
        id="resume-upload-input"
        type="file"
        accept=".pdf,.txt"
        style={{ display: 'none' }}
        onChange={handleResumeUpload}
      />
      <div className="cluely-header" onMouseDown={onMouseDown} style={{display:'flex',alignItems:'center',justifyContent:'space-between',padding:'12px 24px',background:'rgba(24,24,24,0.95)',borderBottom:'1px solid #333',cursor:'move'}}>
        <span role="img" aria-label="insights">💡</span>
        <span style={{fontWeight:600,fontSize:'1.2em',margin:'0 16px'}}>Live insights</span>
        <span style={{fontSize:'1.1em',color:smartMode?'#4CAF50':'#888',marginLeft:16}}>Smart mode: {smartMode ? 'ON' : 'OFF'}</span>
        <span style={{marginLeft:'auto',color:'#4CAF50',fontWeight:600,fontSize:'1.1em'}}>Credits: {credits}</span>
        <button className="cluely-hide-btn" title="Hide" onClick={() => {
          widgetRef.current.style.display = 'none';
          setIsMinimized(true);
        }} style={{marginLeft:16,fontSize:'1.5em',background:'none',border:'none',color:'#fff',cursor:'pointer'}}>×</button>
        <button title="Logout (Alt+Shift+L)" onClick={handleLogout} style={{marginLeft:8,fontSize:'1.1em',background:'none',border:'none',color:'#fff',cursor:'pointer',fontWeight:600}}>Logout</button>
      </div>
      <div style={{display:'flex',flex:1}}>
        {/* Questions panel */}
        <div style={{flex:'0 0 320px',background:'rgba(35,35,35,0.85)',padding:'24px 12px',display:'flex',flexDirection:'column',borderRight:'1px solid #333',height:'100%'}}>
          <div style={{fontWeight:600,fontSize:'1.1em',marginBottom:8}}>Questions</div>
          <div ref={questionPanelRef} style={{flex:1,overflowY:'auto',maxHeight:'340px'}}>
            {questions.map((q,i)=>(
              <div key={i} style={{marginBottom:8,padding:'8px',background:'rgba(41,41,41,0.95)',borderRadius:6,fontSize:'0.98em'}}>{q}</div>
            ))}
          </div>
          <button
            onClick={() => {
              setSpeechError('');
              setListening(true);
            }}
            style={{
              marginTop: 16,
              padding: '8px 8px',
              borderRadius: 24,
              border: 'none',
              background: 'linear-gradient(90deg,#2563eb 60%,#42a5f5 100%)',
              color: '#fff',
              fontWeight: 700,
              fontSize: '0.9em',
              alignSelf: 'flex-start',
              boxShadow: '0 2px 8px rgba(0,0,0,0.18)',
              cursor: 'pointer',
              transition: 'background 0.2s, box-shadow 0.2s',
              display: 'flex',
              alignItems: 'center',
              gap: 5,
              opacity: listening ? 0.7 : 1,
              pointerEvents: listening ? 'none' : 'auto'
            }}
            disabled={listening}
            onMouseEnter={e => e.currentTarget.style.boxShadow = '0 4px 16px rgba(0,0,0,0.28)'}
            onMouseLeave={e => e.currentTarget.style.boxShadow = '0 2px 8px rgba(0,0,0,0.18)'}
          >
            <span style={{fontSize:'0.9em',marginRight:6}}>🎤</span> Start Listening
          </button>
          {listening && (
            <span style={{marginTop:12,color:'#4CAF50',fontWeight:700,fontSize:'1.08em'}}>Listening...</span>
          )}
          
          <span style={{color: resumeError ? '#e53935' : '#4CAF50',fontWeight:600,marginTop:8}}>
            {resumeError ? resumeError : (resume ? 'Resume loaded' : '')}
          </span>
          {/* Hotkey instructions */}
          <div style={{marginTop:16,color:'#aaa',fontSize:'0.95em'}}>
            <div>Smart mode: Alt+Shift+S</div>
            <div>Upload resume: Alt+Shift+R</div>
            <div>Clear answers: Alt+Shift+C</div>
            <div>Hide: Alt+Shift+H | Unhide: Alt+Shift+U | Quit: Alt+Shift+Q</div>
          </div>
        </div>
        {/* Answers panel */}
        <div style={{flex:1,background:'rgba(35,35,35,0.85)',padding:'24px 12px',display:'flex',flexDirection:'column',height:'100%'}}>
          <div style={{fontWeight:600,fontSize:'1.1em',marginBottom:8}}>Answers</div>
          <div ref={answerPanelRef} style={{flex:1,overflowY:'auto',maxHeight:'340px'}}>
            {answers.map((a,i)=>(
              <div key={i} style={{marginBottom:8,padding:'12px',background:'rgba(40,40,40,0.95)',borderRadius:10,fontSize:'0.98em',lineHeight:'1.5'}}>{a}</div>
            ))}
            {aiResponse && <div style={{marginBottom:8,padding:'12px',background:'rgba(40,40,40,0.95)',borderRadius:10,color:'#4CAF50',fontSize:'0.98em'}}>{aiResponse}</div>}
          </div>
        </div>
      </div>
    </div>
  );
}

export default App;
