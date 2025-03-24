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

    // Handle submit button click (with null check)
    if (submitButton) {
        submitButton.addEventListener('click', function() {
            console.log('Submit button clicked');
            if (validateForm()) {
                console.log('Form validation passed');
                handleSubmission();
            } else {
                console.log('Form validation failed');
                addMessage('assistant', 'Please fill in all required fields before submitting.');
            }
        });
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
        const buttonText = submitButton.querySelector('.button-text');
        
        // Generate initial query based on consultation type
        const consultationType = document.querySelector('input[name="consultation-type"]:checked').value;
        const message = consultationType === 'diagnosis' 
            ? 'Please provide diagnosis recommendations based on the provided information.'
            : `Please provide procedure guidelines and checklist for ${document.getElementById('procedure-name').value}.`;

        // Collect patient information
        const patientInfo = {
            consultationType: consultationType,
            procedureName: document.getElementById('procedure-name').value,
            age: document.getElementById('patient-age').value,
            gender: document.getElementById('patient-gender').value,
            chiefComplaint: document.getElementById('chief-complaint').value,
            bp: document.getElementById('bp').value,
            heartRate: document.getElementById('heart-rate').value,
            temperature: document.getElementById('temperature').value,
            spo2: document.getElementById('spo2').value,
            allergies: document.getElementById('allergies').value,
            medicalHistory: document.getElementById('medical-history').value,
            testResults: document.getElementById('test-results').value,
            medications: document.getElementById('medications').value,
            query: message,
            chatHistory: chatHistory
        };

        // Add user message to chat
        addMessage('user', message);

        // Show loading state
        const spinner = submitButton.querySelector('.spinner-border');
        submitButton.disabled = true;
        spinner.classList.remove('d-none');
        buttonText.textContent = 'Processing...';

        try {
            const response = await fetch('/chat', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify(patientInfo)
            });

            const data = await response.json();
            
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
            console.error('Error:', error);
            addMessage('assistant', 'Sorry, there was an error processing your request.');
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

    function addMessage(sender, text) {
        const messageDiv = document.createElement('div');
        messageDiv.className = `message ${sender}-message`;
        
        // Parse markdown-like formatting for checklists and risks
        const formattedText = formatMessage(text);
        messageDiv.innerHTML = formattedText;
        
        messagesArea.appendChild(messageDiv);
        // Only scroll to bottom for user follow-up messages
        if (sender === 'user' && userInput.style.display !== 'none') {
            messagesArea.scrollTop = messagesArea.scrollHeight;
        } else {
            // Keep scrolled to top for initial query and all assistant responses
            messagesArea.scrollTop = 0;
        }
    }

    function formatMessage(text) {
        // Convert markdown-style formatting to HTML with interactive checkboxes for procedures
        return text
            .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
            .replace(/□ (.*)/g, '<div class="checklist-item"><input type="checkbox" class="form-check-input me-2"> $1</div>')  // Interactive checkboxes
            .replace(/!RISK: (.*)/g, '<div class="risk-alert">⚠️ $1</div>')
            .replace(/\[PROTOCOL: (.*?)\]/g, '<div class="protocol-reference">📋 Protocol: $1</div>')
            .replace(/\n/g, '<br>');
    }

    // Add form validation before submission
    function validateForm() {
        const consultationType = document.querySelector('input[name="consultation-type"]:checked').value;
        console.log('Validating form for type:', consultationType);

        const requiredFields = {
            'patient-age': 'Age',
            'patient-gender': 'Gender',
            'chief-complaint': 'Chief Complaint',
            'bp': 'Blood Pressure',
            'heart-rate': 'Heart Rate',
            'temperature': 'Temperature',
            'spo2': 'SpO2'
        };

        // Add procedure name to required fields if in procedure mode
        if (consultationType === 'procedure') {
            requiredFields['procedure-name'] = 'Procedure Name';
        }

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
                field.classList.remove('is-invalid');
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