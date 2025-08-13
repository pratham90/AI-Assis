
import React, { useState, useRef, useEffect } from 'react';
import './App.css';



const BACKEND_URL = process.env.REACT_APP_BACKEND_URL || 'http://localhost:5000';

function App() {
  const [drag, setDrag] = useState(false);
  const [pos, setPos] = useState({ x: 20, y: 20 }); // Smaller default position
  const [offset, setOffset] = useState({ x: 0, y: 0 });
  const [questions, setQuestions] = useState([]);
  const [answers, setAnswers] = useState([]);
  const [aiResponse, setAiResponse] = useState('');
  const [listening, setListening] = useState(false);
  const [resume, setResume] = useState(null);
  const [resumeFile, setResumeFile] = useState(null);
  const [smartMode, setSmartMode] = useState(false);
  
  // Privacy features
  const [compactMode, setCompactMode] = useState(false);
  const [opacity, setOpacity] = useState(0.95);
  const [isMinimized, setIsMinimized] = useState(false);

  // Always reset Smart mode and resume state on page load to prevent stale state after refresh
  useEffect(() => {
    setSmartMode(false);
    setResume(null);
    setResumeFile(null);
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
    setDrag(true);
    setOffset({
      x: e.clientX - pos.x,
      y: e.clientY - pos.y,
    });
  };
  const onMouseMove = (e) => {
    if (drag) {
      setPos({
        x: e.clientX - offset.x,
        y: e.clientY - offset.y,
      });
    }
  };
  const onMouseUp = () => setDrag(false);

  useEffect(() => {
    if (drag) {
      window.addEventListener('mousemove', onMouseMove);
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
    const handleHotkey = (e) => {
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
        case 's': // Toggle smart mode
          if (!resumeFile) {
            alert('Please upload a resume before enabling Smart mode.');
            setSmartMode(false);
            return;
          }
          setSmartMode((prev) => !prev);
          break;
        case 'r': { // Upload resume
          const input = document.getElementById('resume-upload');
          if (input) input.click();
          break;
        }
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
          setOpacity(prev => prev > 0.7 ? 0.6 : 0.95);
          break;
        case 'x': // Quick minimize (very low opacity)
          setOpacity(0.3);
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
    };
    window.addEventListener('keydown', handleHotkey);
    return () => window.removeEventListener('keydown', handleHotkey);
  }, [resumeFile]);

  // Speech recognition setup
  useEffect(() => {
    if (!('webkitSpeechRecognition' in window || 'SpeechRecognition' in window)) {
      return;
    }
    const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
    const recognition = new SpeechRecognition();
    recognition.continuous = true;
    recognition.interimResults = false;
    recognition.lang = 'en-US';
    recognitionRef.current = recognition;

    recognition.onresult = (event) => {
      const lastResult = event.results[event.results.length - 1];
      if (lastResult.isFinal) {
        const text = lastResult[0].transcript.trim();
        setQuestions((q) => [...q, text]);
        askAI(text);
      }
    };
    recognition.onend = () => {
      if (listening) recognition.start();
    };
    if (listening) recognition.start();
    return () => recognition.stop();
    // eslint-disable-next-line
  }, [listening]);

  // Auto-scroll to latest question/answer
  useEffect(() => {
    if (questionPanelRef.current) {
      questionPanelRef.current.scrollTop = questionPanelRef.current.scrollHeight;
    }
  }, [questions]);
  useEffect(() => {
    if (answerPanelRef.current) {
      answerPanelRef.current.scrollTop = answerPanelRef.current.scrollHeight;
    }
  }, [answers, aiResponse]);

  // Backend call for AI response
  const askAI = async (question) => {
    setAiResponse('Thinking...');
    // Build conversation history for context chaining
    const history = questions.map((q, i) => ({
      role: 'user', content: q
    })).concat(
      answers.map((a, i) => ({
        role: 'assistant', content: a
      }))
    );
    try {
      let res, data;
      if (smartMode) {
        if (!resumeFile) {
          setAiResponse('');
          setAnswers(['Error: Please upload a resume before using Smart mode.']);
          return;
        }
        // Debug: print Smart mode, resumeFile, and FormData contents
        console.log('[DEBUG] Smart mode ON');
        console.log('[DEBUG] resumeFile:', resumeFile);
        // Use FormData for file upload in Smart mode
        const formData = new FormData();
        formData.append('question', question);
        formData.append('mode', 'resume');
        formData.append('history', JSON.stringify(history));
        formData.append('resume', resumeFile);
        // Print FormData keys and values
        for (let pair of formData.entries()) {
          console.log(`[DEBUG] FormData: ${pair[0]} =`, pair[1]);
        }
        res = await fetch(`${BACKEND_URL}/ask`, {
          method: 'POST',
          body: formData
        });
      } else {
        // Only use global mode if Smart mode is off
        console.log('[DEBUG] Smart mode OFF');
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
      }
      data = await res.json();
      setAiResponse('');
      setAnswers([data.answer || 'No response.']); // Only show latest answer
    } 
    catch (e) {
      setAiResponse('');
      setAnswers(['Error connecting to backend.']);
    }
  };

  // Resume upload handler
  const handleResumeUpload = (e) => {
    const file = e.target.files[0];
    if (!file) return;
    setResumeFile(file);
    console.log('Resume file set:', file);
    if (file.name.endsWith('.pdf')) {
      setResume('PDF resume loaded'); // Placeholder, backend will extract text
    } else {
      const reader = new FileReader();
      reader.onload = (ev) => {
        setResume(ev.target.result);
      };
      reader.readAsText(file);
    }
  };

  // UI
  return (
    <div
      className={`cluely-widget ${compactMode ? 'compact' : 'wide'}`}
      ref={widgetRef}
      style={{ 
        left: pos.x, 
        top: pos.y, 
        opacity: opacity,
        transition: 'opacity 0.3s ease',
        maxWidth: compactMode ? '300px' : '1200px',
        fontSize: compactMode ? '0.85em' : '1em'
      }}
    >
      <div className="cluely-header" onMouseDown={onMouseDown}>
        <span role="img" aria-label="insights">💡</span> 
        {compactMode ? 'IA' : 'Live insights'}
        <span style={{ fontSize: '0.75em', marginLeft: 8, color: '#888' }}>
          {compactMode ? '(Alt+Shift+H)' : '(Hide: Alt+Shift+H, Unhide: Alt+Shift+U)'}
        </span>
        <button className="cluely-hide-btn" title="Hide" onClick={() => {
          widgetRef.current.style.display = 'none';
          setIsMinimized(true);
        }}>×</button>
      </div>
      <div className="cluely-main-panel">
        <div className="cluely-section cluely-left-panel">
          <div className="cluely-subheader">{compactMode ? 'Q' : 'Questions'}</div>
          <div className="cluely-transcript" ref={questionPanelRef}>
            {questions.length === 0 && <div className="cluely-faint">No questions yet.</div>}
            {questions.map((item, i) => (
              <div key={i} className="cluely-line user" style={{marginBottom:'1.2em'}}>{item}</div>
            ))}
          </div>
          <div className="cluely-section" style={{display:'flex',alignItems:'center',gap:'1rem'}}>
            <button className={`cluely-action-btn ${listening ? 'listening' : ''}`} onClick={() => setListening(l => !l)}>
              {listening ? '⏸️ Stop Listening' : '🎤 Start Listening'}
            </button>
            <input id="resume-upload" type="file" accept=".txt,.pdf" style={{ display: 'none' }} onChange={handleResumeUpload} />
            {resumeFile && <span className="cluely-faint">✓</span>}
            {!resumeFile && smartMode && (
              <span className="cluely-faint" style={{color:'red'}}>Upload resume</span>
            )}
          </div>
          <div className="cluely-faint" style={{marginTop:'0.5rem', fontSize: '0.8em'}}>
            {compactMode ? (
              <>
                S: <span style={{color: smartMode && resumeFile ? '#4CAF50' : '#aaa'}}>{smartMode && resumeFile ? 'ON' : 'OFF'}</span> | 
                Smart: Alt+Shift+S | Resume: Alt+Shift+R | Clear: Alt+Shift+C | Hide: Alt+Shift+H | Unhide: Alt+Shift+U | Compact: Alt+Shift+M | Opacity: Alt+Shift+O | Minimize: Alt+Shift+X | Quit: Alt+Shift+Q
              </>
            ) : (
              <>
                Smart: <span style={{color: smartMode && resumeFile ? '#4CAF50' : '#aaa', fontWeight:600}}>{smartMode && resumeFile ? 'ON' : 'OFF'}</span> (Alt+Shift+S) | 
                Resume: Alt+Shift+R | Clear: Alt+Shift+C | Hide: Alt+Shift+H | Unhide: Alt+Shift+U | Compact: Alt+Shift+M | Opacity: Alt+Shift+O | Minimize: Alt+Shift+X | Quit: Alt+Shift+Q<br/>
                {smartMode && resumeFile && <span style={{color:'#4CAF50'}}>Resume context active</span>}
              </>
            )}
          </div>
        </div>
        <div className="cluely-section cluely-right-panel">
          <div className="cluely-subheader">{compactMode ? 'A' : 'Answers'}</div>
          <div className="cluely-ai-response-panel" ref={answerPanelRef}>
            {answers.length === 0 && <span className="cluely-faint">No answers yet.</span>}
            {answers.map((ans, i) => (
              <div key={i} className="cluely-line ai" style={{marginBottom:'1.2em'}}>
                {Array.isArray(ans)
                  ? (
                    <ul style={{margin:0, paddingLeft:'1.2em'}}>
                      {ans.map((item, idx) => <li key={idx}>{item}</li>)}
                    </ul>
                  )
                  : (ans.includes('\n- ') || ans.includes('\n• ')
                    ? (
                        <ul style={{margin:0, paddingLeft:'1.2em'}}>
                          {ans.split(/\n[-•] /).filter(Boolean).map((item, idx) => <li key={idx}>{item.trim()}</li>)}
                        </ul>
                    )
                    : ans.split(/\n{2,}/).map((p, idx) => <p key={idx} style={{margin:'0 0 0.7em 0'}}>{p.trim()}</p>)
                  )
                }
              </div>
            ))}
            {aiResponse === 'Thinking...' && <div className="cluely-faint">Thinking...</div>}
          </div>
        </div>
      </div>
    </div>
  );
}

export default App;
