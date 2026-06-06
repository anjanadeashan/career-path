// Profile page interactions (handling dynamic skill additions/deletions and spinners)
document.addEventListener('DOMContentLoaded', () => {
    const uploadForm = document.getElementById('upload-resume-form');
    const uploadBtn = document.getElementById('upload-btn');
    const uploadProgress = document.getElementById('upload-progress');

    // Step animation helpers
    const STEPS = ['step-upload', 'step-parse', 'step-ai', 'step-recs'];
    let stepTimer = null;

    function setStep(stepId, state) {
        const el = document.getElementById(stepId);
        if (!el) return;
        const icon = el.querySelector('.step-icon');
        const label = el.querySelector('span:last-child');
        if (state === 'active') {
            icon.textContent = '●';
            icon.className = 'step-icon text-primary';
            label.className = 'text-white';
        } else if (state === 'done') {
            icon.textContent = '✓';
            icon.className = 'step-icon text-success';
            label.className = 'text-success';
        } else {
            icon.textContent = '○';
            icon.className = 'step-icon text-secondary';
            label.className = 'text-secondary';
        }
    }

    function startStepAnimation() {
        let current = 0;
        setStep(STEPS[0], 'active');
        stepTimer = setInterval(() => {
            setStep(STEPS[current], 'done');
            current++;
            if (current < STEPS.length) {
                setStep(STEPS[current], 'active');
            } else {
                clearInterval(stepTimer);
            }
        }, 5000);
    }

    function finishSteps(success) {
        clearInterval(stepTimer);
        STEPS.forEach(s => setStep(s, success ? 'done' : 'done'));
    }

    // 1. AJAX resume upload with step-by-step progress
    if (uploadForm && uploadBtn) {
        uploadForm.addEventListener('submit', async (e) => {
            e.preventDefault();

            const fileInput = document.getElementById('resume');
            if (!fileInput.files.length) return;

            // Show progress, hide button
            uploadBtn.disabled = true;
            uploadBtn.innerHTML = '<span class="spinner-border spinner-border-sm me-2" role="status" aria-hidden="true"></span>Processing...';
            if (uploadProgress) uploadProgress.classList.remove('d-none');
            startStepAnimation();

            const formData = new FormData(uploadForm);

            try {
                const response = await fetch(uploadForm.action, {
                    method: 'POST',
                    headers: { 'X-Requested-With': 'XMLHttpRequest' },
                    body: formData
                });

                const result = await response.json();
                finishSteps(result.success);

                if (result.success) {
                    showToast(result.message, result.warning ? 'warning' : 'success');
                    // Reload so the updated skills/resume section renders
                    setTimeout(() => { window.location.reload(); }, 1500);
                } else {
                    showToast(result.error || 'Upload failed.', 'danger');
                    resetUploadUI();
                }
            } catch (err) {
                console.error('Upload error:', err);
                finishSteps(false);
                showToast('Upload failed — network error or server timeout. Please try again.', 'danger');
                resetUploadUI();
            }
        });
    }

    function resetUploadUI() {
        if (uploadBtn) {
            uploadBtn.disabled = false;
            uploadBtn.innerHTML = '<i class="fa-solid fa-wand-magic-sparkles"></i> Extract & Match CV';
        }
        if (uploadProgress) uploadProgress.classList.add('d-none');
        STEPS.forEach(s => setStep(s, 'idle'));
    }

    // 2. Set up event listeners for deleting existing skill pills
    const skillContainer = document.getElementById('skills-section-container');
    if (skillContainer) {
        skillContainer.addEventListener('click', async (e) => {
            if (e.target.classList.contains('btn-close-skill')) {
                e.preventDefault();
                const button = e.target;
                const skillName = button.getAttribute('data-skill-name');
                const pill = button.closest('.skill-pill');

                try {
                    const response = await fetch('/profile/skills/delete', {
                        method: 'POST',
                        headers: {
                            'Content-Type': 'application/json'
                        },
                        body: JSON.stringify({ skill_name: skillName })
                    });
                    
                    const result = await response.json();
                    if (result.success) {
                        pill.remove();
                        showToast(`Removed skill: ${skillName}`, 'info');
                    } else {
                        showToast(`Error removing skill: ${result.error}`, 'danger');
                    }
                } catch (err) {
                    console.error("Error deleting skill:", err);
                    showToast("Failed to delete skill. Check network.", "danger");
                }
            }
        });
    }

    // 3. Handle manual skill additions via AJAX
    const addSkillForm = document.getElementById('add-skill-form');
    if (addSkillForm) {
        addSkillForm.addEventListener('submit', async (e) => {
            e.preventDefault();
            const inputField = document.getElementById('skill-input');
            const typeSelect = document.getElementById('skill-type-select');
            
            const skillName = inputField.value.trim();
            const skillType = typeSelect.value;
            
            if (!skillName) return;

            try {
                const response = await fetch('/profile/skills/add', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json'
                    },
                    body: JSON.stringify({ skill_name: skillName, skill_type: skillType })
                });

                const result = await response.json();
                if (result.success) {
                    const savedSkillName = result.skill.skill_name;
                    const savedSkillType = result.skill.skill_type;
                    
                    // Create and append the new pill
                    const targetContainerId = savedSkillType === 'technical' ? 'tech-skills-container' : 'soft-skills-container';
                    const targetContainer = document.getElementById(targetContainerId);
                    
                    if (targetContainer) {
                        // Check if no skills placeholder text is there, clear it
                        const placeholder = targetContainer.querySelector('.text-muted');
                        if (placeholder) placeholder.remove();

                        const pillColorClass = savedSkillType === 'technical' ? 'skill-pill-tech' : 'skill-pill-soft';
                        const newPill = document.createElement('span');
                        newPill.className = `skill-pill ${pillColorClass}`;
                        newPill.innerHTML = `
                            ${savedSkillName}
                            <button type="button" class="btn-close btn-close-skill" data-skill-name="${savedSkillName}" aria-label="Close"></button>
                        `;
                        targetContainer.appendChild(newPill);
                    }
                    
                    inputField.value = ''; // Reset input
                    showToast(`Added skill: ${savedSkillName}`, 'success');
                } else {
                    showToast(`Error adding skill: ${result.error}`, 'danger');
                }
            } catch (err) {
                console.error("Error adding skill:", err);
                showToast("Failed to add skill.", "danger");
            }
        });
    }
});

// Toast/notification utility
function showToast(message, type = 'success') {
    const toastContainer = document.getElementById('toast-container');
    if (!toastContainer) {
        // Create container if it doesn't exist
        const container = document.createElement('div');
        container.id = 'toast-container';
        container.className = 'position-fixed bottom-0 end-0 p-3';
        container.style.zIndex = '1100';
        document.body.appendChild(container);
    }
    
    const container = document.getElementById('toast-container');
    const toast = document.createElement('div');
    toast.className = `toast align-items-center text-white bg-${type} border-0 show m-2`;
    toast.role = 'alert';
    toast.ariaLive = 'assertive';
    toast.ariaAtomic = 'true';
    toast.innerHTML = `
        <div class="d-flex">
            <div class="toast-body">
                ${message}
            </div>
            <button type="button" class="btn-close btn-close-white me-2 m-auto" data-bs-dismiss="toast" aria-label="Close"></button>
        </div>
    `;
    
    container.appendChild(toast);
    
    // Auto-remove after 4 seconds
    setTimeout(() => {
        toast.remove();
    }, 4000);
}
