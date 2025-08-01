console.log("main.js script parsing started.");

// Toast notification function
function showToast(message, type = 'info') {
    // Remove any existing toast
    const existingToast = document.getElementById('toast');
    if (existingToast) {
        existingToast.remove();
    }
    
    // Create toast element
    const toast = document.createElement('div');
    toast.id = 'toast';
    toast.className = `toast align-items-center text-white bg-${type === 'error' ? 'danger' : type === 'success' ? 'success' : type === 'warning' ? 'warning' : 'info'} border-0 position-fixed top-0 start-50 translate-middle-x mt-3`;
    toast.style.zIndex = '9999';
    toast.setAttribute('role', 'alert');
    toast.setAttribute('aria-live', 'assertive');
    toast.setAttribute('aria-atomic', 'true');
    
    toast.innerHTML = `
        <div class="d-flex">
            <div class="toast-body">
                ${message}
            </div>
            <button type="button" class="btn-close btn-close-white me-2 m-auto" data-bs-dismiss="toast" aria-label="Close"></button>
        </div>
    `;
    
    document.body.appendChild(toast);
    
    // Initialize and show toast
    const bsToast = new bootstrap.Toast(toast, { delay: 3000 });
    bsToast.show();
    
    // Remove toast after it's hidden
    toast.addEventListener('hidden.bs.toast', function() {
        toast.remove();
    });
}

console.log(`showToast function defined: ${typeof showToast}`);

document.addEventListener('DOMContentLoaded', function() {
    console.log("DOMContentLoaded event fired.");
    const uploadArea = document.getElementById('uploadArea');
    const fileInput = document.getElementById('fileInput');
    const uploadForm = document.getElementById('uploadForm');
    const selectedFile = document.getElementById('selectedFile');
    const fileName = document.getElementById('fileName');
    const fileSize = document.getElementById('fileSize');
    const progressContainer = document.getElementById('progressContainer');
    const progressText = document.getElementById('progressText');
    const progressBar = document.querySelector('.progress-bar');
    const resultContainer = document.getElementById('resultContainer');
    const errorContainer = document.getElementById('errorContainer');
    const errorMessage = document.getElementById('errorMessage');
    const convertBtn = document.getElementById('convertBtn');
    const totalChunks = document.getElementById('totalChunks');
    const totalSize = document.getElementById('totalSize');
    const downloadBtn = document.getElementById('downloadBtn');
    


    // Drag and drop functionality
    uploadArea.addEventListener('dragover', function(e) {
        e.preventDefault();
        uploadArea.classList.add('dragover');
    });

    uploadArea.addEventListener('dragleave', function(e) {
        e.preventDefault();
        uploadArea.classList.remove('dragover');
    });

    uploadArea.addEventListener('drop', function(e) {
        e.preventDefault();
        uploadArea.classList.remove('dragover');
        
        const files = e.dataTransfer.files;
        if (files.length > 0) {
            handleFileSelection(files[0]);
        }
    });

    // Click to upload
    uploadArea.addEventListener('click', function() {
        fileInput.click();
    });

    // File input change
    fileInput.addEventListener('change', function(e) {
        if (e.target.files.length > 0) {
            handleFileSelection(e.target.files[0]);
        }
    });

    // Handle file selection
    function handleFileSelection(file) {
        // Validate file type
        const allowedTypes = ['.aax', '.aa'];
        const fileExtension = '.' + file.name.split('.').pop().toLowerCase();
        
        if (!allowedTypes.includes(fileExtension)) {
            showError('Invalid file type. Please select a .aax or .aa file.');
            return;
        }

        // Display selected file
        fileName.textContent = file.name;
        fileSize.textContent = formatFileSize(file.size);
        selectedFile.classList.remove('d-none');
        
        // Hide previous results/errors
        hideResults();
        hideError();
    }

    // Clear file selection
    window.clearFile = function() {
        fileInput.value = '';
        selectedFile.classList.add('d-none');
        hideResults();
        hideError();
    }

    // Format file size
    function formatFileSize(bytes) {
        if (bytes === 0) return '0 Bytes';
        const k = 1024;
        const sizes = ['Bytes', 'KB', 'MB', 'GB'];
        const i = Math.floor(Math.log(bytes) / Math.log(k));
        return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
    }

    // Form submission
    uploadForm.addEventListener('submit', function(e) {
        e.preventDefault();
        
        if (!fileInput.files[0]) {
            showError('Please select a file to convert.');
            return;
        }

        // Show progress
        showProgress();
        hideResults();
        hideError();

        // Prepare form data
        const formData = new FormData();
        formData.append('file', fileInput.files[0]);
        formData.append('activation_bytes', document.getElementById('activationBytes').value);

        // Simulate progress updates
        let progress = 0;
        const progressInterval = setInterval(() => {
            progress += Math.random() * 15;
            if (progress > 90) progress = 90;
            updateProgress(progress, 'Converting and splitting audio...');
        }, 1000);

        // Upload file
        fetch('/upload', {
            method: 'POST',
            body: formData
        })
        .then(response => response.json())
        .then(data => {
            clearInterval(progressInterval);
            hideProgress();
            
            if (data.success) {
                showResults(data);
            } else {
                showError(data.error || 'An error occurred during conversion.');
            }
        })
        .catch(error => {
            clearInterval(progressInterval);
            hideProgress();
            showError('Network error: ' + error.message);
        });
    });

    // Show progress
    function showProgress() {
        progressContainer.classList.remove('d-none');
        convertBtn.disabled = true;
        convertBtn.innerHTML = '<i class="fas fa-spinner fa-spin me-2"></i>Converting...';
        updateProgress(10, 'Starting conversion...');
    }

    // Update progress
    function updateProgress(percent, text) {
        progressBar.style.width = percent + '%';
        progressText.textContent = text;
    }

    // Hide progress
    function hideProgress() {
        progressContainer.classList.add('d-none');
        convertBtn.disabled = false;
        convertBtn.innerHTML = '<i class="fas fa-magic me-2"></i>Convert to MP3';
    }

    // Show results
    function showResults(data) {
        totalChunks.textContent = data.total_chunks;
        totalSize.textContent = data.total_size_mb + ' MB';
        downloadBtn.href = data.download_url;
        downloadBtn.download = data.zip_name;
        resultContainer.classList.remove('d-none');
        
        // Scroll to results
        resultContainer.scrollIntoView({ behavior: 'smooth' });
    }

    // Hide results
    function hideResults() {
        resultContainer.classList.add('d-none');
    }

    // Show error
    function showError(message) {
        errorMessage.textContent = message;
        errorContainer.classList.remove('d-none');
        
        // Scroll to error
        errorContainer.scrollIntoView({ behavior: 'smooth' });
    }

    // Hide error
    function hideError() {
        errorContainer.classList.add('d-none');
    }

    // Auto-hide alerts after 10 seconds
    setInterval(() => {
        if (!resultContainer.classList.contains('d-none')) {
            const resultTime = resultContainer.dataset.showTime;
            if (resultTime && Date.now() - parseInt(resultTime) > 300000) { // 5 minutes
                hideResults();
            }
        }
    }, 30000);

    // Set show time when results are displayed
    const observer = new MutationObserver((mutations) => {
        mutations.forEach((mutation) => {
            if (mutation.type === 'attributes' && mutation.attributeName === 'class') {
                if (!resultContainer.classList.contains('d-none')) {
                    resultContainer.dataset.showTime = Date.now().toString();
                }
            }
        });
    });
    observer.observe(resultContainer, { attributes: true });
});

// Activation Bytes Extraction Functions
function showExtractionModal() {
    const modal = new bootstrap.Modal(document.getElementById('extractionModal'));
    modal.show();
}

function showBrowserInstructions() {
    const modal = new bootstrap.Modal(document.getElementById('browserInstructionsModal'));
    modal.show();
}

function loadSavedActivationBytes() {
    fetch('/load-activation-bytes')
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                document.getElementById('activationBytes').value = data.activation_bytes;
                showToast('✅ Activation bytes loaded successfully!', 'success');
            } else {
                showToast('❌ No saved activation bytes found', 'warning');
            }
        })
        .catch(error => {
            console.error('Error loading activation bytes:', error);
            showToast('❌ Error loading activation bytes', 'error');
        });
}

function extractActivationBytes(method) {
    const extractionStatus = document.getElementById('extractionStatus');
    const extractionResult = document.getElementById('extractionResult');
    const extractionStatusText = document.getElementById('extractionStatusText');
    
    // Show loading state
    extractionStatus.classList.remove('d-none');
    extractionResult.classList.add('d-none');
    
    const requestData = { method: method };
    
    // Update status text based on method
    switch(method) {
        case 'cli':
            extractionStatusText.textContent = 'Using audible-cli to extract activation bytes...';
            break;
        case 'file':
            extractionStatusText.textContent = 'Searching files for activation bytes...';
            break;
        case 'auth':
            extractionStatusText.textContent = 'Authenticating with Audible...';
            break;
        default:
            extractionStatusText.textContent = 'Extracting activation bytes...';
    }
    
    fetch('/extract-activation-bytes', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(requestData)
    })
    .then(response => response.json())
    .then(data => {
        extractionStatus.classList.add('d-none');
        extractionResult.classList.remove('d-none');
        
        const extractionAlert = document.getElementById('extractionAlert');
        const extractionMessage = document.getElementById('extractionMessage');
        
        if (data.success) {
            extractionAlert.className = 'alert alert-success';
            extractionMessage.innerHTML = `
                <i class="fas fa-check-circle me-2"></i>
                <strong>Success!</strong> Activation bytes: <code>${data.activation_bytes}</code>
            `;
            document.getElementById('activationBytes').value = data.activation_bytes;
            showToast('✅ Activation bytes extracted successfully!', 'success');
        } else {
            extractionAlert.className = 'alert alert-warning';
            let suggestions = '';
            if (data.suggestions) {
                suggestions = '<ul class="mb-0 mt-2">';
                data.suggestions.forEach(suggestion => {
                    suggestions += `<li>${suggestion}</li>`;
                });
                suggestions += '</ul>';
            }
            extractionMessage.innerHTML = `
                <i class="fas fa-exclamation-triangle me-2"></i>
                <strong>Could not extract activation bytes</strong><br>
                ${data.error}
                ${suggestions}
            `;
            showToast('⚠️ Could not extract activation bytes', 'warning');
        }
    })
    .catch(error => {
        console.error('Error extracting activation bytes:', error);
        extractionStatus.classList.add('d-none');
        extractionResult.classList.remove('d-none');
        
        const extractionAlert = document.getElementById('extractionAlert');
        const extractionMessage = document.getElementById('extractionMessage');
        
        extractionAlert.className = 'alert alert-danger';
        extractionMessage.innerHTML = `
            <i class="fas fa-times-circle me-2"></i>
            <strong>Error:</strong> ${error.message || 'Failed to extract activation bytes'}
        `;
        showToast('❌ Error extracting activation bytes', 'error');
    });
}

function extractWithCredentials() {
    const email = document.getElementById('audibleEmail').value.trim();
    const password = document.getElementById('audiblePassword').value.trim();
    
    if (!email || !password) {
        showToast('❌ Please enter both email and password', 'error');
        return;
    }
    
    const extractionStatus = document.getElementById('extractionStatus');
    const extractionResult = document.getElementById('extractionResult');
    const extractionStatusText = document.getElementById('extractionStatusText');
    
    extractionStatus.classList.remove('d-none');
    extractionResult.classList.add('d-none');
    extractionStatusText.textContent = 'Authenticating with Audible...';
    
    fetch('/extract-activation-bytes', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
            method: 'auth',
            email: email,
            password: password
        })
    })
    .then(response => response.json())
    .then(data => {
        extractionStatus.classList.add('d-none');
        extractionResult.classList.remove('d-none');
        
        const extractionAlert = document.getElementById('extractionAlert');
        const extractionMessage = document.getElementById('extractionMessage');
        
        if (data.success) {
            extractionAlert.className = 'alert alert-success';
            extractionMessage.innerHTML = `
                <i class="fas fa-check-circle me-2"></i>
                <strong>Success!</strong> Activation bytes: <code>${data.activation_bytes}</code>
            `;
            document.getElementById('activationBytes').value = data.activation_bytes;
            document.getElementById('audiblePassword').value = ''; // Clear password
            showToast('✅ Activation bytes extracted successfully!', 'success');
        } else {
            extractionAlert.className = 'alert alert-danger';
            extractionMessage.innerHTML = `
                <i class="fas fa-times-circle me-2"></i>
                <strong>Authentication failed:</strong> ${data.error}
            `;
            showToast('❌ Authentication failed', 'error');
        }
    })
    .catch(error => {
        console.error('Error:', error);
        showToast('❌ Error during authentication', 'error');
    });
}

function extractWithSelenium() {
    const email = document.getElementById('audibleEmail').value.trim();
    const password = document.getElementById('audiblePassword').value.trim();
    const browser = document.getElementById('seleniumBrowser').value;
    const debug = document.getElementById('seleniumDebug').checked;
    
    if (!email || !password) {
        showToast('❌ Please enter both email and password', 'error');
        return;
    }
    
    const extractionStatus = document.getElementById('extractionStatus');
    const extractionResult = document.getElementById('extractionResult');
    const extractionStatusText = document.getElementById('extractionStatusText');
    
    extractionStatus.classList.remove('d-none');
    extractionResult.classList.add('d-none');
    extractionStatusText.textContent = 'Using Selenium to authenticate with Audible (this may take a moment)...';
    
    fetch('/extract-activation-bytes', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
            method: 'selenium',
            email: email,
            password: password,
            browser: browser,
            debug: debug
        })
    })
    .then(response => response.json())
    .then(data => {
        extractionStatus.classList.add('d-none');
        extractionResult.classList.remove('d-none');
        
        const extractionAlert = document.getElementById('extractionAlert');
        const extractionMessage = document.getElementById('extractionMessage');
        
        if (data.success) {
            extractionAlert.className = 'alert alert-success';
            extractionMessage.innerHTML = `
                <i class="fas fa-check-circle me-2"></i>
                <strong>Success!</strong> Activation bytes: <code>${data.activation_bytes}</code>
                <br><small class="text-muted">Extracted using Selenium automation</small>
            `;
            document.getElementById('activationBytes').value = data.activation_bytes;
            document.getElementById('audiblePassword').value = ''; // Clear password
            showToast('✅ Activation bytes extracted with Selenium!', 'success');
        } else {
            extractionAlert.className = 'alert alert-danger';
            let suggestions = '';
            if (data.suggestions) {
                suggestions = '<ul class="mb-0 mt-2">';
                data.suggestions.forEach(suggestion => {
                    suggestions += `<li>${suggestion}</li>`;
                });
                suggestions += '</ul>';
            }
            extractionMessage.innerHTML = `
                <i class="fas fa-times-circle me-2"></i>
                <strong>Selenium extraction failed:</strong> ${data.error}
                ${suggestions}
                <br><small class="text-muted mt-2 d-block">💡 Try the browser method or check if you have 2FA enabled</small>
            `;
            showToast('❌ Selenium extraction failed', 'error');
        }
    })
    .catch(error => {
        console.error('Error:', error);
        extractionStatus.classList.add('d-none');
        extractionResult.classList.remove('d-none');
        
        const extractionAlert = document.getElementById('extractionAlert');
        const extractionMessage = document.getElementById('extractionMessage');
        
        extractionAlert.className = 'alert alert-danger';
        extractionMessage.innerHTML = `
            <i class="fas fa-times-circle me-2"></i>
            <strong>Error:</strong> ${error.message || 'Selenium extraction failed'}
            <br><small class="text-muted mt-2 d-block">Make sure you have Chrome or Firefox installed. WebDriver will be automatically downloaded.</small>
        `;
        console.log("Calling showToast from general catch block.");
        showToast('❌ Error during Selenium extraction', 'error');
    });
}

function saveManualActivationBytes() {
    const activationBytes = document.getElementById('manualActivationBytes').value.trim().toUpperCase();
    
    if (!activationBytes) {
        showToast('❌ Please enter activation bytes', 'error');
        return;
    }
    
    if (activationBytes.length !== 8 || !/^[0-9A-F]{8}$/.test(activationBytes)) {
        showToast('❌ Activation bytes must be 8 hexadecimal characters', 'error');
        return;
    }
    
    fetch('/extract-activation-bytes', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
            method: 'manual',
            activation_bytes: activationBytes
        })
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            document.getElementById('activationBytes').value = data.activation_bytes;
            document.getElementById('manualActivationBytes').value = '';
            
            const extractionResult = document.getElementById('extractionResult');
            const extractionAlert = document.getElementById('extractionAlert');
            const extractionMessage = document.getElementById('extractionMessage');
            
            extractionResult.classList.remove('d-none');
            extractionAlert.className = 'alert alert-success';
            extractionMessage.innerHTML = `
                <i class="fas fa-check-circle me-2"></i>
                <strong>Saved!</strong> Activation bytes: <code>${data.activation_bytes}</code>
            `;
            showToast('✅ Activation bytes saved successfully!', 'success');
        } else {
            console.log("Calling showToast after Selenium failure:", data.error);
            showToast('❌ ' + data.error, 'error');
        }
    })
    .catch(error => {
        console.error('Error:', error);
        showToast('❌ Error saving activation bytes', 'error');
    });
}
