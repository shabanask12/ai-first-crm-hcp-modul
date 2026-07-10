import { configureStore, createSlice, createAsyncThunk } from '@reduxjs/toolkit';

const API_BASE_URL = 'http://localhost:8000/api';

// ----------------------------------------------------
// Thunks for API calls
// ----------------------------------------------------

export const fetchHCPs = createAsyncThunk('crm/fetchHCPs', async (query = '') => {
  const url = query ? `${API_BASE_URL}/hcps?q=${encodeURIComponent(query)}` : `${API_BASE_URL}/hcps`;
  const response = await fetch(url);
  return await response.json();
});

export const fetchProducts = createAsyncThunk('crm/fetchProducts', async () => {
  const response = await fetch(`${API_BASE_URL}/products`);
  return await response.json();
});

export const fetchInteractions = createAsyncThunk('crm/fetchInteractions', async () => {
  const response = await fetch(`${API_BASE_URL}/interactions`);
  return await response.json();
});

export const saveInteraction = createAsyncThunk('crm/saveInteraction', async ({ id, data }, { dispatch }) => {
  const method = id ? 'PUT' : 'POST';
  const url = id ? `${API_BASE_URL}/interactions/${id}` : `${API_BASE_URL}/interactions`;
  const response = await fetch(url, {
    method,
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(data),
  });
  const result = await response.json();
  dispatch(fetchInteractions());
  return result;
});

export const sendChatMessage = createAsyncThunk(
  'crm/sendChatMessage',
  async ({ messageText, history, formDraft, currentHcpId, currentInteractionId }, { dispatch }) => {
    // Construct request message history
    const payloadMessages = [
      ...history,
      { sender: 'user', text: messageText }
    ];
    
    const response = await fetch(`${API_BASE_URL}/chat`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        messages: payloadMessages,
        form_draft: formDraft,
        current_hcp_id: currentHcpId,
        current_interaction_id: currentInteractionId
      }),
    });
    
    if (!response.ok) {
      const errData = await response.json();
      throw new Error(errData.detail || 'Server error');
    }
    
    const data = await response.json();
    return data; // contains messages, form_draft, current_hcp_id, current_interaction_id
  }
);

export const summarizeVoiceNoteText = createAsyncThunk(
  'crm/summarizeVoice',
  async (transcript) => {
    const response = await fetch(`${API_BASE_URL}/voice-summarize`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ transcript }),
    });
    const data = await response.json();
    return data.summary;
  }
);

// ----------------------------------------------------
// Slice definition
// ----------------------------------------------------

const getEmptyDraft = () => ({
  hcp_id: null,
  hcp_name: '',
  type: 'Meeting',
  date: new Date().toISOString().split('T')[0],
  time: new Date().toLocaleTimeString('en-US', { hour12: false, hour: '2-digit', minute: '2-digit' }),
  attendees: '',
  topics: '',
  sentiment: 'Neutral',
  outcomes: '',
  follow_ups: '',
  material_ids: []
});

const crmSlice = createSlice({
  name: 'crm',
  initialState: {
    formDraft: getEmptyDraft(),
    currentHcpId: null,
    currentInteractionId: null,
    chatHistory: [
      { sender: 'ai', text: "Hello! I am your AI CRM Assistant. You can describe your HCP interaction here, and I'll extract the details, update the form, and log it to the database for you." }
    ],
    hcps: [],
    products: [],
    interactions: [],
    status: {
      hcps: 'idle',
      products: 'idle',
      interactions: 'idle',
      chat: 'idle',
      voice: 'idle'
    },
    error: null
  },
  reducers: {
    updateFormField: (state, action) => {
      const { field, value } = action.payload;
      state.formDraft[field] = value;
      if (field === 'hcp_id') {
        state.currentHcpId = value;
        const selected = state.hcps.find(h => h.id === value);
        state.formDraft.hcp_name = selected ? selected.name : '';
      }
    },
    clearForm: (state) => {
      state.formDraft = getEmptyDraft();
      state.currentHcpId = null;
      state.currentInteractionId = null;
    },
    loadDraftIntoForm: (state, action) => {
      const interaction = action.payload;
      state.currentInteractionId = interaction.id;
      state.currentHcpId = interaction.hcp_id;
      state.formDraft = {
        hcp_id: interaction.hcp_id,
        hcp_name: interaction.hcp_name,
        type: interaction.type,
        date: interaction.date,
        time: interaction.time,
        attendees: interaction.attendees,
        topics: interaction.topics,
        sentiment: interaction.sentiment,
        outcomes: interaction.outcomes,
        follow_ups: interaction.follow_ups,
        material_ids: interaction.materials.map(m => m.id)
      };
    },
    addManualUserMessage: (state, action) => {
      state.chatHistory.push({ sender: 'user', text: action.payload });
    }
  },
  extraReducers: (builder) => {
    builder
      // Fetch HCPs
      .addCase(fetchHCPs.pending, (state) => { state.status.hcps = 'loading'; })
      .addCase(fetchHCPs.fulfilled, (state, action) => {
        state.status.hcps = 'succeeded';
        state.hcps = action.payload;
      })
      // Fetch Products
      .addCase(fetchProducts.fulfilled, (state, action) => {
        state.status.products = 'succeeded';
        state.products = action.payload;
      })
      // Fetch Interactions
      .addCase(fetchInteractions.fulfilled, (state, action) => {
        state.status.interactions = 'succeeded';
        state.interactions = action.payload;
      })
      // Save Interaction
      .addCase(saveInteraction.fulfilled, (state) => {
        state.formDraft = getEmptyDraft();
        state.currentHcpId = null;
        state.currentInteractionId = null;
      })
      // Chat
      .addCase(sendChatMessage.pending, (state, action) => {
        state.status.chat = 'loading';
        state.chatHistory.push({ sender: 'user', text: action.meta.arg.messageText });
      })
      .addCase(sendChatMessage.fulfilled, (state, action) => {
        state.status.chat = 'succeeded';
        state.chatHistory = action.payload.messages;
        state.formDraft = {
          ...state.formDraft,
          ...action.payload.form_draft
        };
        state.currentHcpId = action.payload.current_hcp_id;
        state.currentInteractionId = action.payload.current_interaction_id;
      })
      .addCase(sendChatMessage.rejected, (state, action) => {
        state.status.chat = 'failed';
        const errorMsg = action.error?.message || "Please check that your backend is running and GROQ_API_KEY is configured.";
        state.chatHistory.push({ sender: 'ai', text: `Sorry, I encountered an issue: ${errorMsg}` });
      })
      // Voice Summarizer
      .addCase(summarizeVoiceNoteText.pending, (state) => { state.status.voice = 'loading'; })
      .addCase(summarizeVoiceNoteText.fulfilled, (state, action) => {
        state.status.voice = 'succeeded';
        state.formDraft.topics = action.payload;
      })
      .addCase(summarizeVoiceNoteText.rejected, (state) => {
        state.status.voice = 'failed';
      });
  }
});

export const { updateFormField, clearForm, loadDraftIntoForm, addManualUserMessage } = crmSlice.actions;

export const store = configureStore({
  reducer: {
    crm: crmSlice.reducer
  }
});
