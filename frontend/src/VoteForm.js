import React, { useState } from "react";
import axios from "axios";
import "./App.css"; // ייבוא קובץ העיצוב
import CryptoJS from "crypto-js";


function VoteForm({ graph, sharedKey, centerId }) {
  const [selectedOption, setSelectedOption] = useState("");
  const [message, setMessage] = useState("");
  const [isLoading, setIsLoading] = useState(false);

  const handleVote = async (e) => {
    e.preventDefault();
  
    if (!selectedOption) {
      alert("Please select an option!");
      return;
    }
  
    if (!sharedKey) {
      alert("Encryption key not available. Please try again.");
      return;
    }
  
    try {
      const key = CryptoJS.SHA256(sharedKey.toString()).toString();
      const parsedKey = CryptoJS.enc.Hex.parse(key);
  
      // יצירת nonce אקראי לכל הצבעה
      const nonce = CryptoJS.lib.WordArray.random(16).toString(); // 16 בתים אקראיים
      console.log("Generated Nonce:", nonce);
  
      // הצפנת ההצבעה יחד עם nonce
      const payload = {
        vote: selectedOption,
        nonce: nonce,
      };
  
      const encryptedVote = CryptoJS.AES.encrypt(
        JSON.stringify(payload),
        parsedKey,
        {
          mode: CryptoJS.mode.ECB,
          padding: CryptoJS.pad.Pkcs7,
        }
      ).toString();
  
      console.log("Encrypted Vote:", encryptedVote);
  
      // שליחת הנתונים לשרת
      const response = await axios.post("http://127.0.0.1:5000/vote", {
        graph: graph,
        encrypted_vote: encryptedVote,
        center_id: centerId,
      });
  
      console.log("Server Response:", response.data);
    } catch (error) {
      console.error("Error during encryption or request:", error);
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
        <button type="submit" disabled={isLoading}>
          {isLoading ? "Submitting..." : "Submit Vote"}
        </button>
      </form>
      {message && <p>{message}</p>}
    </div>
  );
}

export default VoteForm;
