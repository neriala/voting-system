import React, { useState } from "react";
import axios from "axios";
import AddVoterForm from "./AddVoterForm";

function App() {
  const [authenticated, setAuthenticated] = useState(false); // האם המשתמש מאומת
  const [nationalId, setNationalId] = useState(""); // ת"ז של המשתמש
  const [selectedOption, setSelectedOption] = useState(""); // אפשרות שנבחרה
  const [message, setMessage] = useState(""); // הודעה למשתמש

  // פונקציה לאימות ת"ז
  const handleAuth = async (e) => {
    e.preventDefault();

    if (!nationalId) {
      alert("Please enter your National ID!");
      return;
    }

    try {
      const response = await axios.post("http://127.0.0.1:5000/authenticate", {
        national_id: nationalId,
      });
      alert(response.data.message); // הצגת הודעת הצלחה
      setAuthenticated(true); // סימון שהמשתמש מאומת
    } catch (error) {
      alert(error.response?.data?.error || "Authentication failed!");
    }
  };

  // פונקציה לשליחת ההצבעה
  const handleVote = async (e) => {
    e.preventDefault();
    if (!selectedOption) {
      alert("Please select an option!");
      return;
    }

    try {
      const response = await axios.post("http://127.0.0.1:5000/vote", {
        national_id: nationalId,
        vote: selectedOption,
      });
      setMessage(response.data.message); // הצגת הודעת הצלחה
    } catch (error) {
      setMessage(error.response?.data?.error || "Error submitting vote.");
    }
  };

  return (
    
    <div style={{ textAlign: "center", padding: "20px" }}>
      <h1>Voting System</h1>
      
      {!authenticated ? (
        // טופס אימות
        <form onSubmit={handleAuth}>
          <h2>Authenticate to Vote</h2>
          <input
            type="text"
            placeholder="Enter National ID"
            value={nationalId}
            onChange={(e) => setNationalId(e.target.value)}
          />
          <br />
          <button type="submit" style={{ marginTop: "10px" }}>
            Authenticate
          </button>
        </form>
      ) : (
        // טופס הצבעה
        <form onSubmit={handleVote}>
          <h2>Vote for Your Candidate</h2>
          <label>
            <input
              type="radio"
              name="vote"
              value="Candidate A"
              onChange={(e) => setSelectedOption(e.target.value)}
            />
            Candidate A
          </label>
          <br />
          <label>
            <input
              type="radio"
              name="vote"
              value="Candidate B"
              onChange={(e) => setSelectedOption(e.target.value)}
            />
            Candidate B
          </label>
          <br />
          <label>
            <input
              type="radio"
              name="vote"
              value="Candidate C"
              onChange={(e) => setSelectedOption(e.target.value)}
            />
            Candidate C
          </label>
          <br />
          <button type="submit" style={{ marginTop: "10px" }}>
            Submit Vote
          </button>
        </form>
      )}
      {message && <p>{message}</p>}
    </div>
    
  );
}

export default App;
