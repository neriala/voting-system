import React, { useState } from "react";
import axios from "axios";
import "./App.css"; // ייבוא קובץ העיצוב
import VoteForm from "./VoteForm"; // ייבוא רכיב טופס ההצבעה

function App() {
  const [idNumber, setIdNumber] = useState("");
  const [message, setMessage] = useState("");
  const [isAuthenticated, setIsAuthenticated] = useState(false); // מצב לזיהוי אם המשתמש מאומת
  const [showMessage, setShowMessage] = useState(false); // האם להציג הודעה זמנית

  // פונקציה לבדיקת תקינות מספר זיהוי
  function isValidNationalId(id) {
    if (id.length !== 9 || isNaN(id)) {
      return false;
    }

    let counter = 0;

    for (let i = 0; i < 9; i++) {
      let digit = parseInt(id[i]) * ((i % 2) + 1); // הכפלת הספרה
      if (digit > 9) {
        digit -= 9;
      }
      counter += digit;
    }

    return counter % 10 === 0;
  }

  const handleSubmit = async (e) => {
    e.preventDefault();

    // בדיקת תקינות ת"ז
    if (!isValidNationalId(idNumber)) {
      setMessage("Invalid National ID. Please check the number and try again.");
      return;
    }

    const graphData = generateGraphFromId(idNumber); // יצירת גרף מהת"ז
    console.log(graphData);
    try {
      const response = await axios.post("http://127.0.0.1:5000/zkp", {
        graph: graphData, // שליחת הגרף לשרת
      });

      if (response.data.status === "valid") {
        setShowMessage(true); // הצגת ההודעה
        setMessage("You are eligible to vote!"); // הודעת הצלחה

        // לאחר 3 שניות, מעבר לטופס ההצבעה
        setTimeout(() => {
          setShowMessage(false); // הסתרת ההודעה
          setIsAuthenticated(true); // עדכון מצב כמשתמש מאומת
        }, 3000);
      } else {
        setMessage(response.data.message);
      }
    } catch (error) {
      console.error(error);
      setMessage("An error occurred while verifying your ID.");
    }
  };

  // פונקציה ליצירת גרף מת"ז
  const generateGraphFromId = (idNumber) => {
    const graph = { nodes: [], edges: [] }; // גרף עם צמתים וקשתות
    for (let i = 0; i < idNumber.length; i++) {
      graph.nodes.push(idNumber[i]); // הוספת צומת
    }
    for (let i = 0; i < idNumber.length - 1; i++) {
      for (let j = i + 1; j < idNumber.length; j++) {
        if ((parseInt(idNumber[i]) + parseInt(idNumber[j])) % 3 === 0) {
          graph.edges.push([idNumber[i], idNumber[j]]); // הוספת קשת
        }
      }
    }
    return graph;
  };

  return (
    <div>
      <h1>Voting System - Advanced Cryptography</h1>
      {isAuthenticated ? (
        // אם המשתמש מאומת, הצג את רכיב ההצבעה
        <VoteForm nationalId={idNumber} />
      ) : (
        // אם המשתמש לא מאומת, הצג את טופס האימות
        <form onSubmit={handleSubmit}>
          <input
            type="text"
            placeholder="Enter your 9-digit ID"
            value={idNumber}
            onChange={(e) => setIdNumber(e.target.value)}
          />
          <br />
          <button type="submit" style={{ marginTop: "10px" }}>
            Submit
          </button>
        </form>
      )}
      {/* הצגת הודעה זמנית */}
      {message && <p>{message}</p>}
    </div>
  );
}

export default App;