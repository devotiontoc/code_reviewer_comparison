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
        findings_by_file,
        review_speed,
        suggestion_overlap
    } = results.summary_charts;

    const COLORS = ['#38BDF8', '#F472B6', '#A78BFA', '#34D399', '#FBBF24', '#F87171'];

    // --- Existing Charts ---
    new Chart(document.getElementById('findingsByToolChart').getContext('2d'), {
        type: 'bar', data: { labels: tool_names, datasets: [{ label: 'Number of Findings', data: findings_by_tool, backgroundColor: COLORS }] }, options: { indexAxis: 'y', responsive: true, plugins: { legend: { display: false } } }
    });
    new Chart(document.getElementById('findingsByCategoryChart').getContext('2d'), {
        type: 'doughnut', data: { labels: findings_by_category.labels, datasets: [{ data: findings_by_category.data, backgroundColor: ['#991B1B', '#166534', '#9A3412', '#1E40AF'] }] }, options: { responsive: true }
    });
    new Chart(document.getElementById('findingsByFileChart').getContext('2d'), {
        type: 'bar', data: { labels: findings_by_file.labels, datasets: [{ label: 'Number of Findings', data: findings_by_file.data, backgroundColor: '#A78BFA' }] }, options: { responsive: true, plugins: { legend: { display: false } } }
    });
    new Chart(document.getElementById('commentVerbosityChart').getContext('2d'), {
        type: 'bar', data: { labels: comment_verbosity.labels, datasets: [{ label: 'Average Characters per Comment', data: comment_verbosity.data, backgroundColor: '#34D399' }] }, options: { responsive: true, plugins: { legend: { display: false } } }
    });
    new Chart(document.getElementById('reviewSpeedChart').getContext('2d'), {
        type: 'bar',
        data: { labels: review_speed.labels, datasets: [{ label: 'Average Time to Comment (seconds)', data: review_speed.data, backgroundColor: '#FBBF24', }] },
        options: { responsive: true, plugins: { legend: { display: false }, tooltip: { callbacks: { label: (ctx) => `${ctx.raw} seconds` } } }, scales: { y: { ticks: { callback: value => `${value} s` } } } }
    });

    // --- START: REPLACEMENT FOR VENN DIAGRAM ---
    const overlapCtx = document.getElementById('suggestionOverlapChart').getContext('2d');
    // Filter for actual overlaps and sort them to show the most frequent ones on top
    const overlapData = suggestion_overlap.filter(item => item.sets.length > 1).sort((a, b) => b.size - a.size);

    if (overlapData.length > 0) {
        // Create a horizontal bar chart for the top overlaps
        new Chart(overlapCtx, {
            type: 'bar',
            data: {
                labels: overlapData.map(d => d.sets.join(' & ')),
                datasets: [{
                    label: 'Overlapping Findings',
                    data: overlapData.map(d => d.size),
                    backgroundColor: '#F87171' // Red
                }]
            },
            options: {
                indexAxis: 'y', // This makes the bar chart horizontal
                responsive: true,
                maintainAspectRatio: false,
                plugins: { legend: { display: false } },
                scales: { x: { beginAtZero: true, ticks: { stepSize: 1 } } }
            }
        });
    } else {
        const chartContainer = overlapCtx.canvas.parentNode;
        chartContainer.innerHTML = '<p class="no-data-message">No overlapping findings were detected among the tools.</p>';
    }
    // --- END: REPLACEMENT FOR VENN DIAGRAM ---
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
        if (Array.isArray(finding.reviews)) {
            finding.reviews.forEach(review => {
                const toolClassName = review.tool.replace(/\s+/g, '-');
                let diffHTML = '';
                if (review.original_code && review.suggested_code) {
                    const diffString = `--- a/${finding.location}\n+++ b/${finding.location}\n${review.original_code.split('\n').map(l => `-${l}`).join('\n')}\n${review.suggested_code.split('\n').map(l => `+${l}`).join('\n')}`;
                    diffHTML = Diff2Html.html(diffString, {
                        drawFileList: false,
                        matching: 'lines',
                        outputFormat: 'side-by-side'
                    });
                }
                reviewsHTML += `
                    <div class="tool-review ${toolClassName}">
                        <h4>${review.tool}</h4>
                        <blockquote>${escapeHtml(review.comment)}</blockquote>
                        ${diffHTML ? `<div class="diff-container">${diffHTML}</div>` : ''}
                    </div>`;
            });
        }
        card.innerHTML = `
            <div class="finding-card-header">
                <h3><code>${finding.location}</code></h3>
                <span class="category ${finding.category.toLowerCase().replace(/ /g, '-')}">${finding.category}</span>
            </div>
            <div class="finding-card-body">${reviewsHTML}</div>`;
        container.appendChild(card);
    });
}

function escapeHtml(unsafe) {
    if (typeof unsafe !== 'string') { return ''; }
    return unsafe.replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;").replace(/"/g, "&quot;").replace(/'/g, "&#039;");
}