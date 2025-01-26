import React, { useEffect, useState } from "react";
import axios from "axios";
import "./App.css"; // ייבוא קובץ העיצוב
import VoteForm from "./VoteForm"; // ייבוא רכיב טופס ההצבעה
import CryptoJS from "crypto-js";

function App() {
  const [idNumber, setIdNumber] = useState("");
  const [message, setMessage] = useState("");
  const [isAuthenticated, setIsAuthenticated] = useState(false); // מצב לזיהוי אם המשתמש מאומת
  const [showMessage, setShowMessage] = useState(false); // האם להציג הודעה זמנית
  const [sharedKey, setSharedKey] = useState(null); // המפתח המשותף
  const [graph, setGraph] = useState(null); // גרף מאומת

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

    const graphData = generateGraphFromId(idNumber); // יצירת גרף מת"ז
    setGraph(graphData); // שמירת הגרף

    try {
      const response = await axios.post("http://127.0.0.1:5000/zkp", {
        graph: graphData,
      });

      if (response.data.status === "valid") {
        setShowMessage(true);
        setMessage("You are eligible to vote!");

        setTimeout(() => {
          setShowMessage(false);
          setIsAuthenticated(true);
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
    const graph = { nodes: [], edges: [] };
    for (let i = 0; i < idNumber.length; i++) {
      graph.nodes.push(idNumber[i]);
    }
    for (let i = 0; i < idNumber.length - 1; i++) {
      for (let j = i + 1; j < idNumber.length; j++) {
        if ((parseInt(idNumber[i]) + parseInt(idNumber[j])) % 3 === 0) {
          graph.edges.push([idNumber[i], idNumber[j]]);
        }
      }
    }
    return graph;
  };

  const encryptData = (data) => {
    if (!sharedKey) {
      console.error("Shared key not available for encryption.");
      return null;
    }
    const ciphertext = CryptoJS.AES.encrypt(JSON.stringify(data), sharedKey).toString();
    return ciphertext;
  };

  return (
    <div>
      <h1>Voting System - Advanced Cryptography</h1>
      {isAuthenticated ? (
        // אם המשתמש מאומת, הצג את רכיב ההצבעה
        <VoteForm graph={graph} sharedKey={sharedKey}  />
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