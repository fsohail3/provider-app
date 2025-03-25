// Expose handleSubmission to window scope
window.handleSubmission = null;

document.addEventListener('DOMContentLoaded', function() {
    console.log('DOM Content Loaded - Setting up event handlers');
    
    const chatForm = document.getElementById('chat-form');
    const patientForm = document.getElementById('patient-form');
    const userInput = document.getElementById('user-input');
    const messagesArea = document.getElementById('chat-messages');
    const procedureSection = document.getElementById('procedure-section');
    const diagnosisSection = document.getElementById('diagnosis-section');
    const newRequestButton = document.getElementById('new-request');
    const submitButton = document.getElementById('submit-button');
    const followUpButton = document.getElementById('follow-up-button');
    const consultationTypes = document.getElementsByName('consultation-type');

    console.log('Elements found:', {
        chatForm: !!chatForm,
        patientForm: !!patientForm,
        procedureSection: !!procedureSection,
        submitButton: !!submitButton,
        messagesArea: !!messagesArea
    });

    // Chat history
    let chatHistory = [];

    // Set procedure as default
    const procedureRadio = document.getElementById('procedure');
    if (procedureRadio) {
        procedureRadio.checked = true;
        console.log('Set procedure as default');
    }

    // Show procedure section by default (with null check)
    if (procedureSection) {
        procedureSection.style.display = 'block';
        console.log('Showed procedure section');
    }

    // Handle consultation type change
    document.querySelectorAll('input[name="consultation-type"]').forEach(radio => {
        radio.addEventListener('change', (e) => {
            console.log('Consultation type changed:', e.target.value);
            if (procedureSection) {
                procedureSection.style.display = e.target.value === 'procedure' ? 'block' : 'none';
            }
        });
    });

    // Handle submit button click (with debug logging)
    if (submitButton) {
        console.log('Adding click handler to submit button');
        submitButton.addEventListener('click', function(e) {
            console.log('Submit button clicked (main.js handler)');
            e.preventDefault();
            
            if (validateForm()) {
                console.log('Form validation passed, calling handleSubmission');
                handleSubmission();
            } else {
                console.log('Form validation failed');
                addMessage('assistant', 'Please fill in the required fields before submitting.');
            }
        });
    } else {
        console.error('Submit button not found in DOM');
    }

    // New request button handler (with null check)
    if (newRequestButton && patientForm && procedureSection) {
        newRequestButton.addEventListener('click', function() {
            console.log('New request button clicked');
            patientForm.reset();
            if (messagesArea) messagesArea.innerHTML = '';
            chatHistory = [];
            if (userInput) userInput.value = '';
            if (procedureRadio) procedureRadio.checked = true;
            procedureSection.style.display = 'block';
        });
    }

    // Add a global loading state
    let isLoading = false;

    // Handle form submission logic
    async function handleSubmission() {
        console.log('handleSubmission called');
        if (isLoading) {
            console.log('Already loading, returning');
            return;
        }
        
        isLoading = true;
        showLoadingState();
        
        console.log('Starting form submission');
        const buttonText = submitButton.querySelector('.button-text');
        const spinner = submitButton.querySelector('.spinner-border');
        
        // Show initial loading message in chat
        const loadingMessage = addLoadingMessage();
        
        try {
            // Generate initial query based on consultation type
            const consultationType = document.querySelector('input[name="consultation-type"]:checked').value;
            console.log('Consultation type:', consultationType);
            
            const procedureName = document.getElementById('procedure-name').value;
            console.log('Procedure name:', procedureName);
            
            const message = consultationType === 'diagnosis' 
                ? 'Please provide diagnosis recommendations based on the provided information.'
                : `Please provide procedure guidelines and checklist for ${procedureName}.`;

            // Collect patient information
            const patientInfo = {
                consultationType: consultationType,
                procedureName: procedureName
            };

            // Only add other fields if they have values
            const optionalFields = {
                'age': 'patient-age',
                'gender': 'patient-gender',
                'chiefComplaint': 'chief-complaint',
                'bp': 'bp',
                'heartRate': 'heart-rate',
                'temperature': 'temperature',
                'spo2': 'spo2',
                'allergies': 'allergies',
                'medicalHistory': 'medical-history',
                'testResults': 'test-results',
                'medications': 'medications'
            };

            for (const [key, id] of Object.entries(optionalFields)) {
                const field = document.getElementById(id);
                if (field && field.value) {
                    patientInfo[key] = field.value;
                }
            }

            patientInfo.query = message;
            patientInfo.chatHistory = chatHistory;

            console.log('Submitting request with data:', patientInfo);

            // Add user message to chat
            addMessage('user', message);

            console.log('Sending fetch request to /chat');
            const response = await fetch('/chat', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify(patientInfo)
            });

            console.log('Response received:', response.status);
            const data = await response.json();
            console.log('Response data received:', data);
            
            if (data.show_payment) {
                document.getElementById('payment-container').style.display = 'block';
                return;
            }

            // Remove loading message and add real response
            loadingMessage.remove();
            addFormattedMessage('assistant', data.response);
            
            if (data.queries_remaining !== null) {
                addMessage('system', `You have ${data.queries_remaining} out of 10 free queries remaining.`);
            }
            
            chatHistory.push({ role: 'user', content: message });
            chatHistory.push({ role: 'assistant', content: data.response });

            // Show follow-up input field
            userInput.style.display = 'block';
            followUpButton.style.display = 'block';
            submitButton.style.display = 'none';
            
        } catch (error) {
            console.error('Error during submission:', error);
            loadingMessage.remove();
            addFormattedMessage('assistant', 'Sorry, there was an error processing your request. Please try again.');
        } finally {
            hideLoadingState();
            isLoading = false;
        }
    }

    // Expose handleSubmission to window scope
    window.handleSubmission = handleSubmission;

    function showLoadingState() {
        console.log('Showing loading state');
        submitButton.disabled = true;
        const spinner = submitButton.querySelector('.spinner-border');
        const buttonText = submitButton.querySelector('.button-text');
        spinner.classList.remove('d-none');
        buttonText.textContent = 'Processing...';
    }

    function hideLoadingState() {
        console.log('Hiding loading state');
        submitButton.disabled = false;
        const spinner = submitButton.querySelector('.spinner-border');
        const buttonText = submitButton.querySelector('.button-text');
        spinner.classList.add('d-none');
        buttonText.textContent = 'Get Recommendations';
    }

    function addLoadingMessage() {
        console.log('Adding loading message');
        const loadingDiv = document.createElement('div');
        loadingDiv.className = 'message assistant-message loading-message';
        loadingDiv.innerHTML = `
            <div class="loading-state">
                <div class="loading-animation">
                    <div class="typing-indicator">
                        <span></span>
                        <span></span>
                        <span></span>
                    </div>
                </div>
                <div class="loading-text">
                    <h4>Analyzing procedure requirements...</h4>
                    <p>This typically takes 15-20 seconds. I'm preparing detailed, evidence-based recommendations.</p>
                </div>
            </div>
        `;
        messagesArea.appendChild(loadingDiv);
        messagesArea.scrollTop = messagesArea.scrollHeight;
        return loadingDiv;
    }

    // Add form validation before submission
    function validateForm() {
        const consultationType = document.querySelector('input[name="consultation-type"]:checked').value;
        console.log('Validating form for type:', consultationType);

        // For procedure type, only require procedure name
        if (consultationType === 'procedure') {
            const procedureName = document.getElementById('procedure-name');
            console.log('Procedure name value:', procedureName ? procedureName.value : 'field not found');
            
            if (!procedureName || !procedureName.value.trim()) {
                if (procedureName) {
                    procedureName.classList.add('is-invalid');
                    procedureName.focus();
                }
                console.log('Validation failed: Procedure name required');
                return false;
            }
            
            console.log('Validation passed: Procedure name provided');
            return true;
        }

        return true;
    }

    function addMessage(sender, text) {
        console.log('Adding message from:', sender);
        const messageDiv = document.createElement('div');
        messageDiv.className = `message ${sender}-message`;
        messageDiv.innerHTML = text;
        messagesArea.appendChild(messageDiv);
        messagesArea.scrollTop = messagesArea.scrollHeight;
    }

    function addFormattedMessage(sender, text) {
        console.log('Adding formatted message from:', sender);
        const messageDiv = document.createElement('div');
        messageDiv.className = `message ${sender}-message`;
        messageDiv.innerHTML = text;
        messagesArea.appendChild(messageDiv);
        
        if (sender === 'user') {
            messagesArea.scrollTop = messagesArea.scrollHeight;
        } else {
            messagesArea.scrollTop = 0;
        }
    }

    // Handle follow-up chat form
    chatForm.addEventListener('submit', async function(e) {
        e.preventDefault();
        console.log('Chat form submitted');
        
        const message = userInput.value.trim();
        if (!message) return;

        // Add user message to chat
        addMessage('user', message);
        userInput.value = '';

        // Show loading state
        const spinner = followUpButton.querySelector('.spinner-border');
        followUpButton.disabled = true;
        spinner.classList.remove('d-none');

        try {
            const response = await fetch('/chat', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    query: message,
                    chatHistory: chatHistory
                })
            });

            const data = await response.json();
            
            if (data.show_payment) {
                document.getElementById('payment-container').style.display = 'block';
                return;
            }

            // Add assistant response to chat
            addMessage('assistant', data.response);
            
            if (data.queries_remaining !== null) {
                addMessage('system', `You have ${data.queries_remaining} out of 10 free queries remaining.`);
            }
            
            chatHistory.push({ role: 'user', content: message });
            chatHistory.push({ role: 'assistant', content: data.response });
            
        } catch (error) {
            console.error('Error:', error);
            addMessage('assistant', 'Sorry, there was an error processing your request.');
        } finally {
            followUpButton.disabled = false;
            spinner.classList.add('d-none');
        }
    });

    console.log('All event handlers set up');
}); 