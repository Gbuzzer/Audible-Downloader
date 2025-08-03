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
    const chooseFileBtn = document.getElementById('chooseFileBtn');
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

    // Click to upload (only when clicking the upload area itself, not the button)
    uploadArea.addEventListener('click', function(e) {
        // Don't trigger if clicking on the button or its children
        if (e.target.tagName === 'BUTTON' || e.target.closest('button')) {
            return;
        }
        fileInput.click();
    });

    // Choose File button click
    chooseFileBtn.addEventListener('click', function(e) {
        e.stopPropagation(); // Prevent event bubbling
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
        
        // Get selected output format
        const selectedFormat = document.querySelector('input[name="output_format"]:checked');
        formData.append('output_format', selectedFormat ? selectedFormat.value : 'm4b');

        // Simulate progress updates with realistic timing for large files
        let progress = 0;
        const progressInterval = setInterval(() => {
            progress += Math.random() * 8;  // Slower progress for large files
            if (progress > 85) progress = 85;  // Don't go too high until we know it's done
            
            // Update message based on progress
            let message = 'Converting audio file...';
            if (progress > 30) message = 'Processing audio data...';
            if (progress > 60) message = 'Finalizing conversion...';
            
            updateProgress(progress, message);
        }, 2000);  // Update every 2 seconds instead of 1

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
        convertBtn.innerHTML = '<i class="fas fa-magic me-2"></i>Convert Audio File';
    }

    // Show results
    function showResults(data) {
        totalSize.textContent = data.total_size_mb + ' MB';
        downloadBtn.href = data.download_url;
        downloadBtn.download = data.filename;
        
        // Update format display
        const outputFormat = document.getElementById('outputFormat');
        if (outputFormat) {
            outputFormat.textContent = data.output_format || 'MP3';
        }
        
        // Show chunk button if file is large enough
        const chunkBtn = document.getElementById('chunkBtn');
        if (data.can_chunk) {
            chunkBtn.classList.remove('d-none');
            // Store filename for chunking
            chunkBtn.dataset.filename = data.filename;
        } else {
            chunkBtn.classList.add('d-none');
        }
        
        resultContainer.classList.remove('d-none');
        
        // Scroll to results
        resultContainer.scrollIntoView({ behavior: 'smooth' });
    }

    // Hide results
    function hideResults() {
        resultContainer.classList.add('d-none');
        // Also hide chunk results
        const chunkResultContainer = document.getElementById('chunkResultContainer');
        const chunkingContainer = document.getElementById('chunkingContainer');
        chunkResultContainer.classList.add('d-none');
        chunkingContainer.classList.add('d-none');
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
    
    // Chunk file function
    window.chunkFile = function() {
        const chunkBtn = document.getElementById('chunkBtn');
        const filename = chunkBtn.dataset.filename;
        
        if (!filename) {
            showError('No file available for chunking');
            return;
        }
        
        // Show chunking progress
        const chunkingContainer = document.getElementById('chunkingContainer');
        chunkingContainer.classList.remove('d-none');
        
        // Hide the original result and disable chunk button
        chunkBtn.disabled = true;
        chunkBtn.innerHTML = '<i class="fas fa-spinner fa-spin me-2"></i>Chunking...';
        
        // Make request to chunk the file
        fetch('/chunk-file', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ filename: filename })
        })
        .then(response => response.json())
        .then(data => {
            // Hide chunking progress
            chunkingContainer.classList.add('d-none');
            
            if (data.success) {
                // Show chunking results
                showChunkResults(data);
            } else {
                showError(data.error || 'Chunking failed');
                // Re-enable chunk button
                chunkBtn.disabled = false;
                chunkBtn.innerHTML = '<i class="fas fa-cut me-2"></i>Split into 24MB Chunks';
            }
        })
        .catch(error => {
            console.error('Chunking error:', error);
            chunkingContainer.classList.add('d-none');
            showError('Network error during chunking');
            // Re-enable chunk button
            chunkBtn.disabled = false;
            chunkBtn.innerHTML = '<i class="fas fa-cut me-2"></i>Split into 24MB Chunks';
        });
    };
    
    // Show chunk results
    function showChunkResults(data) {
        const chunkCount = document.getElementById('chunkCount');
        const chunkTotalSize = document.getElementById('chunkTotalSize');
        const chunkDownloadBtn = document.getElementById('chunkDownloadBtn');
        const chunkResultContainer = document.getElementById('chunkResultContainer');
        
        chunkCount.textContent = data.total_chunks;
        chunkTotalSize.textContent = data.total_size_mb + ' MB';
        chunkDownloadBtn.href = data.download_url;
        chunkDownloadBtn.download = data.zip_name;
        
        // Hide the original result container and show chunk result
        resultContainer.classList.add('d-none');
        chunkResultContainer.classList.remove('d-none');
        
        // Scroll to chunk results
        chunkResultContainer.scrollIntoView({ behavior: 'smooth' });
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

// Activation Bytes Functions
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

function extractWithAudibleCli() {
    showToast('🔄 Extracting activation bytes with audible-cli...', 'info');
    
    fetch('/extract-activation-bytes', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ method: 'cli' })
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            document.getElementById('activationBytes').value = data.activation_bytes;
            showToast('✅ Activation bytes extracted successfully!', 'success');
        } else {
            showToast('❌ Could not extract activation bytes: ' + data.error, 'error');
        }
    })
    .catch(error => {
        console.error('Error extracting activation bytes:', error);
        showToast('❌ Error extracting activation bytes', 'error');
    });
}
