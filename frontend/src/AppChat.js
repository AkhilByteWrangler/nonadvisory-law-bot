import React, { useState, useRef, useEffect } from 'react';
import axios from 'axios';
import './App.css';
import {
  Box, Container, TextField, IconButton, CircularProgress, Collapse, Typography, Avatar
} from '@mui/material';
import SendIcon from '@mui/icons-material/Send';
import ExpandMoreIcon from '@mui/icons-material/ExpandMore';
import ExpandLessIcon from '@mui/icons-material/ExpandLess';

const LEXI_AVATAR = 'https://api.dicebear.com/7.x/bottts/svg?seed=Lexi';
const JURI_AVATAR = 'https://api.dicebear.com/7.x/bottts/svg?seed=Juri';
const USER_AVATAR = 'https://api.dicebear.com/7.x/personas/svg?seed=User';

const REACTION_EMOJIS = ['👍', '❤️', '😂', '😮', '😢', '👎'];
const SUGGESTIONS = [
  "What are my tenant rights in California?",
  "How do I file a small claims case?",
  "What is the minimum wage in New York?",
  "Can my employer fire me without notice?",
  "What are the requirements for a legal contract?"
];

function formatTime(ts) {
  const d = new Date(ts);
  return d.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
}

function ResourcesDropdown({ resources }) {
  const [open, setOpen] = useState(false);

  if (!resources || resources.length === 0) return null;

  return (
    <Box mt={1}>
      <Box
        sx={{ 
          cursor: 'pointer', 
          display: 'flex', 
          alignItems: 'center', 
          color: '#1976d2', 
          fontSize: 14,
          gap: '4px'
        }}
        onClick={() => setOpen(o => !o)}
      >
        <Typography variant="subtitle2" sx={{ fontWeight: 600, fontSize: 14 }}>
          Resources & Citations ({resources.length})
        </Typography>
        {open ? <ExpandLessIcon fontSize="small" /> : <ExpandMoreIcon fontSize="small" />}
      </Box>
      <Collapse in={open}>
        <Box sx={{ 
          pl: 2, 
          pt: 1, 
          mt: 1,
          borderLeft: '2px solid #e0e0e0',
          display: 'flex',
          flexDirection: 'column',
          gap: '8px'
        }}>
          {resources.map((r) => (
            <Box key={r.number} sx={{ 
              display: 'flex', 
              alignItems: 'baseline',
              gap: '8px'
            }}>
              <Typography 
                component="span" 
                sx={{ 
                  color: '#666',
                  minWidth: '24px',
                  fontSize: '0.9em'
                }}
              >
                [{r.number}]
              </Typography>
              <Typography
                component="a"
                href={r.url}
                target="_blank"
                rel="noopener noreferrer"
                sx={{
                  color: '#1976d2',
                  textDecoration: 'none',
                  '&:hover': {
                    textDecoration: 'underline'
                  },
                  fontSize: '0.9em',
                  flex: 1,
                  wordBreak: 'break-word'
                }}
              >
                {r.title}
              </Typography>
            </Box>
          ))}
        </Box>
      </Collapse>
    </Box>
  );
}

function ChatBubble({ message, isUser, discussion, resources, onReact, reactions, canReact }) {
  const [open, setOpen] = useState(false);
  const [showReactions, setShowReactions] = useState(false);

  const flattenDiscussion = (discussionArr) => {
    if (!discussionArr) return [];
    const result = [];
    discussionArr.forEach((d) => {
      if (d.generator) {
        result.push({
          who: 'Lexi',
          text: d.generator,
          avatar: LEXI_AVATAR,
          color: 'primary',
          timestamp: d.timestamp || message.timestamp
        });
      }
      if (d.discriminator) {
        result.push({
          who: 'Juri',
          text: d.discriminator,
          avatar: JURI_AVATAR,
          color: 'secondary',
          timestamp: d.timestamp || message.timestamp
        });
      }
    });
    return result;
  };

  const discussionEntries = flattenDiscussion(discussion);
  const hasResources = !isUser && resources && resources.length > 0;

  // --- NEW: Detect missing citations in bot message ---
  let missingCitations = [];
  if (!isUser && resources && resources.length > 0 && message.text) {
    // Find all [n] in the message
    const cited = Array.from(message.text.matchAll(/\[(\d+)\]/g)).map(m => parseInt(m[1], 10));
    const available = resources.map(r => r.number);
    missingCitations = cited.filter(n => !available.includes(n));
  }

  return (
    <Box className={`chat-bubble ${isUser ? 'user' : 'bot'}`}
      onMouseEnter={() => canReact && setShowReactions(true)}
      onMouseLeave={() => canReact && setShowReactions(false)}
      style={{ position: 'relative' }}
    >
      <Box className="bubble-content">
        <Box display="flex" alignItems="center" mb={1}>
          <Avatar 
            src={isUser ? USER_AVATAR : LEXI_AVATAR} 
            sx={{ width: 32, height: 32, mr: 1 }}
            alt={isUser ? 'User' : 'Lexi'}
          />
          <Typography 
            variant="subtitle2" 
            sx={{ 
              display: 'flex',
              alignItems: 'center',
              gap: '8px',
              color: 'text.secondary'
            }}
          >
            <span>{isUser ? 'You' : 'Lexi'}</span>
            {message.timestamp && (
              <span style={{ 
                fontSize: '0.85em', 
                color: '#888',
                whiteSpace: 'nowrap'
              }}>
                {formatTime(message.timestamp)}
              </span>
            )}
          </Typography>
        </Box>
        
        <Typography 
          variant="body1" 
          sx={{ whiteSpace: 'pre-line', mb: hasResources ? 2 : 0 }}
        >
          {message.text}
        </Typography>
        {/* Show warning if citations are referenced but not found in resources */}
        {missingCitations.length > 0 && (
          <Typography variant="caption" color="error" sx={{ mt: 1, display: 'block' }}>
            Warning: Citation{missingCitations.length > 1 ? 's' : ''} [{missingCitations.join(', ')}] referenced but not found in resources.
          </Typography>
        )}
        
        {discussion && discussionEntries.length > 0 && (
          <Box mt={2}>
            <Box
              onClick={() => setOpen(o => !o)}
              sx={{
                cursor: 'pointer',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'flex-end',
                color: 'text.secondary',
                gap: '4px',
                '&:hover': {
                  color: 'text.primary'
                }
              }}
            >
              <Typography 
                variant="body2" 
                sx={{ 
                  display: 'flex',
                  alignItems: 'center',
                  gap: '4px',
                  fontSize: '0.85em',
                  fontWeight: 500,
                  color: '#666'
                }}
              >
                Internal Thought Process
                {open ? <ExpandLessIcon fontSize="small" /> : <ExpandMoreIcon fontSize="small" />}
              </Typography>
            </Box>
            <Collapse in={open}>
              <Box 
                className="discussion-dropdown"
                sx={{
                  mt: 1,
                  backgroundColor: 'rgba(0,0,0,0.02)',
                  borderRadius: '8px',
                  p: 2
                }}
              >
                {discussionEntries.map((d, i) => (
                  <Box 
                    key={i} 
                    sx={{ 
                      mb: i < discussionEntries.length - 1 ? 2 : 0,
                      display: 'flex', 
                      alignItems: 'flex-start',
                      borderBottom: i < discussionEntries.length - 1 ? '1px solid rgba(0,0,0,0.06)' : 'none',
                      pb: i < discussionEntries.length - 1 ? 2 : 0
                    }}
                  >
                    <Avatar 
                      src={d.avatar} 
                      sx={{ 
                        width: 24, 
                        height: 24, 
                        mr: 1.5,
                        border: '1px solid rgba(0,0,0,0.1)'
                      }}
                      alt={d.who}
                    />
                    <Box>
                      <Typography 
                        variant="subtitle2" 
                        color={d.color}
                        sx={{
                          display: 'flex',
                          alignItems: 'center',
                          gap: '8px'
                        }}
                      >
                        <span>{d.who}</span>
                        {d.timestamp && (
                          <span style={{ 
                            fontSize: '0.8em', 
                            color: '#888',
                            whiteSpace: 'nowrap'
                          }}>
                            {formatTime(d.timestamp)}
                          </span>
                        )}
                      </Typography>
                      <Typography 
                        variant="body2" 
                        sx={{ 
                          whiteSpace: 'pre-line',
                          mt: 0.5
                        }}
                      >
                        {d.text}
                      </Typography>
                    </Box>
                  </Box>
                ))}
              </Box>
            </Collapse>
          </Box>
        )}
        
        {hasResources && (
          <ResourcesDropdown resources={resources} />
        )}
      </Box>
      {/* Emoji Reaction Bar (only if canReact) */}
      {canReact && showReactions && (
        <div className="reaction-bar">
          {REACTION_EMOJIS.map((emoji) => (
            <span
              key={emoji}
              className={`reaction-emoji${reactions && reactions[emoji] ? ' reacted' : ''}`}
              onClick={() => onReact && onReact(emoji)}
            >
              {emoji} {reactions && reactions[emoji] ? reactions[emoji] : ''}
            </span>
          ))}
        </div>
      )}
      {/* Show selected reactions below bubble */}
      {reactions && Object.keys(reactions).length > 0 && (
        <div className="reaction-summary">
          {Object.entries(reactions).map(([emoji, count]) => (
            <span key={emoji} className="reaction-emoji reacted">{emoji} {count}</span>
          ))}
        </div>
      )}
    </Box>
  );
}

function App() {
  const [input, setInput] = useState('');
  const [chat, setChat] = useState([]); // [{from: 'user'|'bot', text, discussion, timestamp}]
  const [loading, setLoading] = useState(false);
  const [resourcesMap, setResourcesMap] = useState({});
  const [reactionsMap, setReactionsMap] = useState({}); // {uniqueKey: {emoji: count}}
  const [isBotTyping, setIsBotTyping] = useState(false);
  const [inputSuggestions, setInputSuggestions] = useState([]);
  const [showSuggestions, setShowSuggestions] = useState(false);
  const chatEndRef = useRef(null);

  useEffect(() => {
    axios.get('/history').then(res => {
      const history = res.data || [];
      const formatted = [];
      const resourcesMapTemp = {};
      history.forEach(item => {
        formatted.push({ from: 'user', text: item.user, timestamp: item.timestamp });
        formatted.push({ from: 'bot', text: item.final_answer, discussion: item.discussion, timestamp: item.timestamp });
        if (item.resources && item.timestamp) {
          resourcesMapTemp[item.timestamp] = item.resources;
        }
      });
      setChat(formatted);
      setResourcesMap(resourcesMapTemp);
    });
  }, []);

  useEffect(() => {
    if (chatEndRef.current) chatEndRef.current.scrollIntoView({ behavior: 'smooth' });
  }, [chat, loading]);

  const handleSend = async () => {
    if (!input.trim()) return;
    const ts = Date.now();
    setChat(prev => [...prev, { from: 'user', text: input, timestamp: ts, status: 'sent' }]);
    setLoading(true);
    setIsBotTyping(true);
    try {
      const res = await axios.post('/ask', { question: input });
      // Use backend's timestamp for both chat and resources
      const backendTimestamp = res.data.timestamp || Date.now();
      const botMessage = { 
        from: 'bot', 
        text: res.data.answer, 
        discussion: res.data.discussion, 
        timestamp: backendTimestamp, 
        status: 'delivered' 
      };
      setChat(prev => prev.map(m => m.timestamp === ts ? { ...m, status: 'delivered' } : m).concat(botMessage));
      if (res.data.resources && Array.isArray(res.data.resources) && res.data.resources.length > 0) {
        setResourcesMap(prev => ({ ...prev, [backendTimestamp]: res.data.resources }));
      }
      setInput('');
    } catch (e) {
      const errorTs = Date.now();
      setChat(prev => [
        ...prev,
        { from: 'bot', text: 'Error: ' + (e.response?.data?.detail || e.message), timestamp: errorTs, status: 'delivered' }
      ]);
    }
    setLoading(false);
    setIsBotTyping(false);
  };

  // Autocomplete suggestions based on input
  useEffect(() => {
    if (!input) {
      setInputSuggestions([]);
      setShowSuggestions(false);
      return;
    }
    const filtered = SUGGESTIONS.filter(s => s.toLowerCase().includes(input.toLowerCase()) && s.toLowerCase() !== input.toLowerCase());
    setInputSuggestions(filtered.slice(0, 3));
    setShowSuggestions(filtered.length > 0);
  }, [input]);

  const handleClearHistory = async () => {
    setLoading(true);
    try {
      await axios.delete('/history');
      setChat([]);
      setResourcesMap({});
    } catch (e) {
      console.error('Error clearing history:', e);
    }
    setLoading(false);
  };

  // Helper to get a unique key for each message
  const getMsgKey = (msg, idx) => `${msg.timestamp || ''}_${idx}`;

  // Add reaction handler (only for bot messages)
  const handleReact = (msg, msgKey, emoji) => {
    setReactionsMap(prev => {
      const prevMsg = prev[msgKey] || {};
      return {
        ...prev,
        [msgKey]: {
          ...prevMsg,
          [emoji]: (prevMsg[emoji] || 0) + 1
        }
      };
    });
    // Bot feedback logic
    let botFeedback = '';
    if (emoji === '👍' || emoji === '❤️' || emoji === '😂') {
      botFeedback = 'Thank you for your feedback! 😊';
    } else if (emoji === '👎' || emoji === '😢') {
      botFeedback = 'Sorry to hear that! Could you tell me what was wrong or how I can improve my answer?';
    } else if (emoji === '😮') {
      botFeedback = 'Surprised? Let me know if you want more details or clarification!';
    }
    if (botFeedback) {
      setChat(prev => [
        ...prev,
        { from: 'bot', text: botFeedback, timestamp: Date.now() }
      ]);
    }
  };

  return (
    <div className="App">
      <div className="chat-container">
        <div className="chat-window">
          <Box display="flex" justifyContent="flex-end" mb={1}>
            <IconButton 
              onClick={handleClearHistory} 
              title="Reset Chat"
              aria-label="Reset chat" 
              size="small" 
              disabled={loading}
              sx={{ 
                color: 'error.main',
                '&:hover': {
                  backgroundColor: 'error.light'
                }
              }}
            >
              <svg width="20" height="20" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                <path d="M19 6.41L17.59 5 12 10.59 6.41 5 5 6.41 10.59 12 5 17.59 6.41 19 12 13.41 17.59 19 19 17.59 13.41 12 19 6.41z" fill="currentColor"/>
              </svg>
            </IconButton>
          </Box>
          {chat.map((msg, idx) => {
            const msgKey = getMsgKey(msg, idx);
            const canReact = msg.from === 'bot';
            return (
              <ChatBubble
                key={msgKey}
                message={msg}
                isUser={msg.from === 'user'}
                discussion={msg.discussion}
                resources={msg.from === 'bot' ? resourcesMap[msg.timestamp] : undefined}
                onReact={canReact ? (emoji) => handleReact(msg, msgKey, emoji) : undefined}
                reactions={reactionsMap[msgKey]}
                canReact={canReact}
                status={msg.status}
              />
            );
          })}
          {isBotTyping && (
            <div className="chat-bubble bot typing-indicator">
              <span className="dot"></span><span className="dot"></span><span className="dot"></span>
              <span style={{marginLeft: 8, color: '#aaa'}}>Lexi is typing…</span>
            </div>
          )}
          {loading && (
            <div className="chat-bubble bot">
              <CircularProgress size={24} />
            </div>
          )}
          <div ref={chatEndRef} />
        </div>
        <div className="chat-input-row">
          <TextField
            className="chat-input"
            placeholder="Type your legal question..."
            value={input}
            onChange={e => setInput(e.target.value)}
            onKeyDown={e => {
              if (e.key === 'Enter' && !loading) handleSend();
              if (e.key === 'ArrowDown' && inputSuggestions.length > 0) {
                setInput(inputSuggestions[0]);
                setShowSuggestions(false);
              }
            }}
            disabled={loading}
            fullWidth
            InputProps={{
              style: {
                background: 'transparent',
                color: '#f5f5f7',
                borderRadius: 18,
                fontSize: '1.1em',
                padding: '12px 18px',
              }
            }}
            autoComplete="off"
          />
          <IconButton color="primary" onClick={handleSend} disabled={loading || !input.trim()}>
            <SendIcon />
          </IconButton>
        </div>
        {showSuggestions && (
          <div className="suggestions-dropdown">
            {inputSuggestions.map((s, i) => (
              <div key={i} className="suggestion-item" onClick={() => { setInput(s); setShowSuggestions(false); }}>
                {s}
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}

export default App;
