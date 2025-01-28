import React, { useEffect, useState } from "react";
import axios from "axios";
import "./App.css"; // ייבוא קובץ העיצוב
import VoteForm from "./VoteForm"; // ייבוא רכיב טופס ההצבעה
import CryptoJS from "crypto-js";
import ResultsPage from "./ResultsPage";
import ResultsVerification from "./ResultsVerification"
import sha256 from "js-sha256";

function App() {
  const [idNumber, setIdNumber] = useState("");
  const [message, setMessage] = useState("");
  const [isAuthenticated, setIsAuthenticated] = useState(false); // מצב לזיהוי אם המשתמש מאומת
  const [showMessage, setShowMessage] = useState(false); // האם להציג הודעה זמנית
  const [sharedKey, setSharedKey] = useState(null); // המפתח המשותף
  const [graph, setGraph] = useState(null); // גרף מאומת
  const [currentPage, setCurrentPage] = useState("home"); // מצב הדף הנוכחי
  const [centerId, setCenterId] = useState(1); // centerId מוגדר כאן
  const [isVoting, setIsVoting] = useState(true); // האם המשתמש בעמוד ההצבעה

  const handleTimeout = () => {
    alert("Time is up! Redirecting to the home page...");
    setIsVoting(false); // עדכון מצב המשתמש
    window.location.reload(); // רענון העמוד הראשי
  };

  useEffect(() => {
    performKeyExchange();
  }, []);
  const performKeyExchange = async () => {
    try {
      const paramsResponse = await axios.get("http://127.0.0.1:5000/dh/params");
      const { p, g, server_public_key } = paramsResponse.data;

      //const clientPrivateKey = Math.floor(Math.random() * 100);
      //const clientPublicKey = (g ** clientPrivateKey) % p;
      const clientPrivateKey = 7;
      const clientPublicKey = (g ** clientPrivateKey) % p;
      const exchangeResponse = await axios.post("http://127.0.0.1:5000/dh/exchange", {
        client_public_key: clientPublicKey,
      });
      
      const sharedKeyBase64 = exchangeResponse.data.shared_key_hash;

      // חישוב המפתח המשותף בצד הלקוח
      const sharedKey = (server_public_key ** clientPrivateKey) % p;
      console.log(sharedKey);
      setSharedKey(sharedKey);

      // חישוב ה-Hash של המפתח המשותף
      const sharedKeyHash = CryptoJS.SHA256(sharedKey.toString()).toString();
      console.log(sharedKeyHash);

      // שליחת ה-Hash לשרת לאימות
      const verifyResponse = await axios.post("http://127.0.0.1:5000/dh/verify", {
        shared_key_hash: sharedKeyHash,
      });

      if (verifyResponse.data.status === "success") {
        console.log("Shared key verified successfully!");
      } else {
        console.error("Shared key verification failed:", verifyResponse.data.message);
      }
    } catch (error) {
      console.error("Error during key exchange:", error);
    }
  };

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
    const computedCenterId = (parseInt(idNumber[idNumber.length - 1]) % 3) + 1;
    setCenterId(computedCenterId);
    
    const graphData = generateGraphFromId(idNumber); // יצירת גרף מת"ז מוצפן
    setGraph(graphData); // שמירת הגרף
    // המרת הגרף למחרוזת JSON
    const graphString = JSON.stringify(graphData);
    console.log(graphString);
    // חישוב SHA-256 של הגרף
    const encryptedGraph = CryptoJS.SHA256(graphString).toString();
    console.log(encryptedGraph);

    try {
      // שליחת ה-SHA-256 לשרת
      const response = await axios.post("http://127.0.0.1:5000/zkp", {
        encryptedGraph, // שולחים את ה-SHA-256
      });

      if (response.data.status === "valid") {
        setShowMessage(true);
        setMessage("You are can vote!");

        setTimeout(() => {
          setShowMessage(false);
          setIsAuthenticated(true);
        }, 2000);
        setShowMessage(false);
      } else {
        setMessage(response.data.message);
      }
    } catch (error) {
      console.error(error);
      setMessage("An error occurred while verifying your ID.");
    }
  };
  
  const generateGraphFromId = (idNumber) => {
    const graph = { nodes: [], edges: [] };

    // יצירת צמתים ייחודיים
    const uniqueNodes = new Set();
    for (let char of idNumber) {
      uniqueNodes.add(parseInt(char)); // המרת הספרה למספר והוספה לסט
    }
    graph.nodes = Array.from(uniqueNodes); // המרת הסט למערך

    // יצירת קשתות בין ספרות סמוכות
    for (let i = 0; i < idNumber.length - 1; i++) {
      const edge = [
        parseInt(idNumber[i]),
        parseInt(idNumber[i + 1]),
      ];
      graph.edges.push(edge);
    }
    graph.nodes.sort((a, b) => a - b); // מיון צמתים בסדר עולה

    console.log("Generated Graph:", graph);
    
    return graph;
  };
  
  
  


  return (
    <div>
      {/* ניווט בין הדפים */}
      {currentPage === "home" && (
        <div>
          <h1>Voting System - Advanced Cryptography</h1>
          {isAuthenticated ? (
            // אם המשתמש מאומת, הצג את רכיב ההצבעה
            <VoteForm graph={graph} sharedKey={sharedKey} centerId={centerId} onTimeout={handleTimeout} />
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

          {/* כפתור מעבר לדף התוצאות */}
          <button
            onClick={() => setCurrentPage("results")}
            style={{ marginTop: "20px" }}
          >
            Go to Results
          </button>
          {/* כפתור מעבר לדף ההוכחות */}
          <button
            onClick={() => setCurrentPage("resultsVerification")}
            style={{ marginTop: "20px" }}
          >
            Go to ResultsVerification
          </button>
        </div>
      )}

      {/* דף התוצאות */}
      {currentPage === "results" && (
        <div>
          <button
            onClick={() => setCurrentPage("home")}
            style={{ marginBottom: "20px" }}
          >
            Back to Home
          </button>
          <ResultsPage sharedKey={sharedKey} />
        </div>
      )}
      {/* דף התוצאות */}
      {currentPage === "resultsVerification" && (
        <div>
          <button
            onClick={() => setCurrentPage("home")}
            style={{ marginBottom: "20px" }}
          >
            Back to Home
          </button>
          <ResultsVerification />
        </div>
      )}
    </div>
  );
}

export default App;