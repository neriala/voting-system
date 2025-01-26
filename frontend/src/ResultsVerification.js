import React, { useState, useEffect } from "react";
import axios from "axios";

function ResultsVerification() {
  const [results, setResults] = useState(null);
  const [voteHashes, setVoteHashes] = useState([]);

  useEffect(() => {
    const fetchResults = async () => {
      try {
        const response = await axios.get("http://127.0.0.1:5000/publish_results");
        setResults(response.data.results);
        setVoteHashes(response.data.vote_hashes);
      } catch (error) {
        console.error("Error fetching results:", error);
      }
    };

    fetchResults();
  }, []);

  return (
    <div>
      <h1>Results Verification</h1>
      {results && (
        <div>
          <h3>Final Results:</h3>
          <p>Democratic: {results.Democratic}</p>
          <p>Republican: {results.Republican}</p>
        </div>
      )}
      <h3>Vote Hashes:</h3>
      <ul>
        {voteHashes.map((hash, index) => (
          <li key={index}>{hash}</li>
        ))}
      </ul>
    </div>
  );
}

export default ResultsVerification;
