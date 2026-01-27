// API Configuration - Works when served as static template in Flask
const API_BASE_URL = window.location.origin;
const API_ENDPOINT = `${API_BASE_URL}/chat`;

// Hardcoded for now, or match what you use in Postman
const USER_ID = "guest_user";
const LICENSE_ID = "guest_license";

const chatHistory = document.getElementById("chatHistory");
const messageInput = document.getElementById("messageInput");
const actions = document.getElementById("actions");
const welcomeContent = document.getElementById("welcomeContent");
const sidebar = document.getElementById("sidebar");
const sendBtn = document.getElementById("sendBtn");
const imageModal = document.getElementById("imageModal");
const modalImage = document.getElementById("modalImage");
const confirmModal = document.getElementById("confirmModal");
const confirmDeleteBtn = document.getElementById("confirmDeleteBtn");
// Voice Integration Elements
const voiceBtn = document.getElementById("voiceBtn");
const recordingTimer = document.getElementById("recordingTimer");

// Local in-memory conversation + last tutorial store
let chatStateHistory = []; // stores "User: ..." and "Assistant: ..." strings
let lastTutorialSteps = []; // stores last tutorial steps array returned from backend
let currentSessionId = null;
let isFirstLoad = true;

function toggleSidebar() {
  sidebar.classList.toggle("collapsed");
}

function selectAction(action) {
  const actionTexts = {
    region: "How to add a new region?",
    area: "How to create a new area?",
    territory: "How to add a new territory?",
    distributor: "How to create a distributor?",
    section: "How to add a new section?",
    sector: "How to setup a new sector?",
  };
  messageInput.value = actionTexts[action];
  sendMessage();
}

// Fetch and display sessions on load
async function fetchSessions() {
  try {
    const response = await fetch(`${API_BASE_URL}/sessions?user_id=${USER_ID}`);
    const data = await response.json();
    displaySessions(data.sessions);

    // Session Restoration Logic (Scalable Client-Side)
    // Check if we have an active session in this specific tab/window
    const activeSessionId = sessionStorage.getItem("activeSessionId");

    if (isFirstLoad) {
      if (activeSessionId) {
        // CASE 1: Page Reload - Restore the active session
        // Verify it still exists in the fetched list (in case it was deleted elsewhere)
        const sessionExists = data.sessions.some(
          (s) => s.session_id === activeSessionId,
        );

        if (sessionExists) {
          selectSession(activeSessionId);
        } else {
          // Session ID in storage but not on server (maybe deleted or expired)
          sessionStorage.removeItem("activeSessionId");
          newChat();
        }
      } else {
        // CASE 2: New Tab/Visit - Always start with a fresh landing page
        // Do NOT auto-select the latest session
        newChat();
      }
      isFirstLoad = false;
    }
  } catch (err) {
    console.error("Error fetching sessions:", err);
  }
}

function displaySessions(sessions) {
  const sidebarContent = document.getElementById("sidebarContent");
  sidebarContent.innerHTML = "";

  if (!sessions || sessions.length === 0) {
    sidebarContent.innerHTML = '<div class="history-label">No chats yet</div>';
    return;
  }

  const section = document.createElement("div");
  section.className = "history-section";
  section.innerHTML = '<div class="history-label">Recent Chats</div>';

  sessions.forEach((session) => {
    const item = document.createElement("div");
    item.className = `history-item ${
      session.session_id === currentSessionId ? "active" : ""
    }`;
    item.style.fontWeight =
      session.session_id === currentSessionId ? "600" : "normal";
    item.style.background =
      session.session_id === currentSessionId ? "#f0f0f0" : "transparent";

    const titleSpan = document.createElement("span");
    titleSpan.className = "session-title";
    titleSpan.textContent = session.title || "Untitled Chat";
    titleSpan.style.flex = "1";
    titleSpan.style.overflow = "hidden";
    titleSpan.style.textOverflow = "ellipsis";

    item.appendChild(titleSpan);
    item.onclick = (e) => {
      // Prevent selection if clicking on actions
      if (!e.target.closest(".session-actions")) {
        selectSession(session.session_id);
      }
    };

    const actionsDiv = document.createElement("div");
    actionsDiv.className = "session-actions";

    const editBtn = document.createElement("button");
    editBtn.className = "session-action-btn rename";
    editBtn.innerHTML = '<i class="fas fa-edit"></i>';
    editBtn.onclick = (e) => {
      e.stopPropagation();
      renameSession(session.session_id, session.title);
    };

    const deleteBtn = document.createElement("button");
    deleteBtn.className = "session-action-btn delete";
    deleteBtn.innerHTML = '<i class="fas fa-trash"></i>';
    deleteBtn.onclick = (e) => {
      e.stopPropagation();
      deleteSession(session.session_id);
    };

    actionsDiv.appendChild(editBtn);
    actionsDiv.appendChild(deleteBtn);
    item.appendChild(actionsDiv);

    section.appendChild(item);
  });

  sidebarContent.appendChild(section);
}

async function selectSession(sessionId) {
  if (currentSessionId === sessionId) return;
  currentSessionId = sessionId;

  // Persist active session to sessionStorage (survives reload, clears on close)
  sessionStorage.setItem("activeSessionId", sessionId);

  // Update UI
  fetchSessions(); // Refresh list to show active state

  try {
    const response = await fetch(`${API_BASE_URL}/sessions/${sessionId}`);
    if (!response.ok) throw new Error("Failed to load session");

    const data = await response.json();

    // Clear and load history
    chatHistory.innerHTML = "";
    chatStateHistory = data.history || [];
    lastTutorialSteps = []; // Reset steps for new session (backend will re-detect if needed)

    if (chatStateHistory.length > 0) {
      welcomeContent.classList.add("hidden");
      actions.classList.add("hidden");
      chatHistory.classList.add("active");

      // Re-render whole history with rich data (no animation)
      chatStateHistory.forEach((msg) => {
        if (typeof msg === "string") {
          // Fallback for old string-based history
          if (msg.startsWith("User: ")) {
            addMessage(msg.replace("User: ", ""), true, null, false);
          } else if (msg.startsWith("Assistant: ")) {
            addMessage(msg.replace("Assistant: ", ""), false, null, false);
          }
        } else if (typeof msg === "object" && msg !== null) {
          if (msg.role === "user") {
            addMessage(msg.content, true, null, false);
          } else if (msg.role === "assistant") {
            // Pass the full data object for rich rendering
            addMessage("", false, msg.data || { content: msg.content }, false);
          }
        }
      });
    } else {
      // New chat state
      welcomeContent.classList.remove("hidden");
      actions.classList.remove("hidden");
      chatHistory.classList.remove("active");
    }
  } catch (err) {
    console.error("Error selecting session:", err);
  }
}

function newChat() {
  currentSessionId = null;
  // Clear persistence so next reload shows landing page (until a new message starts a session)
  sessionStorage.removeItem("activeSessionId");

  chatHistory.innerHTML = "";
  chatStateHistory = [];
  lastTutorialSteps = [];

  chatHistory.classList.remove("active");
  welcomeContent.classList.remove("hidden");
  actions.classList.remove("hidden");
  messageInput.value = "";
  auto_resize();

  fetchSessions();
}

let sessionToDelete = null;

function deleteSession(sessionId) {
  sessionToDelete = sessionId;
  confirmModal.classList.add("active");
}

function closeConfirmModal() {
  confirmModal.classList.remove("active");
  sessionToDelete = null;
}

confirmDeleteBtn.onclick = async () => {
  if (!sessionToDelete) return;

  const sessionId = sessionToDelete;
  closeConfirmModal();

  try {
    const response = await fetch(`${API_BASE_URL}/sessions/${sessionId}`, {
      method: "DELETE",
    });

    if (response.ok) {
      if (currentSessionId === sessionId) {
        currentSessionId = null;
        newChat();
      } else {
        fetchSessions();
      }
    }
  } catch (err) {
    console.error("Error deleting session:", err);
  }
};

async function renameSession(sessionId, currentTitle) {
  const newTitle = prompt("Enter new chat title:", currentTitle);
  if (!newTitle || newTitle === currentTitle) return;

  try {
    const response = await fetch(`${API_BASE_URL}/sessions/${sessionId}`, {
      method: "PUT",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ title: newTitle }),
    });

    if (response.ok) {
      fetchSessions();
    }
  } catch (err) {
    console.error("Error renaming session:", err);
  }
}

// Image Modal Functions
function openImageModal(imgSrc) {
  modalImage.src = imgSrc;
  imageModal.classList.add("active");
  document.body.style.overflow = "hidden";
}

function closeImageModal() {
  imageModal.classList.remove("active");
  document.body.style.overflow = "";
}

imageModal.addEventListener("click", function (e) {
  if (e.target === imageModal) closeImageModal();
});

document.addEventListener("keydown", function (e) {
  if (e.key === "Escape" && imageModal.classList.contains("active")) {
    closeImageModal();
  }
});

function addMessage(text, isUser, responseData = null, animate = true) {
  chatHistory.classList.add("active");
  if (chatHistory.children.length === 0) {
    welcomeContent.classList.add("hidden");
    actions.classList.add("hidden");
  }

  const messageDiv = document.createElement("div");
  messageDiv.className = `message ${isUser ? "user" : "assistant"}`;

  const avatarDiv = document.createElement("div");
  avatarDiv.className = "message-avatar";
  avatarDiv.textContent = isUser ? "U" : "AI";

  const contentDiv = document.createElement("div");
  contentDiv.className = "message-content";

  messageDiv.appendChild(avatarDiv);
  messageDiv.appendChild(contentDiv);
  chatHistory.appendChild(messageDiv);

  if (isUser) {
    contentDiv.textContent = text;
    scrollToBottom();
  } else {
    // Assistant Message
    contentDiv.classList.add("markdown-content");

    // 1. Determine Text Content vs. Complex Content
    let textToType = "";
    let complexHtml = "";

    if (responseData) {
      // Extract main text based on type
      textToType = responseData.content || "";

      // Render the REST of the content (complex parts)
      const dataForRender = { ...responseData, content: null };

      if (responseData.type === "tutorial") {
        complexHtml = renderTutorialResponse(dataForRender);
      } else if (responseData.type === "tutorial_clarify") {
        complexHtml = renderTutorialClarifyResponse(dataForRender);
      } else if (responseData.type === "capabilities") {
        complexHtml = renderCapabilitiesResponse(dataForRender);
      } else {
        complexHtml = renderRegularResponse(dataForRender);
      }
    } else {
      textToType = text;
    }

    if (animate) {
      // 2. Start Typing Animation
      if (textToType) {
        typeWriter(contentDiv, textToType, () => {
          // 3. After typing, append Complex Content
          if (complexHtml) {
            const complexDiv = document.createElement("div");
            complexDiv.innerHTML = complexHtml;
            complexDiv.className = "fade-in"; // Add animation class
            contentDiv.appendChild(complexDiv);
            attachEventListeners(complexDiv); // Re-attach listeners to new elements
          }
          scrollToBottom();
        });
      } else if (complexHtml) {
        // No text, just complex content
        contentDiv.innerHTML = complexHtml;
        contentDiv.classList.add("fade-in");
        attachEventListeners(contentDiv);
        scrollToBottom();
      }
    } else {
      // 2. Instant Rendering (No animation)
      if (textToType) {
        const tempDiv = document.createElement("div");
        tempDiv.innerHTML = marked.parse(textToType);
        while (tempDiv.firstChild) {
          contentDiv.appendChild(tempDiv.firstChild);
        }
      }
      if (complexHtml) {
        const complexDiv = document.createElement("div");
        complexDiv.innerHTML = complexHtml;
        contentDiv.appendChild(complexDiv);
        attachEventListeners(complexDiv);
      }
      scrollToBottom();
    }
  }
}

// Typewriter Effect Function
function typeWriter(element, text, callback) {
  let i = 0;
  const speed = 30; // ms per char (slower for aesthetics)
  const step = 1; // 1 char per frame (smoother)

  // Create a temporary container for the typing text
  const textContainer = document.createElement("div");
  element.appendChild(textContainer);

  function type() {
    if (i < text.length) {
      // Append a chunk of text
      const chunk = text.substring(0, i + step);
      // Parse markdown for the current chunk to keep formatting
      textContainer.innerHTML = marked.parse(chunk);

      i += step;
      scrollToBottom();
      setTimeout(type, speed);
    } else {
      // Ensure full text is rendered correctly at the end
      textContainer.innerHTML = marked.parse(text);
      if (callback) callback();
    }
  }

  type();
}

function attachEventListeners(container) {
  // Re-attach listeners for buttons/images inside the container
  if (!container) return;

  // Suggested Actions
  container.querySelectorAll(".suggested-action-btn").forEach((btn) => {
    btn.addEventListener("click", () => {
      selectSuggestedAction(btn.getAttribute("data-action"));
    });
  });

  // Images
  container
    .querySelectorAll(".step-image")
    .forEach((img) =>
      img.addEventListener("click", () => openImageModal(img.src)),
    );

  // Clarify Buttons
  container.querySelectorAll(".clarify-step-btn").forEach((btn) => {
    btn.addEventListener("click", () => {
      const stepNum = btn.getAttribute("data-step");
      messageInput.value = `clarify step ${stepNum}`;
      sendMessage();
    });
  });
}

function renderCapabilitiesResponse(data) {
  // Separated Header (title) from typed content
  let html = `
  <div class="capabilities-wrapper">
    <div class="capabilities-container">
      <div class="capabilities-header">
        <h2 class="capabilities-title">${escapeHtml(data.title || "")}</h2>
        <!-- Content is typed above, so skipped here -->
      </div>

      <div class="capabilities-grid">
  `;

  if (data.features && data.features.length > 0) {
    data.features.forEach((feature) => {
      html += `
      <div class="capability-card">
        <div class="capability-icon">${feature.icon}</div>
        <div class="capability-info">
          <h3 class="capability-title">${escapeHtml(feature.title)}</h3>
          <p class="capability-description">${escapeHtml(
            feature.description,
          )}</p>
        </div>
      </div>
    `;
    });
  }

  html += `
      </div>
      <div class="capabilities-footer">
        ${escapeHtml(data.footer_cta)}
      </div>
      ${renderSuggestedActions(data.suggested_actions)}
    </div>
  </div>
  `;
  return html;
}

function renderTutorialResponse(data) {
  // Content is typed separately
  let html = '<div class="tutorial-content">';

  // Help Note
  if (data.help_note)
    html += `<div class="help-note">${marked.parse(data.help_note)}</div>`;

  // Steps
  if (data.steps && data.steps.length > 0) {
    html += '<div class="steps-container">';
    data.steps.forEach((step) => {
      html += '<div class="step-item">';
      html += '<div class="step-header">';
      html += `<div class="step-number">${step.step_number}</div>`;
      html += `<div class="step-text">${marked.parse(step.text)}</div>`;
      html += "</div>";
      if (step.image) {
        const imageUrl = step.image.startsWith("http")
          ? step.image
          : `${API_BASE_URL}${step.image}`;
        html += `<img src="${imageUrl}" alt="Step ${step.step_number}" class="step-image" onerror="this.style.display='none'">`;
      }
      html += "</div>";
    });
    html += "</div>";
  }

  // Pro Tip & Completion
  html += `<div class="completion-message"><strong>Pro tip:</strong> ${marked.parse(
    data.pro_tip || "",
  )}</div>`;
  html += `<div class="completion-message">${marked.parse(
    data.completion_message || "",
  )}</div>`;

  html += renderSuggestedActions(data.suggested_actions);
  html += "</div>";
  return html;
}

function renderTutorialClarifyResponse(data) {
  const cs = data.clarified_step;
  let html = '<div class="tutorial-content">';
  // Content is typed separately

  html += `<div class="step-item"><div class="step-header"><div class="step-number">${
    cs.step_number
  }</div><div class="step-text">${marked.parse(cs.clarified)}</div></div>`;
  if (cs.image) {
    const imageUrl = cs.image.startsWith("http")
      ? cs.image
      : `${API_BASE_URL}${cs.image}`;
    html += `<img src="${imageUrl}" alt="Step ${cs.step_number}" class="step-image" onerror="this.style.display='none'">`;
  }
  html += "</div>";
  html += renderSuggestedActions(data.suggested_actions);
  html += "</div>";
  return html;
}

function renderRegularResponse(data) {
  let html = "";
  // Content typed separately
  if (data.completion_message)
    html += `<div class="completion-message">${marked.parse(
      data.completion_message,
    )}</div>`;
  html += renderSuggestedActions(data.suggested_actions);
  return html;
}

function renderSuggestedActions(actions) {
  if (!actions || actions.length === 0) return "";
  let html =
    '<div class="suggested-actions"><div class="suggested-actions-title">Suggested Actions</div><div class="suggested-actions-list">';
  actions.forEach((action) => {
    html += `<button class="suggested-action-btn" data-action="${escapeHtml(
      action,
    )}">${escapeHtml(action)}</button>`;
  });
  html += "</div></div>";
  return html;
}

function escapeHtml(text) {
  const div = document.createElement("div");
  div.textContent = text;
  return div.innerHTML;
}

function selectSuggestedAction(action) {
  messageInput.value = action;
  messageInput.focus();
  auto_resize();
  setTimeout(() => sendMessage(), 100);
}

function showTypingIndicator() {
  const messageDiv = document.createElement("div");
  messageDiv.className = "message assistant";
  messageDiv.id = "typing-indicator";

  const avatarDiv = document.createElement("div");
  avatarDiv.className = "message-avatar";
  avatarDiv.textContent = "AI";

  const typingDiv = document.createElement("div");
  typingDiv.className = "message-content";
  typingDiv.innerHTML = `<div class="typing-indicator"><div class="dot"></div><div class="dot"></div><div class="dot"></div></div>`;

  messageDiv.appendChild(avatarDiv);
  messageDiv.appendChild(typingDiv);
  chatHistory.appendChild(messageDiv);
  scrollToBottom();
}

function removeTypingIndicator() {
  const typing = document.getElementById("typing-indicator");
  if (typing) typing.remove();
}

function scrollToBottom() {
  setTimeout(() => {
    const content = document.querySelector(".content");
    if (content) {
      content.scrollTop = content.scrollHeight;
    }
  }, 100);
}

// === SEND MESSAGE (includes conversation_history + last_tutorial) ===
async function sendMessage() {
  const message = messageInput.value.trim();
  if (!message) return;

  // Add user message (UI + local history)
  addMessage(message, true);
  chatStateHistory.push(`User: ${message}`);

  messageInput.value = "";
  auto_resize();
  sendBtn.disabled = true;
  showTypingIndicator();

  try {
    // Lazy Session Creation: Create session if it doesn't exist yet
    if (!currentSessionId) {
      const sessResponse = await fetch(`${API_BASE_URL}/sessions`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ user_id: USER_ID, license_id: LICENSE_ID }),
      });
      const sessData = await sessResponse.json();
      currentSessionId = sessData.session_id;
      // Persist the new session ID immediately
      sessionStorage.setItem("activeSessionId", currentSessionId);
    }

    // If this is a "clarify step X" type, we still send lastTutorialSteps so backend can clarify
    const payload = {
      message: message,
      session_id: currentSessionId,
      last_tutorial: lastTutorialSteps,
    };

    const response = await fetch(API_ENDPOINT, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
    });

    removeTypingIndicator();

    if (!response.ok) {
      throw new Error(`HTTP error ${response.status}`);
    }

    const data = await response.json();

    // Render assistant response object (data)
    addMessage("", false, data);

    // Update local lastTutorialSteps if backend returned steps
    if (data.type === "tutorial" && Array.isArray(data.steps)) {
      lastTutorialSteps = data.steps;
    }
    // If clarify response, we don't overwrite lastTutorialSteps

    // Build assistantText for local chatStateHistory (short content)
    let assistantText = "";
    if (data.type === "tutorial") {
      assistantText = (data.content || "") + " " + (data.summary || "");
    } else if (data.type === "tutorial_clarify") {
      assistantText = data.clarified_step
        ? data.clarified_step.clarified || ""
        : data.content || "";
    } else {
      assistantText = data.content || "";
    }
    assistantText = assistantText.trim();
    if (assistantText) {
      chatStateHistory.push(`Assistant: ${assistantText}`);
    }

    // If response contains conversation_history from server, sync if longer
    if (Array.isArray(data.conversation_history)) {
      if (data.conversation_history.length >= chatStateHistory.length) {
        chatStateHistory.length = 0;
        data.conversation_history.forEach((item) =>
          chatStateHistory.push(item),
        );
      }
    }
    // After first message, refresh sessions to update title
    if (chatStateHistory.length <= 2) {
      fetchSessions();
    }
  } catch (err) {
    removeTypingIndicator();
    console.error("Send error:", err);
    addMessage("Sorry, something went wrong. Try again.", false);
  } finally {
    sendBtn.disabled = false;
  }
}

function handleKeyPress(event) {
  if (event.key === "Enter" && !event.shiftKey) {
    event.preventDefault();
    sendMessage();
  }
}

function auto_resize() {
  messageInput.style.height = "auto";
  messageInput.style.height = Math.min(messageInput.scrollHeight, 200) + "px";
}

messageInput.addEventListener("input", () => {
  auto_resize();
  sendBtn.disabled = !messageInput.value.trim();
});

// Initialize
window.onload = fetchSessions;

// ==========================================
// VOICE INTEGRATION LOGIC
// ==========================================
let mediaRecorder = null;
let audioChunks = [];
let isRecording = false;
let timerInterval = null;
let recordingStartTime = null;

async function toggleRecording() {
  if (isRecording) {
    stopRecording();
  } else {
    await startRecording();
  }
}

async function startRecording() {
  try {
    const stream = await navigator.mediaDevices.getUserMedia({ audio: true });

    mediaRecorder = new MediaRecorder(stream);
    audioChunks = [];

    mediaRecorder.ondataavailable = (event) => {
      audioChunks.push(event.data);
    };

    mediaRecorder.onstop = async () => {
      const audioBlob = new Blob(audioChunks, { type: "audio/webm" }); // Chrome uses webm defaults usually
      await sendAudioToBackend(audioBlob);

      // Stop all tracks to release microphone
      stream.getTracks().forEach((track) => track.stop());
    };

    mediaRecorder.start();
    isRecording = true;

    // Update UI
    voiceBtn.classList.add("recording");
    recordingTimer.classList.remove("hidden");
    recordingTimer.textContent = "00:00";

    // Start Timer
    recordingStartTime = Date.now();
    timerInterval = setInterval(updateTimer, 1000);
  } catch (err) {
    console.error("Error accessing microphone:", err);
    alert("Could not access microphone. Please allow permissions.");
  }
}

function stopRecording() {
  if (mediaRecorder && isRecording) {
    mediaRecorder.stop();
    isRecording = false;

    // Update UI
    voiceBtn.classList.remove("recording");
    recordingTimer.classList.add("hidden");

    // Stop Timer
    clearInterval(timerInterval);
  }
}

function updateTimer() {
  const elapsed = Math.floor((Date.now() - recordingStartTime) / 1000);
  const minutes = Math.floor(elapsed / 60)
    .toString()
    .padStart(2, "0");
  const seconds = (elapsed % 60).toString().padStart(2, "0");
  recordingTimer.textContent = `${minutes}:${seconds}`;
}

async function sendAudioToBackend(audioBlob) {
  // Show loading or some indication?
  // Maybe show typing indicator while transcribing?
  showTypingIndicator();
  const formData = new FormData();
  // We'll append the file. Filename isn't critical but good to have extension.
  formData.append("audio_data", audioBlob, "voice_note.webm");

  try {
    const response = await fetch(`${API_BASE_URL}/transcribe`, {
      method: "POST",
      body: formData,
    });

    if (!response.ok) {
      throw new Error("Generic Transcription Error");
    }

    const data = await response.json();
    removeTypingIndicator();

    if (data.text) {
      // Put text in input and send
      messageInput.value = data.text;
      auto_resize();
      sendMessage();
    } else {
      console.warn("No text transcribed");
    }
  } catch (err) {
    removeTypingIndicator();
    console.error("Transcription failed:", err);
    // Silent fail or alert?
    // Maybe just put text in input saying "Error transcribing"
  }
}
