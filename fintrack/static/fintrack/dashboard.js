function renderIncomeChart(config) {
    const ctx = document.getElementById('incomeChart').getContext('2d');
    new Chart(ctx, {
        type: 'pie', 
        data: {
            labels: config.labels,
            datasets: [{
                data: config.data,
                backgroundColor: config.colors,
                borderWidth: 1
            }]
        },
        options: {
            responsive: true,
            plugins: {
                legend: {
                    display: true, // Ensure legend is shown
                    position: 'top',
                    labels: {
                        font: {
                            size: 14
                        },
                        color: '#333'
                    }
                }
            }
        }
    });
}

function renderExpensesChart(config) {
    const ctx = document.getElementById('expensesChart').getContext('2d');
    new Chart(ctx, {
        type: 'pie', 
        data: {
            labels: config.labels,
            datasets: [{
                data: config.data,
                backgroundColor: config.colors 
            }]
        },
        options: {
            responsive: true,
            plugins: {
                legend: {
                    display: true,
                    position: 'top',
                    labels: {
                        font: {
                            size: 14
                        },
                        color: '#333'
                    }
                }
            }
        }
    });
}

function renderBarChart(labels, income, expenses) {
    const ctx = document.getElementById('incomeExpenseChart').getContext('2d');
    if (window.barChart) window.barChart.destroy(); // Destroy existing chart if any
    window.barChart = new Chart(ctx, {
        type: 'bar',
        data: {
            labels: labels,
            datasets: [
                {
                    label: 'Income',
                    data: income,
                    backgroundColor: 'rgba(75, 192, 192, 0.6)',
                    borderColor: 'rgba(75, 192, 192, 1)',
                    borderWidth: 1,
                },
                {
                    label: 'Expenses',
                    data: expenses,
                    backgroundColor: 'rgba(255, 99, 132, 0.6)',
                    borderColor: 'rgba(255, 99, 132, 1)',
                    borderWidth: 1,
                },
            ],
        },
        options: {
            responsive: true,
            scales: {
                x: {
                    stacked: true,
                },
                y: {
                    beginAtZero: true,
                },
            },
        },
    });
}

function fetchPieChartData() {
    fetch('/get-piechart-data/') 
        .then(response => response.json())
        .then(data => {

            renderIncomeChart({
                labels: data.income_labels,
                data: data.income_data,
            });

            renderExpensesChart({
                labels: data.expenses_labels,
                data: data.expenses_data,
            });
        })
        .catch(error => console.error('Error fetching pie chart data:', error));
}

function fetchBarChartData(period) {
    fetch(`/get-barchart-data/${period}/`)
        .then((response) => response.json())
        .then((data) => {
            renderBarChart(data.labels, data.income, data.expenses);
        });
}

document.addEventListener('DOMContentLoaded', () => {

    // Pie Chart logic
    fetchPieChartData();

    // Bar Chart logic
    const buttons = document.querySelectorAll('.toggle-btn');
    buttons.forEach((button) => {
        button.addEventListener('click', () => {
            fetchBarChartData(button.getAttribute('data-period'));
        });
    });

    // Load default chart (months) on page load
    fetchBarChartData('months');
});
