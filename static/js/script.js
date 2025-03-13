// Application State
const appState = {
  // User profile
  experience: null,
  education: null,
  goal: null,
  
  // Assessment data
  questions: [],
  currentQuestionIndex: 0,
  answers: [],
  
  // Results data
  evaluationResults: null,
  reviewData: null,
  roadmapData: null,
  
  // UI state
  isLoading: false,

    // Chat state - Add new
    chatHistory: [],
    isTyping: false


};




// DOM Elements
const DOM = {
  // Sections
  profileSection: document.getElementById('profile-section'),
  loadingSection: document.getElementById('loading-section'),
  assessmentSection: document.getElementById('assessment-section'),
  resultsSection: document.getElementById('results-section'),
  reviewSection: document.getElementById('review-section'),
  roadmapSection: document.getElementById('roadmap-section'),
  
  // Profile elements
  experienceSelect: document.getElementById('experience'),
  educationRadios: document.getElementsByName('education'),
  goalRadios: document.getElementsByName('goal'),
  startEvaluatorBtn: document.getElementById('start-evaluator-btn'),
  
  // Loading elements
  loadingMessage: document.getElementById('loading-message'),
  
  // Assessment elements
  questionCounter: document.getElementById('question-counter'),
  progressValue: document.getElementById('progress-value'),
  questionText: document.getElementById('question-text'),
  optionsContainer: document.getElementById('options-container'),
  prevQuestionBtn: document.getElementById('prev-question-btn'),
  nextQuestionBtn: document.getElementById('next-question-btn'),
  submitEvaluationBtn: document.getElementById('submit-evaluation-btn'),
  
  // Results elements
  overallScoreValue: document.getElementById('overall-score-value'),
  scoreChart: document.getElementById('score-chart'),
  areaScores: document.getElementById('area-scores'),
  reviewAnswersBtn: document.getElementById('review-answers-btn'),
  generateRoadmapBtn: document.getElementById('generate-roadmap-btn'),
  
  // Review elements
  reviewContainer: document.getElementById('review-container'),
  backToResultsBtn: document.getElementById('back-to-results-btn'),
  
  // Roadmap elements
  roadmapTitle: document.getElementById('roadmap-title'),
  levelBadge: document.getElementById('level-badge'),
  weeksContainer: document.getElementById('weeks-container'),
  restartBtn: document.getElementById('restart-btn'),
  downloadRoadmapBtn: document.getElementById('download-roadmap-btn'),

  // Chat elements - Add new chat-related elements
  chatMessages: document.getElementById('chat-messages'),
  chatInput: document.getElementById('chat-input'),
  sendMessageBtn: document.getElementById('send-message-btn'),
  backToRoadmapBtn: document.getElementById('back-to-roadmap-btn'),
  openChatBtn: document.getElementById('open-chat-btn')

  
};



// Chart instance
let scoreChart = null;

// Application Initialization
document.addEventListener('DOMContentLoaded', () => {
  // Set up event listeners
  setupEventListeners();
  
  // Show profile section by default
  showSection('profile-section');
});

// Setup Event Listeners
function setupEventListeners() {
  // Profile section
  DOM.startEvaluatorBtn.addEventListener('click', handleStartEvaluator);
  
  // Assessment section
  DOM.prevQuestionBtn.addEventListener('click', goToPreviousQuestion);
  DOM.nextQuestionBtn.addEventListener('click', goToNextQuestion);
  DOM.submitEvaluationBtn.addEventListener('click', submitEvaluation);
  
  // Results section
  DOM.reviewAnswersBtn.addEventListener('click', () => showSection('review-section'));
  DOM.generateRoadmapBtn.addEventListener('click', generateRoadmap);
  
  // Review section
  DOM.backToResultsBtn.addEventListener('click', () => showSection('results-section'));
  
  // Roadmap section
  DOM.restartBtn.addEventListener('click', restartApplication);
  DOM.downloadRoadmapBtn.addEventListener('click', downloadRoadmap);

  // Chat section - Add new
  DOM.openChatBtn.addEventListener('click', () => showSection('chat-section'));
  DOM.backToRoadmapBtn.addEventListener('click', () => showSection('roadmap-section'));
  DOM.sendMessageBtn.addEventListener('click', sendChatMessage);
  DOM.chatInput.addEventListener('keydown', handleChatInputKeydown);
}


// Section Management
function showSection(sectionId) {
  // Hide all sections
  DOM.profileSection.classList.add('hidden');
  DOM.loadingSection.classList.add('hidden');
  DOM.assessmentSection.classList.add('hidden');
  DOM.resultsSection.classList.add('hidden');
  DOM.reviewSection.classList.add('hidden');
  DOM.roadmapSection.classList.add('hidden');
  
  // Show the requested section
  document.getElementById(sectionId).classList.remove('hidden');
  
    // Additional actions when showing certain sections
    if (sectionId === 'results-section' && appState.evaluationResults) {
        initializeResultsSection();
    } else if (sectionId === 'chat-section') {
        initializeChatSection(); // Initialize chat when showing chat section
    } else if (sectionId === 'roadmap-section' && appState.roadmapData) {
        // Ensure roadmap is initialized properly
    }
  // Scroll to top
  window.scrollTo(0, 0);
}


// Handle Enter key in chat input
function handleChatInputKeydown(event) {
    if (event.key === 'Enter' && !event.shiftKey) {
        event.preventDefault();
        sendChatMessage();
    }
}

// Send message to the agent and display in chat
async function sendChatMessage() {
    const messageText = DOM.chatInput.value.trim();
    
    // Don't send empty messages
    if (!messageText) return;
    
    // Clear input
    DOM.chatInput.value = '';
    
    // Add user message to chat
    addMessageToChat('user', messageText);
    
    // Show typing indicator
    showTypingIndicator();
    
    try {
        // Send message to the agent via API
        const response = await fetch('/api/chat', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                message: messageText,
                context: {
                    experience: appState.experience,
                    education: appState.education,
                    goal: appState.goal,
                    evaluationResults: appState.evaluationResults,
                    roadmapData: appState.roadmapData
                }
            })
        });
        
        // Remove typing indicator
        hideTypingIndicator();
        
        if (!response.ok) {
            throw new Error('Failed to get response from assistant');
        }
        
        const data = await response.json();
        
        // Add agent response to chat
        addMessageToChat('assistant', data.response);
        
        // Save to chat history
        appState.chatHistory.push({
            role: 'user',
            content: messageText
        });
        
        appState.chatHistory.push({
            role: 'assistant',
            content: data.response
        });
        
    } catch (error) {
        console.error('Error sending message:', error);
        
        // Remove typing indicator
        hideTypingIndicator();
        
        // Show error message
        addMessageToChat('assistant', 'Sorry, I encountered an error processing your request. Please try again.');
    }
    
    // Scroll to bottom of chat
    scrollChatToBottom();
}

// Add a message to the chat container
function addMessageToChat(role, content) {
    const messageDiv = document.createElement('div');
    messageDiv.className = `message ${role}-message`;
    
    // Process content for code blocks
    const processedContent = processCodeBlocks(content);
    
    const messageContent = document.createElement('div');
    messageContent.className = 'message-content';
    messageContent.innerHTML = processedContent;
    
    messageDiv.appendChild(messageContent);
    DOM.chatMessages.appendChild(messageDiv);
    
    // Clear float for proper rendering
    const clearDiv = document.createElement('div');
    clearDiv.style.clear = 'both';
    DOM.chatMessages.appendChild(clearDiv);
    
    // Scroll to bottom
    scrollChatToBottom();
}

// Process code blocks in the message content
function processCodeBlocks(content) {
    // Simple regex for code blocks (```code```)
    return content.replace(/```([\s\S]*?)```/g, '<div class="code-block">$1</div>');
}

// Show typing indicator
function showTypingIndicator() {
    if (appState.isTyping) return;
    
    appState.isTyping = true;
    
    const typingDiv = document.createElement('div');
    typingDiv.className = 'message assistant-message';
    typingDiv.id = 'typing-indicator';
    
    const typingContent = document.createElement('div');
    typingContent.className = 'typing-indicator';
    typingContent.innerHTML = '<span></span><span></span><span></span>';
    
    typingDiv.appendChild(typingContent);
    DOM.chatMessages.appendChild(typingDiv);
    
    // Clear float
    const clearDiv = document.createElement('div');
    clearDiv.style.clear = 'both';
    DOM.chatMessages.appendChild(clearDiv);
    
    scrollChatToBottom();
}

// Hide typing indicator
function hideTypingIndicator() {
    const indicator = document.getElementById('typing-indicator');
    if (indicator) {
        indicator.remove();
    }
    
    appState.isTyping = false;
}

// Scroll chat to bottom
function scrollChatToBottom() {
    DOM.chatMessages.scrollTop = DOM.chatMessages.scrollHeight;
}

// Initialize chat section when shown
function initializeChatSection() {
    // If no chat history, add welcome message
    if (appState.chatHistory.length === 0) {
        // Welcome message is already added in HTML
        
        // Save welcome message to history
        appState.chatHistory.push({
            role: 'assistant',
            content: 'Hello! I\'m your learning assistant. How can I help you with your learning path today?'
        });
    } else {
        // Clear existing messages
        DOM.chatMessages.innerHTML = '';
        
        // Add all messages from history
        appState.chatHistory.forEach(msg => {
            addMessageToChat(msg.role, msg.content);
        });
    }
    
    // Focus on input
    setTimeout(() => {
        DOM.chatInput.focus();
    }, 100);
}




// Save User Profile
function handleStartEvaluator() {
  // Validate inputs
  if (!validateProfileInputs()) {
      alert('Please fill in all the fields before continuing');
      return;
  }
  
  // Save profile data
  appState.experience = DOM.experienceSelect.value;
  appState.education = getSelectedRadioValue(DOM.educationRadios);
  appState.goal = getSelectedRadioValue(DOM.goalRadios);
  
  // Show loading screen
  showSection('loading-section');
  DOM.loadingMessage.textContent = 'Loading your personalized assessment...';
  
  // Save profile data to the server
  saveProfile()
      .then(() => fetchQuestions())
      .catch(error => {
          console.error('Error starting evaluation:', error);
          alert('There was an error starting the evaluation. Please try again.');
          showSection('profile-section');
      });
}

// Validate Profile Inputs
function validateProfileInputs() {
  if (!DOM.experienceSelect.value) return false;
  if (!getSelectedRadioValue(DOM.educationRadios)) return false;
  if (!getSelectedRadioValue(DOM.goalRadios)) return false;
  return true;
}

// Save Profile to Server
async function saveProfile() {
  try {
      const response = await fetch('/api/save_profile', {
          method: 'POST',
          headers: {
              'Content-Type': 'application/json'
          },
          body: JSON.stringify({
              experience: appState.experience,
              education: appState.education,
              goal: appState.goal
          })
      });
      
      if (!response.ok) {
          throw new Error('Failed to save profile');
      }
      
      return await response.json();
  } catch (error) {
      console.error('Error saving profile:', error);
      throw error;
  }
}

// Fetch Questions from Server
async function fetchQuestions() {
  try {
      const response = await fetch('/api/get_questions');
      
      if (!response.ok) {
          throw new Error('Failed to fetch questions');
      }
      
      const data = await response.json();
      
      // Save questions to state
      appState.questions = data.questions || [];
      appState.answers = Array(appState.questions.length).fill(null);
      
      // Initialize the assessment section
      initializeAssessment();
      
      // Show assessment section
      showSection('assessment-section');
  } catch (error) {
      console.error('Error fetching questions:', error);
      alert('There was an error loading the questions. Please try again.');
      showSection('profile-section');
  }
}

// Initialize Assessment Section
function initializeAssessment() {
  // Reset state
  appState.currentQuestionIndex = 0;
  
  // Update UI for first question
  updateQuestionUI();
}

// Update Question UI
function updateQuestionUI() {
  const currentQuestion = appState.questions[appState.currentQuestionIndex];
  
  // Update progress and counter
  const progressPercentage = ((appState.currentQuestionIndex + 1) / appState.questions.length) * 100;
  DOM.progressValue.style.width = `${progressPercentage}%`;
  DOM.questionCounter.textContent = `Question ${appState.currentQuestionIndex + 1} of ${appState.questions.length}`;
  
  // Update question text
  DOM.questionText.textContent = currentQuestion.question;
  
  // Clear existing options
  DOM.optionsContainer.innerHTML = '';
  
  // Generate options
  currentQuestion.options.forEach(option => {
      const optionElement = document.createElement('div');
      optionElement.className = 'option';
      
      // If this option is selected, add selected class
      if (appState.answers[appState.currentQuestionIndex] === option.id) {
          optionElement.classList.add('selected');
      }
      
      // Create option HTML
      optionElement.innerHTML = `
          <div class="option-marker">${option.id}</div>
          <div class="option-text">${option.text}</div>
      `;
      
      // Add click event
      optionElement.addEventListener('click', () => selectOption(option.id));
      
      // Add to container
      DOM.optionsContainer.appendChild(optionElement);
  });
  
  // Update navigation buttons
  DOM.prevQuestionBtn.disabled = appState.currentQuestionIndex === 0;
  
  // Show/hide next and submit buttons
  if (appState.currentQuestionIndex === appState.questions.length - 1) {
      DOM.nextQuestionBtn.classList.add('hidden');
      DOM.submitEvaluationBtn.classList.remove('hidden');
  } else {
      DOM.nextQuestionBtn.classList.remove('hidden');
      DOM.submitEvaluationBtn.classList.add('hidden');
  }
}

// Select Option
function selectOption(optionId) {
  // Save answer
  appState.answers[appState.currentQuestionIndex] = optionId;
  
  // Update UI
  const options = DOM.optionsContainer.querySelectorAll('.option');
  options.forEach(option => {
      const marker = option.querySelector('.option-marker');
      if (marker.textContent === optionId) {
          option.classList.add('selected');
      } else {
          option.classList.remove('selected');
      }
  });
}

// Navigation Functions
function goToPreviousQuestion() {
  if (appState.currentQuestionIndex > 0) {
      appState.currentQuestionIndex--;
      updateQuestionUI();
  }
}

function goToNextQuestion() {
  if (appState.currentQuestionIndex < appState.questions.length - 1) {
      appState.currentQuestionIndex++;
      updateQuestionUI();
  }
}

// Submit Evaluation
async function submitEvaluation() {
  // Check if all questions are answered
  const unansweredCount = appState.answers.filter(answer => answer === null).length;
  
  if (unansweredCount > 0) {
      const confirmSubmit = confirm(`You have ${unansweredCount} unanswered questions. Do you want to submit anyway?`);
      if (!confirmSubmit) return;
  }
  
  // Show loading screen
  showSection('loading-section');
  DOM.loadingMessage.textContent = 'Evaluating your answers...';
  
  try {
      const response = await fetch('/api/submit_answers', {
          method: 'POST',
          headers: {
              'Content-Type': 'application/json'
          },
          body: JSON.stringify({
              answers: appState.answers
          })
      });
      
      if (!response.ok) {
          throw new Error('Failed to submit answers');
      }
      
      const data = await response.json();
      
      // Save evaluation results
      appState.evaluationResults = data;
      appState.reviewData = data.review;
      
      // Show results section
      showSection('results-section');
  } catch (error) {
      console.error('Error submitting answers:', error);
      alert('There was an error evaluating your answers. Please try again.');
      showSection('assessment-section');
  }
}

// Initialize Results Section
function initializeResultsSection() {
  const results = appState.evaluationResults;
  
  // Update overall score
  DOM.overallScoreValue.textContent = `${results.score}%`;
  
  // Initialize chart if it doesn't exist
  initializeScoreChart();
  
  // Update area scores
  updateAreaScores();
}

// Initialize Score Chart
function initializeScoreChart() {
  const results = appState.evaluationResults;
  const ctx = DOM.scoreChart.getContext('2d');
  
  // Extract data for chart
  const areas = Object.keys(results.areas);
  const userScores = areas.map(area => results.areas[area].score);
  const recommendedScores = areas.map(area => results.areas[area].recommended);
  
  // Destroy existing chart if it exists
  if (scoreChart) {
      scoreChart.destroy();
  }
  
  // Create new chart
  scoreChart = new Chart(ctx, {
      type: 'radar',
      data: {
          labels: areas,
          datasets: [
              {
                  label: 'Your Score',
                  data: userScores,
                  backgroundColor: 'rgba(67, 97, 238, 0.2)',
                  borderColor: 'rgba(67, 97, 238, 1)',
                  pointBackgroundColor: 'rgba(67, 97, 238, 1)',
                  pointBorderColor: '#fff',
                  pointHoverBackgroundColor: '#fff',
                  pointHoverBorderColor: 'rgba(67, 97, 238, 1)'
              },
              {
                  label: 'Recommended Level',
                  data: recommendedScores,
                  backgroundColor: 'rgba(76, 201, 240, 0.2)',
                  borderColor: 'rgba(76, 201, 240, 1)',
                  pointBackgroundColor: 'rgba(76, 201, 240, 1)',
                  pointBorderColor: '#fff',
                  pointHoverBackgroundColor: '#fff',
                  pointHoverBorderColor: 'rgba(76, 201, 240, 1)'
              }
          ]
      },
      options: {
          scales: {
              r: {
                  min: 0,
                  max: 100,
                  ticks: {
                      stepSize: 20
                  }
              }
          },
          elements: {
              line: {
                  tension: 0.1
              }
          }
      }
  });
}

// Update Area Scores
function updateAreaScores() {
  const results = appState.evaluationResults;
  
  // Clear existing scores
  DOM.areaScores.innerHTML = '';
  
  // Add area score cards
  Object.keys(results.areas).forEach(area => {
      const areaData = results.areas[area];
      const scoreCard = document.createElement('div');
      scoreCard.className = 'area-score-card';
      
      // Create HTML
      scoreCard.innerHTML = `
          <div class="area-name">${area}</div>
          <div class="area-progress">
              <div class="area-progress-value" style="width: ${areaData.score}%"></div>
          </div>
          <div class="area-score-value">
              <span>Your score: ${areaData.score}%</span>
              <span>Recommended: ${areaData.recommended}%</span>
          </div>
          <div class="area-feedback">${areaData.feedback}</div>
      `;
      
      // Add to container
      DOM.areaScores.appendChild(scoreCard);
  });
}

// Generate Roadmap
async function generateRoadmap() {
  // Show loading screen
  showSection('loading-section');
  DOM.loadingMessage.textContent = 'Generating your personalized learning path...';
  
  try {
      const response = await fetch('/api/generate_roadmap');
      
      if (!response.ok) {
          throw new Error('Failed to generate roadmap');
      }
      
      const data = await response.json();
      
      // Save roadmap data
      appState.roadmapData = data;
      
      // Initialize roadmap section
      initializeRoadmapSection();
      
      // Show roadmap section
      showSection('roadmap-section');
  } catch (error) {
      console.error('Error generating roadmap:', error);
      alert('There was an error generating your learning path. Please try again.');
      showSection('results-section');
  }
}

// Initialize Roadmap Section
function initializeRoadmapSection() {
  const roadmap = appState.roadmapData;
  
  // Update title and level
  DOM.roadmapTitle.textContent = roadmap.title;
  DOM.levelBadge.textContent = roadmap.level;
  
  // Clear existing weeks
  DOM.weeksContainer.innerHTML = '';
  
  // Generate week cards
  roadmap.weeks.forEach(week => {
      const weekCard = document.createElement('div');
      weekCard.className = 'week-card';
      
      // Week header
      const weekHeader = document.createElement('div');
      weekHeader.className = 'week-header';
      weekHeader.innerHTML = `
          <div class="week-title">Week ${week.week}: ${week.focus}</div>
          <div class="week-stats">
              <div class="week-stat">
                  <span class="week-stat-icon">⏱️</span>
                  <span>${week.hours} hours</span>
              </div>
              <div class="week-stat">
                  <span class="week-stat-icon">📚</span>
                  <span>${week.modules} modules</span>
              </div>
              <div class="week-stat">
                  <span class="week-stat-icon">📝</span>
                  <span>${week.lessons} lessons</span>
              </div>
          </div>
      `;
      
      // Week content
      const weekContent = document.createElement('div');
      weekContent.className = 'week-content';
      
      // Topics
      const topicsList = document.createElement('div');
      topicsList.className = 'topics-list';
      topicsList.innerHTML = `
          <div class="topics-title">Topics to Cover:</div>
          <div class="topics">
              ${week.topics.map(topic => `<div class="topic-tag">${topic}</div>`).join('')}
          </div>
      `;
      
      // Resources
      const resourcesList = document.createElement('div');
      resourcesList.className = 'resources-list';
      resourcesList.innerHTML = `
          <div class="topics-title">Recommended Resources:</div>
          ${week.resources.map(resource => `
              <div class="resource-item">
                  <div class="resource-title">${resource.type}: ${resource.title}</div>
                  ${resource.url ? `<a href="${resource.url}" target="_blank" class="resource-link">Open Resource →</a>` : ''}
              </div>
          `).join('')}
      `;
      
      // Assemble week card
      weekContent.appendChild(topicsList);
      weekContent.appendChild(resourcesList);
      weekCard.appendChild(weekHeader);
      weekCard.appendChild(weekContent);
      
      // Add to container
      DOM.weeksContainer.appendChild(weekCard);
  });
  
  // Set active week in progress bar
  const weekElements = document.querySelectorAll('.week');
  weekElements.forEach(weekEl => {
      weekEl.addEventListener('click', () => {
          // Remove active class from all weeks
          weekElements.forEach(w => w.classList.remove('active'));
          
          // Add active class to clicked week
          weekEl.classList.add('active');
          
          // Scroll to the corresponding week card
          const weekIndex = parseInt(weekEl.getAttribute('data-week')) - 1;
          const weekCards = DOM.weeksContainer.querySelectorAll('.week-card');
          
          if (weekCards[weekIndex]) {
              weekCards[weekIndex].scrollIntoView({ behavior: 'smooth' });
          }
      });
  });
  
  // Set first week as active by default
  if (weekElements.length > 0) {
      weekElements[0].classList.add('active');
  }
}

// Review Answers
function showReviewSection() {
  // Initialize review section if review data exists
  if (appState.reviewData) {
      initializeReviewSection();
  }
  
  // Show review section
  showSection('review-section');
}

// Initialize Review Section
function initializeReviewSection() {
  // Clear existing review items
  DOM.reviewContainer.innerHTML = '';
  
  // Generate review items
  appState.reviewData.forEach(item => {
      const question = appState.questions.find(q => q.id === item.question_id);
      if (!question) return;
      
      const reviewItem = document.createElement('div');
      reviewItem.className = 'review-item';
      
      // Question text
      const questionElement = document.createElement('div');
      questionElement.className = 'review-question';
      questionElement.textContent = question.question;
      
      // Options
      const optionsContainer = document.createElement('div');
      optionsContainer.className = 'review-options';
      
      question.options.forEach(option => {
          const optionElement = document.createElement('div');
          
          // Determine option class
          if (item.correct && option.id === item.user_answer) {
              optionElement.className = 'review-option correct';
          } else if (!item.correct && option.id === item.user_answer) {
              optionElement.className = 'review-option incorrect';
          } else if (option.id === question.correctAnswer) {
              optionElement.className = 'review-option correct';
          } else {
              optionElement.className = 'review-option neutral';
          }
          
          // Option content
          optionElement.innerHTML = `
              <div class="review-option-marker">${option.id}</div>
              <div class="option-text">${option.text}</div>
          `;
          
          optionsContainer.appendChild(optionElement);
      });
      
      // Explanation
      const explanationElement = document.createElement('div');
      explanationElement.className = 'review-explanation';
      explanationElement.textContent = item.explanation;
      
      // Assemble review item
      reviewItem.appendChild(questionElement);
      reviewItem.appendChild(optionsContainer);
      reviewItem.appendChild(explanationElement);
      
      // Add to container
      DOM.reviewContainer.appendChild(reviewItem);
  });
}

// Download Roadmap
function downloadRoadmap() {
  if (!appState.roadmapData) return;
  
  const roadmap = appState.roadmapData;
  
  // Create text content
  let content = `# ${roadmap.title}\n\n`;
  content += `Level: ${roadmap.level}\n`;
  content += `Overall Score: ${roadmap.overall_score}%\n\n`;
  
  // Add weeks
  roadmap.weeks.forEach(week => {
      content += `## Week ${week.week}: ${week.focus}\n\n`;
      content += `* Study Time: ${week.hours} hours\n`;
      content += `* Modules: ${week.modules}\n`;
      content += `* Lessons: ${week.lessons}\n\n`;
      
      content += `### Topics to Cover:\n`;
      week.topics.forEach(topic => {
          content += `* ${topic}\n`;
      });
      content += `\n`;
      
      content += `### Recommended Resources:\n`;
      week.resources.forEach(resource => {
          if (resource.url) {
              content += `* ${resource.type}: [${resource.title}](${resource.url})\n`;
          } else {
              content += `* ${resource.type}: ${resource.title}\n`;
          }
      });
      content += `\n`;
  });
  
  // Create download link
  const blob = new Blob([content], { type: 'text/plain' });
  const url = URL.createObjectURL(blob);
  const a = document.createElement('a');
  a.href = url;
  a.download = 'learning-roadmap.md';
  
  // Trigger download
  document.body.appendChild(a);
  a.click();
  
  // Cleanup
  document.body.removeChild(a);
  URL.revokeObjectURL(url);
}

// Restart Application
function restartApplication() {
  // Reset state
  appState.experience = null;
  appState.education = null;
  appState.goal = null;
  appState.questions = [];
  appState.currentQuestionIndex = 0;
  appState.answers = [];
  appState.evaluationResults = null;
  appState.reviewData = null;
  appState.roadmapData = null;
  
  // Reset form fields
  DOM.experienceSelect.value = '';
  const radioInputs = [...DOM.educationRadios, ...DOM.goalRadios];
  radioInputs.forEach(input => input.checked = false);
  
  // Clear session on server
  fetch('/api/clear_session', { method: 'POST' })
      .then(() => console.log('Session cleared'))
      .catch(err => console.error('Error clearing session:', err));
  
  // Show profile section
  showSection('profile-section');
}

// Utility Functions
function getSelectedRadioValue(radioButtons) {
  for (const radioButton of radioButtons) {
      if (radioButton.checked) {
          return radioButton.value;
      }
  }
  return null;
}