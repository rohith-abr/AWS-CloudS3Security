
document.addEventListener("DOMContentLoaded", function () {
    const labels = Object.keys(heatmapData);
    const data = Object.values(heatmapData);

    new Chart(document.getElementById('heatmapChart'), {
        type: 'bar',
        data: {
            labels: labels,
            datasets: [{
                label: 'Bucket Size (MB)',
                data: data
            }]
        },
        options: {
            plugins: {
                legend: { display: false }
            },
            scales: {
                y: {
                    beginAtZero: true
                }
            }
        }
    });

    setTimeout(() => {
        location.reload();
    }, 30000); 
});
