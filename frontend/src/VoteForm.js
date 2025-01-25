import React, { useState } from "react";
import axios from "axios";
import "./App.css"; // ייבוא קובץ העיצוב

function VoteForm({ nationalId }) {
  const [selectedOption, setSelectedOption] = useState(""); // אפשרות שנבחרה
  const [message, setMessage] = useState(""); // הודעה למשתמש
  const [isLoading, setIsLoading] = useState(false); // מצביע לתהליך פעיל

  // פונקציה לשליחת ההצבעה
  const handleVote = async (e) => {
    e.preventDefault();
    if (!selectedOption) {
      alert("Please select an option!");
      return;
    }

    setIsLoading(true); // התחלת תהליך טעינה
    setMessage(""); // איפוס ההודעה הקודמת

    try {
      const response = await axios.post("http://127.0.0.1:5000/vote", {
        national_id: nationalId,
        vote: selectedOption,
      });
      setMessage(response.data.message); // הצגת הודעת הצלחה
    } catch (error) {
      setMessage(error.response?.data?.error || "Error submitting vote.");
    } finally {
      setIsLoading(false); // סיום תהליך טעינה
    }
  };

  return (
    <div>
      <h2>Vote for Your Candidate</h2>
      <form onSubmit={handleVote}>
        <label>
          <input
            type="radio"
            name="vote"
            value="Democratic"
            onChange={(e) => setSelectedOption(e.target.value)}
          />
          Democratic Party
        </label>
        <br />
        <label>
          <input
            type="radio"
            name="vote"
            value="Republican"
            onChange={(e) => setSelectedOption(e.target.value)}
          />
          Republican Party
        </label>
        <br />
        
        <br />
        <button type="submit" style={{ marginTop: "10px" }} disabled={isLoading}>
          {isLoading ? "Submitting..." : "Submit Vote"}
        </button>
      </form>

      {/* מצביע תהליך */}
      {isLoading && <p>Submitting your vote, please wait...</p>}

      {/* הצגת הודעה למשתמש */}
      {message && <p>{message}</p>}
    </div>
  );
}

export default VoteForm;
