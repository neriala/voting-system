import React, { useState, useEffect } from "react";
import axios from "axios";

function ResultsVerification() {
  const [totalResults, setTotalResults] = useState(null); // תוצאות כוללות
  const [centerResults, setCenterResults] = useState(null); // תוצאות לפי מרכז ספירה
  const [voteHashes, setVoteHashes] = useState([]); // רשימת ה-Hashes להצבעות

  useEffect(() => {
    const fetchResults = async () => {
      try {
        const response = await axios.get("http://127.0.0.1:5000/publish_results");
        setTotalResults(response.data.total_results); // תוצאות כוללות
        setCenterResults(response.data.center_results); // תוצאות לפי מרכז
        setVoteHashes(response.data.vote_hashes); // ה-Hashes של ההצבעות
      } catch (error) {
        console.error("Error fetching results:", error);
      }
    };

    fetchResults();
  }, []);

  return (
    <div style={{ padding: "20px", fontFamily: "Arial, sans-serif" }}>
      <h1 style={{ textAlign: "center", color: "#333" }}>Results Verification</h1>

      {/* תוצאות כוללות */}
      {totalResults && (
        <div>
          <h3>Final Results (All Centers):</h3>
          <p>Democratic: {totalResults.Democratic}</p>
          <p>Republican: {totalResults.Republican}</p>
        </div>
      )}

      {/* תוצאות לפי מרכז */}
      {centerResults && voteHashes && (
        <div>
          <h3>Results by Center:</h3>
          {Object.entries(centerResults).map(([centerId, centerData]) => (
            <div
              key={centerId}
              style={{
                marginBottom: "15px",
                padding: "10px",
                border: "1px solid #ccc",
              }}
            >
              <h4>Center {centerId}:</h4>
              <p>Democratic: {centerData.Democratic}</p>
              <p>Republican: {centerData.Republican}</p>
              <h5>Vote Hashes:</h5>
              <ul style={{ listStyleType: "none", paddingLeft: "0" }}>
                {voteHashes
                  .filter((hashObj) => hashObj.center_id.toString() === centerId) // פילטר לפי ID מרכז
                  .map((hashObj, index) => (
                    <li
                      key={index}
                      style={{
                        marginBottom: "5px",
                        padding: "5px",
                        border: "1px solid #eee",
                      }}
                    >
                      {hashObj.hash}
                    </li>
                  ))}
              </ul>
            </div>
          ))}
        </div>
      )}



    </div>
  );
}

export default ResultsVerification;
