document.addEventListener("DOMContentLoaded", () => {
  const activitiesList = document.getElementById("activities-list");
  const activitySelect = document.getElementById("activity");
  const signupForm = document.getElementById("signup-form");
  const messageDiv = document.getElementById("message");

  function escapeHtml(value) {
    return value
      .replaceAll("&", "&amp;")
      .replaceAll("<", "&lt;")
      .replaceAll(">", "&gt;")
      .replaceAll('"', "&quot;")
      .replaceAll("'", "&#39;");
  }

  function showMessage(text, type) {
    messageDiv.textContent = text;
    messageDiv.className = type;
    messageDiv.classList.remove("hidden");

    setTimeout(() => {
      messageDiv.classList.add("hidden");
    }, 5000);
  }

  // Function to fetch activities from API
  async function fetchActivities() {
    try {
      const response = await fetch("/activities");
      const activities = await response.json();

      // Clear old content and reset select options to avoid duplicates
      activitiesList.innerHTML = "";
      activitySelect.innerHTML = '<option value="">-- Select an activity --</option>';

      // Populate activities list
      Object.entries(activities).forEach(([name, details]) => {
        const activityCard = document.createElement("div");
        activityCard.className = "activity-card";

        const spotsLeft = details.max_participants - details.participants.length;

        const participantItems = details.participants.length > 0
          ? details.participants.map((participantEmail) => `
            <li>
              <span class="participant-email">${escapeHtml(participantEmail)}</span>
              <button
                type="button"
                class="remove-participant-btn"
                data-activity="${escapeHtml(name)}"
                data-email="${escapeHtml(participantEmail)}"
                aria-label="Remove ${escapeHtml(participantEmail)} from ${escapeHtml(name)}"
                title="Remove participant"
              >
                <svg aria-hidden="true" xmlns="http://www.w3.org/2000/svg" width="13" height="13" viewBox="0 0 24 24" fill="currentColor">
                  <path d="M3 6h18v2H3V6zm2 3h14l-1.5 13h-11L5 9zm5-6h4v2h-4V3z"/>
                </svg>
              </button>
            </li>
          `).join("")
          : `<li class="no-participants">No participants yet</li>`;

        activityCard.innerHTML = `
          <h4>${name}</h4>
          <p>${details.description}</p>
          <p><strong>Schedule:</strong> ${details.schedule}</p>
          <p><strong>Availability:</strong> <span class="spots-badge ${spotsLeft === 0 ? 'spots-full' : ''}"> ${spotsLeft} spot${spotsLeft !== 1 ? 's' : ''} left</span></p>
          <div class="participants-section">
            <button type="button" class="participants-toggle" aria-expanded="false">
              <span>Participants (${details.participants.length}/${details.max_participants})</span>
              <svg class="toggle-chevron" aria-hidden="true" xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="currentColor">
                <path d="M7 10l5 5 5-5z"/>
              </svg>
            </button>
            <ul class="participants-list" hidden>${participantItems}</ul>
          </div>
        `;

        activitiesList.appendChild(activityCard);

        // Add option to select dropdown
        const option = document.createElement("option");
        option.value = name;
        option.textContent = name;
        activitySelect.appendChild(option);
      });
    } catch (error) {
      activitiesList.innerHTML = "<p>Failed to load activities. Please try again later.</p>";
      console.error("Error fetching activities:", error);
    }
  }

  // Confirmation modal logic
  const confirmModal = document.getElementById("confirm-modal");
  const modalBody = document.getElementById("modal-body");
  const modalCancel = document.getElementById("modal-cancel");
  const modalConfirm = document.getElementById("modal-confirm");
  let pendingRemoval = null;
  let lastFocusedElement = null;

  function isModalOpen() {
    return !confirmModal.classList.contains("hidden");
  }

  function getModalFocusableElements() {
    const focusableSelector = 'button, [href], input, select, textarea, [tabindex]:not([tabindex="-1"])';
    return Array.from(confirmModal.querySelectorAll(focusableSelector)).filter((element) => !element.disabled);
  }

  function canReceiveFocus(element) {
    return Boolean(
      element
      && document.contains(element)
      && typeof element.focus === "function"
      && !element.disabled
      && element.getClientRects().length > 0
    );
  }

  function openConfirmModal(activity, email) {
    pendingRemoval = { activity, email };
    lastFocusedElement = document.activeElement;
    modalBody.textContent = `Remove "${email}" from "${activity}"?`;
    confirmModal.classList.remove("hidden");
    modalConfirm.focus();
  }

  function closeConfirmModal() {
    confirmModal.classList.add("hidden");
    pendingRemoval = null;
    if (canReceiveFocus(lastFocusedElement)) {
      lastFocusedElement.focus();
    }
    lastFocusedElement = null;
  }

  modalCancel.addEventListener("click", closeConfirmModal);

  confirmModal.addEventListener("click", (event) => {
    if (event.target === confirmModal) closeConfirmModal();
  });

  document.addEventListener("keydown", (event) => {
    if (!isModalOpen()) return;

    if (event.key === "Escape") {
      event.preventDefault();
      closeConfirmModal();
      return;
    }

    if (event.key !== "Tab") return;

    const focusableElements = getModalFocusableElements();
    if (focusableElements.length === 0) {
      event.preventDefault();
      return;
    }

    const firstFocusable = focusableElements[0];
    const lastFocusable = focusableElements[focusableElements.length - 1];
    const isFocusOutsideModal = !confirmModal.contains(document.activeElement);

    if (event.shiftKey) {
      if (document.activeElement === firstFocusable || isFocusOutsideModal) {
        event.preventDefault();
        lastFocusable.focus();
      }
      return;
    }

    if (document.activeElement === lastFocusable || isFocusOutsideModal) {
      event.preventDefault();
      firstFocusable.focus();
    }
  });

  modalConfirm.addEventListener("click", async () => {
    if (!pendingRemoval) return;
    const { activity, email } = pendingRemoval;
    closeConfirmModal();

    try {
      const response = await fetch(
        `/activities/${encodeURIComponent(activity)}/participants?email=${encodeURIComponent(email)}`,
        { method: "DELETE" }
      );
      const result = await response.json();

      if (!response.ok) {
        showMessage(result.detail || "Could not remove participant", "error");
        return;
      }

      showMessage(result.message, "success");
      fetchActivities();
    } catch (error) {
      showMessage("Failed to remove participant. Please try again.", "error");
      console.error("Error removing participant:", error);
    }
  });

  activitiesList.addEventListener("click", (event) => {
    const toggleButton = event.target.closest(".participants-toggle");
    if (toggleButton) {
      const list = toggleButton.nextElementSibling;
      const isExpanded = toggleButton.getAttribute("aria-expanded") === "true";
      toggleButton.setAttribute("aria-expanded", String(!isExpanded));
      if (isExpanded) {
        list.hidden = true;
      } else {
        list.hidden = false;
      }
      return;
    }

    const removeButton = event.target.closest(".remove-participant-btn");
    if (!removeButton) return;
    openConfirmModal(removeButton.dataset.activity, removeButton.dataset.email);
  });

  // Handle form submission
  signupForm.addEventListener("submit", async (event) => {
    event.preventDefault();

    const email = document.getElementById("email").value;
    const activity = document.getElementById("activity").value;

    try {
      const response = await fetch(
        `/activities/${encodeURIComponent(activity)}/signup?email=${encodeURIComponent(email)}`,
        {
          method: "POST",
        }
      );

      const result = await response.json();

      if (response.ok) {
        showMessage(result.message, "success");
        signupForm.reset();
        fetchActivities();
      } else {
        showMessage(result.detail || "An error occurred", "error");
      }
    } catch (error) {
      showMessage("Failed to sign up. Please try again.", "error");
      console.error("Error signing up:", error);
    }
  });

  // Initialize app
  fetchActivities();
});
