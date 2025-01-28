import React, { useState, useEffect } from "react";
import axios from "axios";
import CryptoJS from "crypto-js";

function VoteForm({ graph, sharedKey, centerId, onTimeout }) {
  const [selectedOption, setSelectedOption] = useState("");
  const [message, setMessage] = useState("");
  const [isLoading, setIsLoading] = useState(false);
  const [timeLeft, setTimeLeft] = useState(10); // 10 שניות להצבעה
  const graphString = JSON.stringify(graph);
  const encryptedGraph = CryptoJS.SHA256(graphString).toString();

  // ספירה לאחור (טיימר)
  useEffect(() => {
    if (timeLeft <= 0) {
      onTimeout(); // קריאה לפונקציית ניתוק
    }

    const timer = setInterval(() => {
      setTimeLeft((prevTime) => prevTime - 1);
    }, 1000);

    return () => clearInterval(timer); // נקה את הטיימר כשיש שינוי
  }, [timeLeft, onTimeout]);

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
      setIsLoading(true);
      const key = CryptoJS.SHA256(sharedKey.toString()).toString();
      const parsedKey = CryptoJS.enc.Hex.parse(key);

      const nonce = CryptoJS.lib.WordArray.random(16).toString();
      const payload = { vote: selectedOption, nonce: nonce };

      const encryptedVote = CryptoJS.AES.encrypt(
        JSON.stringify(payload),
        parsedKey,
        {
          mode: CryptoJS.mode.ECB,
          padding: CryptoJS.pad.Pkcs7,
        }
      ).toString();

      console.log("Encrypted Vote:", encryptedVote);

      const response = await axios.post("http://127.0.0.1:5000/vote", {
        encryptedGraph: encryptedGraph,
        encrypted_vote: encryptedVote,
        center_id: centerId,
      });

      console.log("Server Response:", response.data);
      setMessage("Vote submitted successfully!");
      setTimeout(() => {
        window.location.reload(); // רענון העמוד הראשי
      }, 2000);
    } catch (error) {
      console.error("Error during encryption or request:", error);
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div>
      <h2>Vote for Your Candidate</h2>
      <h3>Time Left: {timeLeft} seconds</h3> {/* שעון הצבעה */}
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
