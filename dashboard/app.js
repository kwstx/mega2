document.addEventListener("DOMContentLoaded", () => {
    const heatmapContainer = document.getElementById("heatmap-container");

    const times = ["2pm", "1pm", "12am", "11am", "10am", "9am", "8am"];
    const days = ["Sun", "Mon", "Tue", "Wed", "Thu", "Fri", "Sat"];

    // Provide some sample data to create an appealing heatmap pattern
    // 0 = dark, 1 = striped, 2 = med, 3 = light
    const data = [
        [0, 1, 0, 0, 0, 1, 0], // 2pm
        [1, 1, 1, 2, 2, 1, 1], // 1pm
        [1, 2, 2, 3, 2, 2, 1], // 12am
        [0, 2, 2, 3, 3, 2, 0], // 11am
        [0, 1, 1, 2, 1, 1, 0], // 10am
        [0, 0, 1, 1, 1, 0, 0], // 9am
        [0, 0, 0, 0, 0, 0, 0], // 8am
    ];

    // Generate HTML for the grid
    let gridHTML = "";

    // Body rows
    times.forEach((time, rowIndex) => {
        gridHTML += `<div class="hm-label">${time}</div>`;
        data[rowIndex].forEach(cellVal => {
            let cellClass = "";
            if (cellVal === 0) cellClass = "dark";
            else if (cellVal === 1) cellClass = "striped";
            else if (cellVal === 2) cellClass = "med";
            else if (cellVal === 3) cellClass = "light";

            gridHTML += `<div class="hm-cell ${cellClass}"></div>`;
        });
    });

    // Footer row (Empty bottom-left cell + Days)
    gridHTML += `<div class="hm-label"></div>`;
    days.forEach(day => {
        gridHTML += `<div class="hm-x-label">${day}</div>`;
    });


    heatmapContainer.innerHTML = gridHTML;

    // Toast Notification Logic
    function showNotification(title, message) {
        const container = document.getElementById('notification-container');
        if (!container) return;

        const toast = document.createElement('div');
        toast.className = 'toast-notification';

        toast.innerHTML = `
            <div class="toast-icon">
                <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                    <path d="M13 2L3 14h9l-1 8 10-12h-9l1-8z" />
                </svg>
            </div>
            <div class="toast-content">
                <div class="toast-title">${title}</div>
                <div class="toast-message">${message}</div>
            </div>
            <button class="toast-close">
                <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                    <line x1="18" y1="6" x2="6" y2="18"></line>
                    <line x1="6" y1="6" x2="18" y2="18"></line>
                </svg>
            </button>
        `;

        container.appendChild(toast);

        // Add event listener to close button
        toast.querySelector('.toast-close').addEventListener('click', () => {
            toast.classList.remove('show');
            setTimeout(() => toast.remove(), 400);
        });

        // Trigger animation
        setTimeout(() => {
            toast.classList.add('show');
        }, 100);

        // Auto remove after 10 seconds
        setTimeout(() => {
            if (toast.parentElement) {
                toast.classList.remove('show');
                setTimeout(() => toast.remove(), 400);
            }
        }, 10000);
    }

    // Fetch notification from backend or use fallback
    async function fetchNotification() {
        try {
            const response = await fetch('http://localhost:8000/api/schedule');
            const data = await response.json();
            if (data.notification) {
                showNotification("Smart Schedule Update", data.notification);
            } else {
                // If backend does not provide it, use fallback
                showNotification("Actionable Recommendation", "Charging your EV at 2 AM saves €1.50 today. (AI selected lowest-cost periods before 07:00)");
            }
        } catch (error) {
            console.log("Backend offline, using fallback notification");
            // Fallback for demonstration transparency
            showNotification("Actionable Recommendation", "Charging your EV at 2 AM saves €1.50 today. (AI selected lowest-cost periods before 07:00)");
        }
    }

    // Show notification shortly after page load
    setTimeout(fetchNotification, 1500);

});
