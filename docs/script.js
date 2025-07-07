// docs/script.js
document.addEventListener('DOMContentLoaded', async function() {
    try {
        const response = await fetch('results.json');
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        const results = await response.json();
        renderCharts(results);
        renderFindings(results);
    } catch (error) {
        const main = document.querySelector('main');
        main.innerHTML = `<p style="text-align:center; color:red;">Could not load analysis results. Please ensure a pull request has been analyzed.</p>`;
        console.error("Failed to load or parse results.json:", error);
    }
});

function renderCharts(results) {
    const { tool_names } = results.metadata;
    const { findings_by_tool, findings_by_category } = results.summary_charts;

    // Chart 1: Total Findings by Tool
    const findingsByToolCtx = document.getElementById('findingsByToolChart').getContext('2d');
    new Chart(findingsByToolCtx, {
        type: 'bar',
        data: {
            labels: tool_names,
            datasets: [{
                label: 'Number of Findings',
                data: findings_by_tool,
                backgroundColor: ['#3498db', '#e74c3c', '#9b59b6', '#2ecc71'],
            }]
        },
        options: { indexAxis: 'y', responsive: true, plugins: { legend: { display: false } } }
    });

    // Chart 2: Findings by Category
    const findingsByCategoryCtx = document.getElementById('findingsByCategoryChart').getContext('2d');
    new Chart(findingsByCategoryCtx, {
        type: 'doughnut',
        data: {
            labels: findings_by_category.labels,
            datasets: [{
                data: findings_by_category.data,
                backgroundColor: ['#e74c3c', '#f1c40f', '#3498db', '#95a5a6'],
            }]
        },
        options: { responsive: true }
    });
}

function renderFindings(results) {
    const container = document.getElementById('detailed-findings');
    if (results.findings.length === 0) {
        container.innerHTML = '<p>No findings were reported by the automated tools for this pull request.</p>';
        return;
    }

    results.findings.forEach(finding => {
        const card = document.createElement('div');
        card.className = 'finding-card';

        let reviewsHTML = '';
        finding.reviews.forEach(review => {
            const toolClassName = review.tool.replace(/\s+/g, '-');
            reviewsHTML += `
                <div class="tool-review ${toolClassName}">
                    <h4>${review.tool}</h4>
                    <blockquote>${escapeHtml(review.comment)}</blockquote>
                </div>
            `;
        });

        card.innerHTML = `
            <div class="finding-card-header">
                <h3><code>${finding.location}</code></h3>
                <span class="category ${finding.category.toLowerCase().replace(/ /g, '-')}">${finding.category}</span>
            </div>
            <div class="finding-card-body">${reviewsHTML}</div>
        `;
        container.appendChild(card);
    });
}

function escapeHtml(unsafe) {
    return unsafe
        .replace(/&/g, "&amp;")
        .replace(/</g, "&lt;")
        .replace(/>/g, "&gt;")
        .replace(/"/g, "&quot;")
        .replace(/'/g, "&#039;");
}