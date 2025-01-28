import React, { useState } from "react";
import axios from "axios";
import { Bar } from "react-chartjs-2";
import { Chart as ChartJS } from "chart.js/auto";

function ResultsPage() {
  const [results, setResults] = useState(null);
  const [title, setTitle] = useState("Results");

  const fetchResults = async (url, title) => {
    try {
      const response = await axios.post(url);
      setResults(response.data.results || response.data);
      setTitle(title);
    }  catch (error) {
      if (error.response && error.response.status === 400) {
        // שגיאה מהשרת עם קוד 400
        alert(error.response.data.error || "Hash mismatch detected. Please contact support.");
      } else {
        // שגיאה אחרת
        console.error("Error fetching results:", error);
        alert("An error occurred while fetching the results. Please try again later.");
      }
    }
  };

  const data = {
    labels: ["Democratic", "Republican"],
    datasets: [
      {
        label: title,
        data: results ? [results.Democratic, results.Republican] : [0, 0],
        backgroundColor: ["#4caf50", "#ff5722"],
      },
    ],
  };

  return (
    <div style={{ display: "flex", flexDirection: "column", alignItems: "center" }}>
      <h1>Voting Results</h1>
      <div style={{ marginBottom: "20px" }}>
        <button
          onClick={() => fetchResults("http://127.0.0.1:5000/center_count_votes/1", "Center 1 Results")}
          style={{ margin: "5px" }}
        >
          Count Center 1
        </button>
        <button
          onClick={() => fetchResults("http://127.0.0.1:5000/center_count_votes/2", "Center 2 Results")}
          style={{ margin: "5px" }}
        >
          Count Center 2
        </button>
        <button
          onClick={() => fetchResults("http://127.0.0.1:5000/center_count_votes/3", "Center 3 Results")}
          style={{ margin: "5px" }}
        >
          Count Center 3
        </button>
        <button
          onClick={() => fetchResults("http://127.0.0.1:5000/total_count_votes", "Total Results")}
          style={{ margin: "5px" }}
        >
          Count All
        </button>
      </div>
      {results && (
        <div style={{ width: "60%" }}>
          <Bar data={data} />
        </div>
      )}
    </div>
  );
}

export default ResultsPage;
