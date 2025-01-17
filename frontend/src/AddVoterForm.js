import React, { useState } from "react";
import axios from "axios";
import { TextField, Button, Box, Typography, CircularProgress } from "@mui/material";

const AddVoterForm = () => {
  const [nationalId, setNationalId] = useState("");
  const [message, setMessage] = useState("");
  const [loading, setLoading] = useState(false);

  const handleAddVoter = async (e) => {
    e.preventDefault();
    setMessage("");
    setLoading(true);

    try {
      const response = await axios.post("http://127.0.0.1:5000/add_voter", {
        national_id: nationalId,
      });
      setMessage(response.data.message);
    } catch (error) {
      setMessage(error.response?.data?.error || "Failed to add voter.");
    } finally {
      setLoading(false);
    }
  };

  return (
    <Box
      sx={{
        maxWidth: 400,
        margin: "0 auto",
        padding: 2,
        border: "1px solid #ccc",
        borderRadius: 2,
        boxShadow: 3,
      }}
    >
      <Typography variant="h5" sx={{ marginBottom: 2 }}>
        Add Voter
      </Typography>
      <form onSubmit={handleAddVoter}>
        <TextField
          fullWidth
          label="National ID"
          variant="outlined"
          value={nationalId}
          onChange={(e) => setNationalId(e.target.value)}
          required
          sx={{ marginBottom: 2 }}
        />
        <Button
          type="submit"
          variant="contained"
          color="primary"
          fullWidth
          disabled={loading}
        >
          {loading ? <CircularProgress size={24} /> : "Add Voter"}
        </Button>
      </form>
      {message && (
        <Typography
          variant="body1"
          sx={{
            marginTop: 2,
            color: message.includes("successfully") ? "green" : "red",
          }}
        >
          {message}
        </Typography>
      )}
    </Box>
  );
};

export default AddVoterForm;
