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
    const {
        findings_by_tool,
        findings_by_category,
        comment_verbosity,
        findings_by_file
    } = results.summary_charts;

    // Chart 1: Total Findings by Tool
    const findingsByToolCtx = document.getElementById('findingsByToolChart').getContext('2d');
    new Chart(findingsByToolCtx, {
        type: 'bar',
        data: {
            labels: tool_names,
            datasets: [{
                label: 'Number of Findings',
                data: findings_by_tool,
                backgroundColor: ['#38BDF8', '#F472B6', '#A78BFA', '#34D399', '#FBBF24'],
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
                backgroundColor: ['#991B1B', '#166534', '#9A3412', '#1E40AF'],
            }]
        },
        options: { responsive: true }
    });

    // --- ADD THE TWO NEW CHART RENDERERS ---

    // Chart 3: Findings per File
    const findingsByFileCtx = document.getElementById('findingsByFileChart').getContext('2d');
    new Chart(findingsByFileCtx, {
        type: 'bar',
        data: {
            labels: findings_by_file.labels,
            datasets: [{
                label: 'Number of Findings',
                data: findings_by_file.data,
                backgroundColor: '#A78BFA', // Purple
            }]
        },
        options: { responsive: true, plugins: { legend: { display: false } } }
    });

    // Chart 4: Comment Verbosity
    const commentVerbosityCtx = document.getElementById('commentVerbosityChart').getContext('2d');
    new Chart(commentVerbosityCtx, {
        type: 'bar',
        data: {
            labels: comment_verbosity.labels,
            datasets: [{
                label: 'Average Characters per Comment',
                data: comment_verbosity.data,
                backgroundColor: '#34D399', // Green
            }]
        },
        options: { responsive: true, plugins: { legend: { display: false } } }
    });
}

function renderFindings(results) {
    const container = document.getElementById('detailed-findings');
    if (!results.findings || results.findings.length === 0) {
        container.innerHTML = '<p>No findings were reported by the automated tools for this pull request.</p>';
        return;
    }

    results.findings.forEach(finding => {
        const card = document.createElement('div');
        card.className = 'finding-card';

        let reviewsHTML = '';

        // Ensure finding.reviews is an array before calling forEach
        if (Array.isArray(finding.reviews)) {
            finding.reviews.forEach(review => {
                const toolClassName = review.tool.replace(/\s+/g, '-');
                reviewsHTML += `
                    <div class="tool-review ${toolClassName}">
                        <h4>${review.tool}</h4>
                        <blockquote>${escapeHtml(review.comment)}</blockquote>
                    </div>
                `;
            });
        }

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
    if (typeof unsafe !== 'string') {
        return '';
    }
    return unsafe
        .replace(/&/g, "&amp;")
        .replace(/</g, "&lt;")
        .replace(/>/g, "&gt;")
        .replace(/"/g, "&quot;")
        .replace(/'/g, "&#039;");
}