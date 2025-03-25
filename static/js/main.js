document.addEventListener('DOMContentLoaded', function() {
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

    console.log('DOM Content Loaded');
    console.log('Elements found:', {
        chatForm: !!chatForm,
        patientForm: !!patientForm,
        procedureSection: !!procedureSection,
        submitButton: !!submitButton
    });

    // Chat history
    let chatHistory = [];

    // Set procedure as default
    const procedureRadio = document.getElementById('procedure');
    if (procedureRadio) {
        procedureRadio.checked = true;
    }

    // Show procedure section by default (with null check)
    if (procedureSection) {
        procedureSection.style.display = 'block';
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
        submitButton.addEventListener('click', function(e) {
            console.log('Submit button clicked');
            console.log('Button properties:', {
                disabled: submitButton.disabled,
                display: submitButton.style.display,
                classList: Array.from(submitButton.classList)
            });

            // Prevent any default form submission
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
            patientForm.reset();
            if (messagesArea) messagesArea.innerHTML = '';
            chatHistory = [];
            if (userInput) userInput.value = '';
            if (procedureRadio) procedureRadio.checked = true;
            procedureSection.style.display = 'block';
        });
    }

    // Handle form submission logic
    async function handleSubmission() {
        console.log('Starting form submission');
        const buttonText = submitButton.querySelector('.button-text');
        const spinner = submitButton.querySelector('.spinner-border');
        
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

        // Show loading state
        submitButton.disabled = true;
        spinner.classList.remove('d-none');
        buttonText.textContent = 'Processing...';

        try {
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
            console.log('Response data received');
            
            if (data.show_payment) {
                document.getElementById('payment-container').style.display = 'block';
                return;
            }

            // Add assistant response to chat and update history
            addMessage('assistant', data.response);
            
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
            addMessage('assistant', 'Sorry, there was an error processing your request. Please try again.');
        } finally {
            submitButton.disabled = false;
            spinner.classList.add('d-none');
            buttonText.textContent = 'Get Recommendations';
        }
    }

    // Handle follow-up chat form
    chatForm.addEventListener('submit', async function(e) {
        e.preventDefault();  // Prevent form from submitting normally
        
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

    function formatMessage(text) {
        // First, split the text into sections
        const sections = text.split('\n\n');
        
        return sections.map(section => {
            // Process each section
            return section
                // Headers (must be at start of line)
                .replace(/^### (.*?)$/gm, '<h3>$1</h3>')
                .replace(/^#### (.*?)$/gm, '<h4>$1</h4>')
                
                // Bold text
                .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
                
                // Lists (must be at start of line)
                .replace(/^(\d+)\. (.*?)$/gm, '<div class="numbered-item"><span class="number">$1.</span> $2</div>')
                .replace(/^- (.*?)$/gm, '<div class="bullet-item">• $1</div>')
                
                // Checkboxes (must be at start of line)
                .replace(/^□ (.*?)$/gm, '<div class="checklist-item"><input type="checkbox" class="form-check-input me-2"><span>$1</span></div>')
                
                // Special formatting
                .replace(/^!RISK: (.*?)$/gm, '<div class="risk-alert">⚠️ $1</div>')
                .replace(/^\[PROTOCOL: (.*?)\]$/gm, '<div class="protocol-reference">📋 Protocol: $1</div>')
                
                // Replace remaining newlines with <br>
                .replace(/\n/g, '<br>');
        }).join('<br><br>');
    }

    // Update the style with better formatting
    const style = document.createElement('style');
    style.textContent = `
        .message {
            margin-bottom: 20px;
            padding: 15px;
            border-radius: 8px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.05);
        }

        .assistant-message {
            background-color: #f8f9fa;
            border-left: 4px solid #0d6efd;
        }

        .user-message {
            background-color: #e3f2fd;
            border-left: 4px solid #0d6efd;
            text-align: right;
        }

        .numbered-item, .bullet-item {
            margin: 8px 0;
            padding: 8px;
            background-color: #ffffff;
            border-radius: 4px;
            box-shadow: 0 1px 3px rgba(0,0,0,0.05);
        }

        .numbered-item .number {
            font-weight: bold;
            color: #0d6efd;
            margin-right: 8px;
        }
        
        .checklist-item {
            display: flex;
            align-items: flex-start;
            margin: 8px 0;
            padding: 12px;
            background-color: #ffffff;
            border-radius: 4px;
            box-shadow: 0 1px 3px rgba(0,0,0,0.05);
            transition: all 0.2s ease;
        }
        
        .checklist-item:hover {
            background-color: #f8f9fa;
            transform: translateX(2px);
        }
        
        .checklist-item.completed {
            background-color: #e8f5e9;
            color: #2e7d32;
        }
        
        .checklist-item.completed span {
            text-decoration: line-through;
        }

        .checklist-item input[type="checkbox"] {
            margin-top: 3px;
            margin-right: 12px;
        }
        
        .risk-alert {
            background-color: #fff3cd;
            border: 1px solid #ffeeba;
            color: #856404;
            padding: 15px;
            margin: 12px 0;
            border-radius: 5px;
            box-shadow: 0 1px 3px rgba(0,0,0,0.05);
        }
        
        .protocol-reference {
            background-color: #e9ecef;
            padding: 15px;
            margin: 12px 0;
            border-radius: 5px;
            font-size: 0.9em;
            color: #495057;
            box-shadow: 0 1px 3px rgba(0,0,0,0.05);
        }
        
        h3 {
            font-size: 1.5em;
            color: #2c3e50;
            border-bottom: 2px solid #eee;
            padding-bottom: 8px;
            margin: 20px 0 15px 0;
        }
        
        h4 {
            font-size: 1.2em;
            color: #34495e;
            margin: 15px 0 10px 0;
        }

        .loading-indicator {
            display: flex;
            align-items: center;
            justify-content: center;
            padding: 20px;
            color: #666;
        }

        .loading-indicator .spinner {
            margin-right: 10px;
        }
    `;
    document.head.appendChild(style);

    // Add checkbox functionality
    document.addEventListener('click', function(e) {
        if (e.target && e.target.type === 'checkbox' && e.target.closest('.checklist-item')) {
            const item = e.target.closest('.checklist-item');
            if (e.target.checked) {
                item.classList.add('completed');
            } else {
                item.classList.remove('completed');
            }
        }
    });

    // Update addMessage to show loading state
    function addMessage(sender, text) {
        const messageDiv = document.createElement('div');
        messageDiv.className = `message ${sender}-message`;
        
        if (sender === 'assistant') {
            // Show loading indicator first
            messageDiv.innerHTML = `
                <div class="loading-indicator">
                    <div class="spinner-border spinner-border-sm" role="status"></div>
                    <span>Processing response...</span>
                </div>
            `;
            messagesArea.appendChild(messageDiv);
            
            // Process the message after a short delay
            setTimeout(() => {
                const formattedText = formatMessage(text);
                messageDiv.innerHTML = formattedText;
            }, 100);
        } else {
            messageDiv.innerHTML = text;
        }
        
        messagesArea.appendChild(messageDiv);
        
        if (sender === 'user' && userInput.style.display !== 'none') {
            messagesArea.scrollTop = messagesArea.scrollHeight;
        } else {
            messagesArea.scrollTop = 0;
        }
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

        // For diagnosis type, require all fields
        const requiredFields = {
            'patient-age': 'Age',
            'patient-gender': 'Gender',
            'chief-complaint': 'Chief Complaint',
            'bp': 'Blood Pressure',
            'heart-rate': 'Heart Rate',
            'temperature': 'Temperature',
            'spo2': 'SpO2'
        };

        let isValid = true;
        let firstInvalidField = null;

        for (const [id, label] of Object.entries(requiredFields)) {
            const field = document.getElementById(id);
            console.log('Checking field:', id, 'Value:', field ? field.value : 'field not found');
            
            if (!field || !field.value) {
                isValid = false;
                if (field) {
                    field.classList.add('is-invalid');
                    if (!firstInvalidField) firstInvalidField = field;
                }
                console.log('Invalid field:', label);
            } else {
                if (field) field.classList.remove('is-invalid');
            }
        }

        if (!isValid && firstInvalidField) {
            firstInvalidField.focus();
        }

        console.log('Form validation result:', isValid);
        return isValid;
    }

    document.getElementById('subscribe-button').addEventListener('click', async () => {
        try {
            const response = await fetch('/create-checkout-session', {
                method: 'POST',
            });
            const data = await response.json();
            
            if (data.checkoutUrl) {
                window.location.href = data.checkoutUrl;
            }
        } catch (error) {
            console.error('Error:', error);
            alert('Failed to initialize checkout. Please try again.');
        }
    });

    // Show consent modal if not already accepted
    if (!localStorage.getItem('consentAccepted')) {
        const consentModal = new bootstrap.Modal(document.getElementById('consentModal'));
        consentModal.show();
    }

    // Handle consent checkbox
    document.getElementById('consentCheckbox').addEventListener('change', function() {
        document.getElementById('acceptConsent').disabled = !this.checked;
    });

    // Handle consent acceptance
    document.getElementById('acceptConsent').addEventListener('click', async () => {
        if (document.getElementById('consentCheckbox').checked) {
            const response = await fetch('/accept-consent', {
                method: 'POST'
            });
            if (response.ok) {
                document.querySelector('.alert-info').style.display = 'none';
                document.querySelector('.main-container').style.display = 'block';
            }
        }
    });

    // Initially hide main container until consent
    document.addEventListener('DOMContentLoaded', () => {
        if (!session.get('consent_accepted')) {
            document.querySelector('.main-container').style.display = 'none';
        }
    });
}); 