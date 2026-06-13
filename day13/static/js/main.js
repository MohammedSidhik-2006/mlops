document.addEventListener('DOMContentLoaded', () => {
    const dropzone = document.getElementById('dropzone');
    const fileInput = document.getElementById('file-input');
    const previewContainer = document.getElementById('preview-container');
    const previewImage = document.getElementById('preview-image');
    const confidenceSlider = document.getElementById('confidence-threshold');
    const confidenceValue = document.getElementById('confidence-value');
    const analyzeBtn = document.getElementById('analyze-btn');
    const loadingIndicator = document.getElementById('loading-indicator');
    const errorMessage = document.getElementById('error-message');
    const resultsContainer = document.getElementById('results-container');
    const originalImg = document.getElementById('result-original-img');
    const annotatedImg = document.getElementById('result-annotated-img');
    const detectionDetails = document.getElementById('detection-details');

    let selectedFile = null;

    // Track slider changes
    confidenceSlider.addEventListener('input', (e) => {
        confidenceValue.textContent = parseFloat(e.target.value).toFixed(2);
    });

    // Handle drag and drop events
    ['dragenter', 'dragover'].forEach(eventName => {
        dropzone.addEventListener(eventName, (e) => {
            e.preventDefault();
            e.stopPropagation();
            dropzone.classList.add('dragover');
        }, false);
    });

    ['dragleave', 'drop'].forEach(eventName => {
        dropzone.addEventListener(eventName, (e) => {
            e.preventDefault();
            e.stopPropagation();
            dropzone.classList.remove('dragover');
        }, false);
    });

    dropzone.addEventListener('drop', (e) => {
        const dt = e.dataTransfer;
        const files = dt.files;
        if (files.length > 0) {
            handleFile(files[0]);
        }
    });

    dropzone.addEventListener('click', () => {
        fileInput.click();
    });

    fileInput.addEventListener('change', (e) => {
        if (e.target.files.length > 0) {
            handleFile(e.target.files[0]);
        }
    });

    // File validation and preview
    function handleFile(file) {
        if (!file.type.startsWith('image/')) {
            showError('Please select a valid image file (PNG, JPG, JPEG).');
            return;
        }

        // 10MB limit
        if (file.size > 10 * 1024 * 1024) {
            showError('File size is too large. Max size allowed is 10MB.');
            return;
        }

        selectedFile = file;
        hideError();
        hideResults();

        // Render preview
        const reader = new FileReader();
        reader.onload = (e) => {
            previewImage.src = e.target.result;
            previewContainer.style.display = 'block';
            analyzeBtn.disabled = false;
        };
        reader.readAsDataURL(file);
    }

    // Error helper
    function showError(message) {
        errorMessage.querySelector('.error-text').textContent = message;
        errorMessage.style.display = 'flex';
        loadingIndicator.style.display = 'none';
        analyzeBtn.disabled = false;
    }

    function hideError() {
        errorMessage.style.display = 'none';
    }

    function hideResults() {
        resultsContainer.style.display = 'none';
    }

    // Submit analysis
    analyzeBtn.addEventListener('click', async () => {
        if (!selectedFile) return;

        // Visual feedback
        analyzeBtn.disabled = true;
        hideError();
        hideResults();
        loadingIndicator.style.display = 'flex';

        const formData = new FormData();
        formData.append('image', selectedFile);
        formData.append('confidence', confidenceSlider.value);

        try {
            const response = await fetch('/detect', {
                method: 'POST',
                body: formData
            });

            const data = await response.json();

            if (!response.ok || !data.success) {
                throw new Error(data.error || 'Failed to process image. Server returned an error.');
            }

            renderResults(data);
        } catch (error) {
            showError(error.message);
        } finally {
            loadingIndicator.style.display = 'none';
            analyzeBtn.disabled = false;
        }
    });

    // Render detections and recovery recommendations dynamically
    function renderResults(data) {
        originalImg.src = data.original_image_url + '?t=' + new Date().getTime();
        annotatedImg.src = data.annotated_image_url + '?t=' + new Date().getTime();

        detectionDetails.innerHTML = '';

        if (!data.detections || data.detections.length === 0) {
            // Safe state: No disasters detected
            detectionDetails.innerHTML = `
                <div class="safe-state">
                    <div class="safe-icon">✓</div>
                    <div class="safe-title">No Disaster Detected</div>
                    <div class="safe-desc">The AI model analyzed the image with a confidence threshold of ${(confidenceSlider.value * 100).toFixed(0)}% and found no major disaster damage.</div>
                </div>
            `;
        } else {
            // Create list of detections
            const badgeContainer = document.createElement('div');
            badgeContainer.className = 'disaster-badge-container';

            const summaryTitle = document.createElement('h2');
            summaryTitle.className = 'summary-title';
            summaryTitle.textContent = `Detections (${data.detections.length})`;
            detectionDetails.appendChild(summaryTitle);
            detectionDetails.appendChild(badgeContainer);

            data.detections.forEach((det) => {
                // Determine severity style class
                const sevClass = `severity-${det.severity.toLowerCase()}`;

                const badge = document.createElement('div');
                badge.className = 'detection-badge';
                badge.innerHTML = `
                    <div class="badge-left">
                        <span class="badge-label">${det.class}</span>
                        <span class="badge-conf">${(det.confidence * 100).toFixed(0)}% Conf</span>
                    </div>
                    <span class="severity-tag ${sevClass}">${det.severity} Severity</span>
                `;

                const recCard = document.createElement('div');
                recCard.className = 'recommendations-card';
                recCard.innerHTML = `
                    <h4>Recommended Recovery Actions:</h4>
                    <ul class="recommendation-list">
                        ${det.recommendations.map(rec => `<li>${rec}</li>`).join('')}
                    </ul>
                `;

                const detGroup = document.createElement('div');
                detGroup.className = 'detection-group';
                detGroup.style.display = 'flex';
                detGroup.style.flexDirection = 'column';
                detGroup.style.gap = '0.5rem';
                detGroup.style.marginBottom = '1.5rem';
                detGroup.appendChild(badge);
                detGroup.appendChild(recCard);

                badgeContainer.appendChild(detGroup);
            });
        }

        resultsContainer.style.display = 'flex';
        // Scroll results into view smoothly
        resultsContainer.scrollIntoView({ behavior: 'smooth', block: 'start' });
    }
});
