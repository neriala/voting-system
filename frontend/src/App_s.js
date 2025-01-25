import React, { useState } from "react";
import axios from "axios";
import VoteForm from "./VoteForm";

function App() {
  const [authenticated, setAuthenticated] = useState(false); // האם המשתמש מאומת
  const [nationalId, setNationalId] = useState(""); // ת"ז של המשתמש

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
        // טופס הצבעה (שנלקח מ-VoteForm.js)
        <VoteForm nationalId={nationalId} />
      )}
    </div>
  );
}

export default App;
