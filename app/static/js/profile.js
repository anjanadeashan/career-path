// Profile page interactions (handling dynamic skill additions/deletions and spinners)
document.addEventListener('DOMContentLoaded', () => {
    const uploadForm = document.getElementById('upload-resume-form');
    const uploadBtn = document.getElementById('upload-btn');
    const uploadSpinner = document.getElementById('upload-spinner');
    
    // 1. Show spinner on resume upload
    if (uploadForm && uploadBtn) {
        uploadForm.addEventListener('submit', () => {
            uploadBtn.disabled = true;
            if (uploadSpinner) {
                uploadSpinner.classList.remove('d-none');
            }
        });
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
