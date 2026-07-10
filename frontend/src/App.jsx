import React, { useEffect, useState, useRef } from 'react';
import { useDispatch, useSelector } from 'react-redux';
import {
  fetchHCPs,
  fetchProducts,
  fetchInteractions,
  saveInteraction,
  sendChatMessage,
  updateFormField,
  clearForm,
  loadDraftIntoForm,
  summarizeVoiceNoteText
} from './store';
import {
  Send,
  Mic,
  Activity,
  User,
  Plus,
  RefreshCw,
  FileText,
  Calendar,
  Clock,
  MessageSquare,
  TrendingUp,
  UserCheck,
  Award,
  Sparkles,
  Bot
} from 'lucide-react';

const SIMULATED_VOICE_NOTES = [
  "Met Dr. John Smith today. We discussed the CardioShield patient samples. He was very positive about the efficacy but requested 2 more sample kits next month. I promised to follow up on this.",
  "I had a Zoom call with Dr. Alice Sharma regarding the OncoBoost Phase III trial data. She seemed extremely engaged and positive about the lung cancer survivability statistics. She requested the clinical report PDF to share with her advisory board.",
  "Emailed Dr. Sarah Jenkins about the EndoBalance diabetes educational materials. She responded with neutral interest and asked if there is a Spanish version of the brochure."
];

function App() {
  const dispatch = useDispatch();
  const {
    formDraft,
    currentHcpId,
    currentInteractionId,
    chatHistory,
    hcps,
    products,
    interactions,
    status
  } = useSelector((state) => state.crm);

  const [chatInput, setChatInput] = useState('');
  const [voiceTranscriptSelect, setVoiceTranscriptSelect] = useState('');
  const [isSimulatingVoice, setIsSimulatingVoice] = useState(false);
  const chatEndRef = useRef(null);

  // Initialize data on mount
  useEffect(() => {
    dispatch(fetchHCPs());
    dispatch(fetchProducts());
    dispatch(fetchInteractions());
  }, [dispatch]);

  // Scroll to bottom of chat when new messages arrive
  useEffect(() => {
    chatEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [chatHistory, status.chat]);

  const handleInputChange = (field, value) => {
    dispatch(updateFormField({ field, value }));
  };

  const handleMaterialToggle = (materialId) => {
    const currentList = formDraft.material_ids || [];
    let newList;
    if (currentList.includes(materialId)) {
      newList = currentList.filter(id => id !== materialId);
    } else {
      newList = [...currentList, materialId];
    }
    handleInputChange('material_ids', newList);
  };

  const handleFormSubmit = (e) => {
    e.preventDefault();
    if (!formDraft.hcp_id) {
      alert('Please select a Healthcare Professional (HCP).');
      return;
    }
    const payload = {
      hcp_id: formDraft.hcp_id,
      date: formDraft.date,
      time: formDraft.time,
      type: formDraft.type,
      attendees: formDraft.attendees,
      topics: formDraft.topics,
      sentiment: formDraft.sentiment,
      outcomes: formDraft.outcomes,
      follow_ups: formDraft.follow_ups,
      material_ids: formDraft.material_ids
    };

    dispatch(saveInteraction({ id: currentInteractionId, data: payload }))
      .unwrap()
      .then((res) => {
        alert(currentInteractionId ? 'Interaction updated successfully!' : 'Interaction logged successfully!');
      })
      .catch((err) => {
        console.error(err);
        alert('Failed to save interaction.');
      });
  };

  const handleChatSend = (e) => {
    e.preventDefault();
    if (!chatInput.trim()) return;

    const messageText = chatInput;
    setChatInput('');

    // Trigger LangGraph chat agent
    dispatch(sendChatMessage({
      messageText,
      history: chatHistory,
      formDraft,
      currentHcpId,
      currentInteractionId
    }));
  };

  const handleQuickPrompt = (promptText) => {
    dispatch(sendChatMessage({
      messageText: promptText,
      history: chatHistory,
      formDraft,
      currentHcpId,
      currentInteractionId
    }));
  };

  const handleVoiceSummarize = () => {
    if (!voiceTranscriptSelect) {
      alert('Please select a simulated voice transcription first.');
      return;
    }
    setIsSimulatingVoice(true);
    dispatch(summarizeVoiceNoteText(voiceTranscriptSelect))
      .unwrap()
      .then(() => {
        setIsSimulatingVoice(false);
      })
      .catch(() => {
        setIsSimulatingVoice(false);
        alert('Failed to summarize voice note. Ensure GROQ_API_KEY is configured.');
      });
  };

  const handleLoadDraft = (interaction) => {
    dispatch(loadDraftIntoForm(interaction));
  };

  const handleClear = () => {
    dispatch(clearForm());
  };

  return (
    <div className="app-container">
      {/* Header */}
      <header className="app-header">
        <div className="brand">
          <div className="brand-logo">Ω</div>
          <div>
            <h1 className="brand-title">Aegis AI-First CRM</h1>
            <p style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>HCP Module • Interaction Center</p>
          </div>
        </div>
        <div className="header-status">
          <div className="status-badge">
            <span className="status-dot"></span>
            <span>FastAPI Server Active</span>
          </div>
          <div className="status-badge">
            <Sparkles size={14} style={{ color: 'var(--primary-hover)' }} />
            <span>Gemma 2 9B Connected</span>
          </div>
        </div>
      </header>

      {/* Main Workspace Layout */}
      <div className="workspace-grid">
        
        {/* Left Column: Form Panel */}
        <section className="panel">
          <div className="panel-header">
            <h2 className="panel-title">
              <Activity size={18} style={{ color: 'var(--primary)' }} />
              {currentInteractionId ? 'Edit HCP Interaction' : 'Log HCP Interaction'}
            </h2>
            <div style={{ display: 'flex', gap: '0.5rem' }}>
              {currentInteractionId && (
                <span className="status-badge" style={{ borderColor: 'var(--warning)', color: 'var(--warning)' }}>
                  Editing ID #{currentInteractionId}
                </span>
              )}
              <button className="btn voice-note-btn" style={{ margin: 0 }} onClick={handleClear}>
                Reset Form
              </button>
            </div>
          </div>
          
          <form className="panel-body form-grid" onSubmit={handleFormSubmit}>
            
            {/* HCP Name Selection */}
            <div className="form-group">
              <label className="form-label">HCP Name</label>
              <select
                className="form-select"
                value={formDraft.hcp_id || ''}
                onChange={(e) => handleInputChange('hcp_id', e.target.value ? Number(e.target.value) : null)}
                required
              >
                <option value="">Search or select HCP...</option>
                {hcps.map(h => (
                  <option key={h.id} value={h.id}>
                    {h.name} ({h.specialty} - {h.hospital})
                  </option>
                ))}
              </select>
            </div>

            {/* Interaction Type Selection */}
            <div className="form-group">
              <label className="form-label">Interaction Type</label>
              <select
                className="form-select"
                value={formDraft.type}
                onChange={(e) => handleInputChange('type', e.target.value)}
              >
                <option value="Meeting">Meeting</option>
                <option value="Call">Call</option>
                <option value="Email">Email</option>
                <option value="Conference">Conference</option>
              </select>
            </div>

            {/* Date Picker */}
            <div className="form-group">
              <label className="form-label">
                <Calendar size={14} style={{ marginRight: '4px', verticalAlign: 'text-bottom' }} />
                Date
              </label>
              <input
                type="date"
                className="form-input"
                value={formDraft.date}
                onChange={(e) => handleInputChange('date', e.target.value)}
                required
              />
            </div>

            {/* Time Picker */}
            <div className="form-group">
              <label className="form-label">
                <Clock size={14} style={{ marginRight: '4px', verticalAlign: 'text-bottom' }} />
                Time
              </label>
              <input
                type="time"
                className="form-input"
                value={formDraft.time}
                onChange={(e) => handleInputChange('time', e.target.value)}
                required
              />
            </div>

            {/* Attendees input */}
            <div className="form-group-full">
              <label className="form-label">Attendees</label>
              <input
                type="text"
                placeholder="Enter names separated by commas (e.g. Dr. Alice Sharma, Rep Alex)..."
                className="form-input"
                value={formDraft.attendees || ''}
                onChange={(e) => handleInputChange('attendees', e.target.value)}
              />
            </div>

            {/* Topics Discussed */}
            <div className="form-group-full">
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                <label className="form-label">Topics Discussed</label>
                <span style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>Voice Summary Supported</span>
              </div>
              
              {/* Simulated Voice Input Section */}
              <div style={{ display: 'flex', gap: '0.5rem', marginBottom: '0.75rem' }}>
                <select
                  className="form-select"
                  style={{ flex: 1, padding: '0.4rem', fontSize: '0.8rem' }}
                  value={voiceTranscriptSelect}
                  onChange={(e) => setVoiceTranscriptSelect(e.target.value)}
                >
                  <option value="">Select voice note transcript simulation...</option>
                  {SIMULATED_VOICE_NOTES.map((note, idx) => (
                    <option key={idx} value={note}>
                      Transcript #{idx + 1}: {note.slice(0, 50)}...
                    </option>
                  ))}
                </select>
                <button
                  type="button"
                  onClick={handleVoiceSummarize}
                  disabled={status.voice === 'loading' || !voiceTranscriptSelect}
                  className={`voice-note-btn ${status.voice === 'loading' ? 'listening' : ''}`}
                  style={{ margin: 0, padding: '0.4rem 0.8rem' }}
                >
                  <Mic size={14} />
                  {status.voice === 'loading' ? 'AI Summarizing...' : 'Summarize Voice'}
                </button>
              </div>

              <textarea
                placeholder="Enter key discussion points discussed with the HCP..."
                className="form-textarea"
                value={formDraft.topics || ''}
                onChange={(e) => handleInputChange('topics', e.target.value)}
                required
              />
            </div>

            {/* Materials Shared Checkboxes */}
            <div className="form-group-full">
              <label className="form-label">Materials Shared & Samples Distributed</label>
              <div className="materials-list">
                {products.map(p => (
                  <label key={p.id} className="material-item">
                    <input
                      type="checkbox"
                      checked={(formDraft.material_ids || []).includes(p.id)}
                      onChange={() => handleMaterialToggle(p.id)}
                    />
                    <span>{p.name}</span>
                    <span className="material-badge">{p.material_type} (Stock: {p.stock})</span>
                  </label>
                ))}
              </div>
            </div>

            {/* Observed/Inferred HCP Sentiment */}
            <div className="form-group-full">
              <label className="form-label">Observed/Inferred HCP Sentiment</label>
              <div className="sentiment-group">
                {['Positive', 'Neutral', 'Negative'].map((sent) => (
                  <label
                    key={sent}
                    className={`sentiment-radio ${sent.toLowerCase()} ${formDraft.sentiment === sent ? 'checked' : ''}`}
                  >
                    <input
                      type="radio"
                      name="sentiment"
                      value={sent}
                      checked={formDraft.sentiment === sent}
                      onChange={() => handleInputChange('sentiment', sent)}
                    />
                    <span>{sent === 'Positive' ? '🟢' : sent === 'Neutral' ? '🟡' : '🔴'}</span>
                    <span>{sent}</span>
                  </label>
                ))}
              </div>
            </div>

            {/* Outcomes */}
            <div className="form-group-full">
              <label className="form-label">Outcomes</label>
              <textarea
                placeholder="Key outcomes, requests, or agreements..."
                className="form-textarea"
                value={formDraft.outcomes || ''}
                onChange={(e) => handleInputChange('outcomes', e.target.value)}
              />
            </div>

            {/* Follow-up Actions */}
            <div className="form-group-full">
              <label className="form-label">Follow-up Actions</label>
              <textarea
                placeholder="Enter next steps, scheduled tasks, or material delivery..."
                className="form-textarea"
                value={formDraft.follow_ups || ''}
                onChange={(e) => handleInputChange('follow_ups', e.target.value)}
              />
              
              {/* Suggestion Chips */}
              <div style={{ marginTop: '0.75rem' }}>
                <span className="form-label" style={{ fontSize: '0.75rem' }}>AI Suggested Follow-ups:</span>
                <div className="suggestions-list">
                  <div
                    className="suggestion-chip"
                    onClick={() => handleInputChange('follow_ups', (formDraft.follow_ups ? formDraft.follow_ups + '\n' : '') + '• Schedule follow-up meeting in 2 weeks')}
                  >
                    + Schedule follow-up meeting in 2 weeks
                  </div>
                  <div
                    className="suggestion-chip"
                    onClick={() => handleInputChange('follow_ups', (formDraft.follow_ups ? formDraft.follow_ups + '\n' : '') + '• Send OncoBoost Phase III PDF')}
                  >
                    + Send OncoBoost Phase III PDF
                  </div>
                  <div
                    className="suggestion-chip"
                    onClick={() => handleInputChange('follow_ups', (formDraft.follow_ups ? formDraft.follow_ups + '\n' : '') + '• Add Dr. Sharma to advisory board invite list')}
                  >
                    + Add Dr. Sharma to advisory board invite list
                  </div>
                </div>
              </div>
            </div>

            {/* Submit Action buttons */}
            <div className="form-actions form-group-full">
              <button type="submit" className="btn btn-primary">
                <UserCheck size={18} />
                {currentInteractionId ? 'Update Interaction Logs' : 'Log HCP Interaction'}
              </button>
            </div>

          </form>
        </section>

        {/* Right Column: AI Assistant Chat Panel */}
        <section className="panel">
          <div className="panel-header">
            <h2 className="panel-title">
              <Bot size={18} style={{ color: 'var(--accent)' }} />
              AI CRM Assistant
            </h2>
            <span className="status-badge" style={{ textTransform: 'uppercase', fontSize: '0.7rem' }}>
              LangGraph Agent
            </span>
          </div>

          <div className="chat-container">
            {/* Chat Messages Log */}
            <div className="chat-history">
              {chatHistory.map((msg, index) => (
                <div key={index} className={`chat-message ${msg.sender}`}>
                  <p style={{ fontWeight: 600, fontSize: '0.75rem', marginBottom: '0.25rem', opacity: 0.8 }}>
                    {msg.sender === 'user' ? 'Rep Alex' : 'AI Assistant'}
                  </p>
                  <div style={{ whiteSpace: 'pre-line' }}>{msg.text}</div>
                </div>
              ))}

              {/* Loader indicator while LLM runs */}
              {status.chat === 'loading' && (
                <div className="chat-message ai">
                  <div className="typing-indicator">
                    <div className="typing-dot"></div>
                    <div className="typing-dot"></div>
                    <div className="typing-dot"></div>
                  </div>
                </div>
              )}
              <div ref={chatEndRef} />
            </div>

            {/* Quick Actions Prompts */}
            <div style={{ padding: '0.75rem 1rem', background: 'rgba(0, 0, 0, 0.2)', borderLeft: '1px solid var(--panel-border)', borderRight: '1px solid var(--panel-border)' }}>
              <span className="form-label" style={{ fontSize: '0.7rem', marginBottom: '0.4rem' }}>Quick AI Actions:</span>
              <div className="suggestions-list">
                <div
                  className="suggestion-chip"
                  onClick={() => handleQuickPrompt("Search for a cardiologist")}
                >
                  "Find cardiologists"
                </div>
                <div
                  className="suggestion-chip"
                  style={{ color: '#818cf8' }}
                  onClick={() => handleQuickPrompt("I met with Dr. Alice Sharma today at 2:00 PM. We discussed the OncoBoost clinical trial. She was very positive about it and requested the report. Set outcomes to: Wants clinical trial report.")}
                >
                  "Log meeting with Dr. Alice Sharma..."
                </div>
                <div
                  className="suggestion-chip"
                  onClick={() => handleQuickPrompt("Suggest follow up task for Alice Sharma to send report")}
                >
                  "Create follow up task..."
                </div>
              </div>
            </div>

            {/* Message input bar */}
            <form className="chat-input-bar" onSubmit={handleChatSend}>
              <input
                type="text"
                placeholder="Describe interaction or ask agent..."
                className="chat-input"
                value={chatInput}
                onChange={(e) => setChatInput(e.target.value)}
                disabled={status.chat === 'loading'}
              />
              <button
                type="submit"
                className="chat-send-btn"
                disabled={status.chat === 'loading' || !chatInput.trim()}
              >
                <Send size={18} />
              </button>
            </form>
          </div>
        </section>

      </div>

      {/* Lower Section: DB History List Table */}
      <section className="history-section">
        <h2 className="history-title">
          <Award size={18} style={{ color: 'var(--primary)' }} />
          Database Logged HCP Interactions History
        </h2>
        <div className="history-table-wrapper">
          <table className="history-table">
            <thead>
              <tr>
                <th>ID</th>
                <th>HCP Name</th>
                <th>Type</th>
                <th>Date & Time</th>
                <th>Attendees</th>
                <th>Topics</th>
                <th>Sentiment</th>
                <th>Shared Materials</th>
                <th>Actions</th>
              </tr>
            </thead>
            <tbody>
              {interactions.map((i) => (
                <tr key={i.id} className="history-row" onClick={() => handleLoadDraft(i)}>
                  <td style={{ fontWeight: 'bold' }}>#{i.id}</td>
                  <td>{i.hcp_name}</td>
                  <td>
                    <span style={{
                      padding: '0.2rem 0.5rem',
                      borderRadius: '4px',
                      fontSize: '0.75rem',
                      background: i.type === 'Meeting' ? 'rgba(99, 102, 241, 0.15)' : 'rgba(13, 148, 136, 0.15)',
                      color: i.type === 'Meeting' ? 'var(--accent-hover)' : 'var(--primary-hover)'
                    }}>
                      {i.type}
                    </span>
                  </td>
                  <td>{i.date} {i.time}</td>
                  <td>{i.attendees || '-'}</td>
                  <td style={{ maxWidth: '250px', whiteSpace: 'nowrap', overflow: 'hidden', textOverflow: 'ellipsis' }}>
                    {i.topics || '-'}
                  </td>
                  <td>
                    <span className={`sentiment-pill ${i.sentiment.toLowerCase()}`}>
                      {i.sentiment}
                    </span>
                  </td>
                  <td>
                    {i.materials.length > 0
                      ? i.materials.map(m => m.name).join(', ')
                      : '-'
                    }
                  </td>
                  <td>
                    <button
                      type="button"
                      className="btn"
                      style={{ padding: '0.2rem 0.6rem', fontSize: '0.75rem', background: 'rgba(255, 255, 255, 0.05)', border: '1px solid var(--panel-border)', display: 'inline-block' }}
                      onClick={(e) => {
                        e.stopPropagation();
                        handleLoadDraft(i);
                      }}
                    >
                      Load to Edit
                    </button>
                  </td>
                </tr>
              ))}
              {interactions.length === 0 && (
                <tr>
                  <td colSpan="9" style={{ textAlign: 'center', padding: '2rem', color: 'var(--text-muted)' }}>
                    No interactions logged in the database yet. Use the form or chat assistant to log one!
                  </td>
                </tr>
              )}
            </tbody>
          </table>
        </div>
      </section>
    </div>
  );
}

export default App;
