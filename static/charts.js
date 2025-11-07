/* Monthly + Category chart initializer.
   Expects:
   - monthlyData: [{month: 'YYYY-MM', amount: Number}]
   - categoryData: [{category: 'Food', amount: Number}]
*/

(function () {
  if (typeof Chart === "undefined") return;

  // Reports page
  if (typeof monthlyData !== "undefined") {
    const mLabels = monthlyData.map(d => d.month);
    const mValues = monthlyData.map(d => Number(d.amount || 0));
    const ctxM = document.getElementById("monthlyChart");
    if (ctxM) new Chart(ctxM, {
      type: "line",
      data: { labels: mLabels, datasets: [{ label: "Monthly Spend", data: mValues }] },
      options: { responsive: true }
    });
  }

  if (typeof categoryData !== "undefined" && document.getElementById("categoryChart")) {
    const cLabels = categoryData.map(d => d.category);
    const cValues = categoryData.map(d => Number(d.amount || 0));
    const ctxC = document.getElementById("categoryChart");
    if (ctxC) new Chart(ctxC, {
      type: "pie",
      data: { labels: cLabels, datasets: [{ label: "By Category", data: cValues }] },
      options: { responsive: true }
    });
  }

  // Stats page (alternate IDs)
  if (typeof categoryData !== "undefined" && document.getElementById("cat")) {
    const cLabels2 = categoryData.map(d => d.category);
    const cValues2 = categoryData.map(d => Number(d.amount || 0));
    new Chart(document.getElementById("cat"), {
      type: "bar",
      data: { labels: cLabels2, datasets: [{ label: "Category Spend", data: cValues2 }] },
      options: { responsive: true }
    });
  }

  if (typeof monthData !== "undefined" && document.getElementById("mon")) {
    const mLabels2 = monthData.map(d => d.month);
    const mValues2 = monthData.map(d => Number(d.amount || 0));
    new Chart(document.getElementById("mon"), {
      type: "line",
      data: { labels: mLabels2, datasets: [{ label: "Monthly Spend", data: mValues2 }] },
      options: { responsive: true }
    });
  }
})();