const ctx = document.getElementById('trendChart').getContext('2d');

Papa.parse("assets/metrics.csv", {
  download: true,
  header: true,
  complete: function(results) {
    const labels = results.data.map(row => row.Date);
    const values = results.data.map(row => parseInt(row.CheckIns, 10));

    new Chart(ctx, {
      type: 'line',
      data: {
        labels: labels,
        datasets: [{
          label: "VarAC Wednesday Check-Ins",
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
              text: "Check-In Callsign Count"
            }
          }
        },
        plugins: {
          title: {
            display: true,
            text: "VarAC Check-In Trends Over Time (Unique callsigns)"
          }
        }
      }
    });
  }
});

