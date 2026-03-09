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
});
