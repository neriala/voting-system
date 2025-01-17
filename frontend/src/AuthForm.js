import React, { useState } from "react";
import axios from "axios";

const AuthForm = ({ onAuthenticated }) => {
  const [nationalId, setNationalId] = useState("");
  const [error, setError] = useState("");

  const handleAuth = async (e) => {
    e.preventDefault();
    setError("");

    try {
      const response = await axios.post("http://127.0.0.1:5000/authenticate", {
        national_id: nationalId,
      });
      onAuthenticated(nationalId); // העברת ת"ז ל-Toplevel Component
    } catch (error) {
      setError(error.response?.data?.error || "An error occurred.");
    }
  };

  return (
    <div>
      <h2>Authenticate Voter</h2>
      <form onSubmit={handleAuth}>
        <input
          type="text"
          placeholder="Enter National ID"
          value={nationalId}
          onChange={(e) => setNationalId(e.target.value)}
        />
        <button type="submit">Authenticate</button>
      </form>
      {error && <p style={{ color: "red" }}>{error}</p>}
    </div>
  );
};

export default AuthForm;
