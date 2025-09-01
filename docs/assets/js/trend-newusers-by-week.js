const ctx2 = document.getElementById('trendChart-newusers-by-week').getContext('2d');

Papa.parse("assets/metrics_new_users_by_week.csv", {
  download: true,
  header: true,
  complete: function(results) {
    const labels = results.data.map(row => row.date);
    const values = results.data.map(row => parseInt(row.count, 10));

    new Chart(ctx2, {
      type: 'line',
      data: {
        labels: labels,
        datasets: [{
          label: "VarAC Wednesday New Users",
          data: values,
          borderColor: "rgba(54, 162, 235, 1)",
          backgroundColor: "rgba(54, 162, 235, 0.2)",
          tension: 0.4,
          pointRadius: 4,
          pointHoverRadius: 6,
          fill: true
        }]
      },
      options: {
        responsive: true,
        scales: {
          x: {
            title: {
              display: true,
              text: "Date"
            }
          },
          y: {
            beginAtZero: true,
            title: {
              display: true,
              text: "Number of new users (callsigns)"
            }
          }
        },
        plugins: {
          title: {
            display: true,
            text: "VarAC Wednesday new users by week (Number of callsigns)"
          }
        }
      }
    });
  }
});

