// Aegis Response Dashboard Controller

document.addEventListener("DOMContentLoaded", () => {
    // DOM Cache
    const form = document.getElementById("analyzer-form");
    const messageInput = document.getElementById("message-input");
    const locationInput = document.getElementById("location-input");
    const submitBtn = document.getElementById("submit-btn");
    const clearMessageBtn = document.getElementById("clear-message");
    const charCountLabel = document.querySelector(".char-count");
    
    const emptyState = document.getElementById("empty-state");
    const resultsPanel = document.getElementById("results-panel");
    
    const priorityAlert = document.getElementById("priority-alert");
    const priorityValue = document.getElementById("priority-value");
    const priorityMessage = document.getElementById("priority-message");
    const resultLocation = document.getElementById("result-location");
    const categoriesGrid = document.getElementById("categories-grid");
    const suggestionsList = document.getElementById("suggestions-list");
    const confirmDispatchBtn = document.getElementById("confirm-dispatch-btn");
    
    const activityList = document.getElementById("activity-list");
    const clearLogsBtn = document.getElementById("clear-logs");
    
    const toast = document.getElementById("toast");
    const toastMessage = document.getElementById("toast-message");

    // Message Character Count
    messageInput.addEventListener("input", (e) => {
        const count = e.target.value.length;
        charCountLabel.textContent = `${count} character${count === 1 ? "" : "s"}`;
    });

    // Clear Message input
    clearMessageBtn.addEventListener("click", () => {
        messageInput.value = "";
        charCountLabel.textContent = "0 characters";
        messageInput.focus();
    });

    // Load templates
    document.querySelectorAll(".template-btn").forEach(btn => {
        btn.addEventListener("click", (e) => {
            messageInput.value = e.target.getAttribute("data-msg");
            locationInput.value = e.target.getAttribute("data-loc");
            
            // Dispatch dynamic character count trigger
            const count = messageInput.value.length;
            charCountLabel.textContent = `${count} characters`;
            
            // Focus input
            messageInput.focus();
            
            // Auto submit template for quick feedback
            showToast("Template loaded. Analyzing distress signal...");
            triggerAnalysis();
        });
    });

    // Handle Triage Form Submission
    form.addEventListener("submit", (e) => {
        e.preventDefault();
        triggerAnalysis();
    });

    // Function to coordinate Flask Endpoint analysis
    async function triggerAnalysis() {
        const msg = messageInput.value.trim();
        const loc = locationInput.value.trim();
        
        if (!msg) {
            showToast("Please enter a valid distress message first.");
            return;
        }

        // 1. Loading UI State
        submitBtn.disabled = true;
        submitBtn.querySelector(".btn-text").textContent = "Analyzing distress telemetry...";
        submitBtn.querySelector(".spinner").classList.add("show");

        try {
            const response = await fetch("http://127.0.0.1:5000/api/predict", {
                method: "POST",
                headers: {
                    "Content-Type": "application/json"
                },
                body: JSON.stringify({
                    message: msg,
                    location: loc
                })
            });

            const data = await response.json();
            
            if (data.status === "success") {
                renderResults(data);
                appendLogEntry(data);
                showToast("Distress signal triaged successfully.");
            } else {
                showToast(`Analysis failed: ${data.message || "Unknown error"}`);
                resetFormState();
            }
        } catch (error) {
            console.error("Fetch error:", error);
            showToast("Network Error: Make sure your Flask backend server is running.");
            resetFormState();
        }
    }

    function resetFormState() {
        submitBtn.disabled = false;
        submitBtn.querySelector(".btn-text").textContent = "Analyze Situation";
        submitBtn.querySelector(".spinner").classList.remove("show");
    }

    // Render results in output card console
    function renderResults(data) {
        // Toggle Panel view
        emptyState.classList.add("hidden");
        resultsPanel.classList.remove("hidden");
        resetFormState();

        // Update location
        resultLocation.textContent = data.location || "Unknown Location";

        // Update priority alert UI styles
        priorityAlert.className = `priority-alert ${data.priority.toLowerCase()}`;
        priorityValue.textContent = data.priority;
        
        if(data.priority === "HIGH") {
            priorityMessage.textContent = "Critical emergency. Immediate action required.";
        } else if (data.priority === "MEDIUM") {
            priorityMessage.textContent = "This situation requires attention.";
        } else {
            priorityMessage.textContent = "Standard response procedures apply.";
        }

        // Render detected active and inactive categories
        categoriesGrid.innerHTML = "";
        
        const allLabels = Object.keys(data.predictions);
        allLabels.sort((a, b) => data.predictions[b] - data.predictions[a]);

        allLabels.forEach(label => {
            const isActive = data.predictions[label] === 1;
            const chip = document.createElement("span");
            
            const readableName = label.replace(/_/g, " ");
            chip.textContent = readableName;
            
            if (!isActive) {
                chip.style.opacity = "0.35";
                chip.style.background = "var(--gray)";
            }
            
            categoriesGrid.appendChild(chip);
        });

        // Render checklist recommendations
        suggestionsList.innerHTML = "";
        data.suggestions.forEach(suggestion => {
            const item = document.createElement("li");
            item.textContent = suggestion;
            suggestionsList.appendChild(item);
        });
    }

    // Append output logs to dispatch table
    function appendLogEntry(data) {
        const noActivity = activityList.querySelector(".no-activity");
        if (noActivity) {
            noActivity.remove();
        }

        const item = document.createElement("div");
        item.className = "activity-item";
        
        const timestamp = new Date().toLocaleTimeString();
        
        item.innerHTML = `
            <div class="activity-time">${timestamp}</div>
            <div class="activity-location">📍 ${escapeHtml(data.location) || "Unknown"}</div>
            <div class="activity-message">"${escapeHtml(data.message)}"</div>
            <div class="activity-priority ${data.priority.toLowerCase()}">${data.priority}</div>
        `;

        activityList.insertBefore(item, activityList.firstChild);
    }

    // Clear operational log tables
    clearLogsBtn.addEventListener("click", () => {
        activityList.innerHTML = '<p class="no-activity">No incidents logged yet</p>';
        showToast("Dispatch logs cleared.");
    });

    // Confirm dispatch action button handler
    confirmDispatchBtn.addEventListener("click", () => {
        showToast("Incident dispatch broadcast sent to rescue field squads!");
        if (activityList.firstChild && !activityList.querySelector(".no-activity")) {
            activityList.firstChild.style.boxShadow = "inset 0 0 10px rgba(16, 185, 129, 0.2)";
            setTimeout(() => {
                activityList.firstChild.style.boxShadow = "none";
            }, 2000);
        }
    });

    // Helper: Toast Notifications manager
    let toastTimeout;
    function showToast(message) {
        clearTimeout(toastTimeout);
        toastMessage.textContent = message;
        toast.classList.remove("hidden");
        
        toastTimeout = setTimeout(() => {
            toast.classList.add("hidden");
        }, 3500);
    }

    // Helper: HTML escaping
    function escapeHtml(text) {
        if (!text) return "";
        return text
            .replace(/&/g, "&amp;")
            .replace(/</g, "&lt;")
            .replace(/>/g, "&gt;")
            .replace(/"/g, "&quot;")
            .replace(/'/g, "&#039;");
    }
});
