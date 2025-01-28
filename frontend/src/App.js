import React, { useEffect, useState } from "react";
import axios from "axios";
import "./App.css"; 
import VoteForm from "./VoteForm"; 
import CryptoJS from "crypto-js";
import ResultsPage from "./ResultsPage";
import ResultsVerification from "./ResultsVerification"


function App() {
  const [idNumber, setIdNumber] = useState("");
  const [message, setMessage] = useState("");
  const [isAuthenticated, setIsAuthenticated] = useState(false); 
  const [showMessage, setShowMessage] = useState(false); 
  const [sharedKey, setSharedKey] = useState(null); 
  const [graph, setGraph] = useState(null); 
  const [currentPage, setCurrentPage] = useState("home"); 
  const [centerId, setCenterId] = useState(1); 
  const [isVoting, setIsVoting] = useState(true); 

  const handleTimeout = () => {
    alert("Time is up! Redirecting to the home page...");
    setIsVoting(false);
    window.location.reload(); 
  };

  useEffect(() => {
    performKeyExchange();
  }, []);
  const performKeyExchange = async () => {
    try {
      const paramsResponse = await axios.get("http://127.0.0.1:5000/dh/params");
      const { p, g, server_public_key } = paramsResponse.data;

      const clientPrivateKey = 7;
      const clientPublicKey = (g ** clientPrivateKey) % p;
      const exchangeResponse = await axios.post("http://127.0.0.1:5000/dh/exchange", {
        client_public_key: clientPublicKey,
      });
      

      //calc shared key
      const sharedKey = (server_public_key ** clientPrivateKey) % p;
      setSharedKey(sharedKey);

      const sharedKeyHash = CryptoJS.SHA256(sharedKey.toString()).toString();
      console.log(sharedKeyHash);

      // verify response
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

  // check valid of israel id
  function isValidNationalId(id) {
    if (id.length !== 9 || isNaN(id)) {
      return false;
    }

    let counter = 0;

    for (let i = 0; i < 9; i++) {
      let digit = parseInt(id[i]) * ((i % 2) + 1); 
      if (digit > 9) {
        digit -= 9;
      }
      counter += digit;
    }

    return counter % 10 === 0;
  }

  const handleSubmit = async (e) => {
    e.preventDefault();
  
    if (!isValidNationalId(idNumber)) {
      setMessage("Invalid National ID. Please check the number and try again.");
      return;
    }
    const computedCenterId = (parseInt(idNumber[idNumber.length - 1]) % 3) + 1;
    setCenterId(computedCenterId);
    
    const graphData = generateGraphFromId(idNumber); //create graph
    setGraph(graphData); 
    
    const graphString = JSON.stringify(graphData);
    console.log(graphString);
    
    const encryptedGraph = CryptoJS.SHA256(graphString).toString();
    console.log(encryptedGraph);

    try {
      // send graph for zkp
      const response = await axios.post("http://127.0.0.1:5000/zkp", {
        encryptedGraph, 
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
  
  //create graph from id
  const generateGraphFromId = (idNumber) => {
    const graph = { nodes: [], edges: [] };

    const uniqueNodes = new Set();
    for (let char of idNumber) {
      uniqueNodes.add(parseInt(char)); 
    }
    graph.nodes = Array.from(uniqueNodes); 

    for (let i = 0; i < idNumber.length - 1; i++) {
      const edge = [
        parseInt(idNumber[i]),
        parseInt(idNumber[i + 1]),
      ];
      graph.edges.push(edge);
    }
    graph.nodes.sort((a, b) => a - b); 
 
    return graph;
  };
  
  
  


  return (
    <div>
      {currentPage === "home" && (
        <div>
          <h1>Voting System - Advanced Cryptography</h1>
          {isAuthenticated ? (
            // if user can vote 
            <VoteForm graph={graph} sharedKey={sharedKey} centerId={centerId} onTimeout={handleTimeout} />
          ) : (
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
          {message && <p>{message}</p>}
          {/* RESULT*/}
          <button
            onClick={() => setCurrentPage("results")}
            style={{ marginTop: "20px" }}
          >
            Go to Results
          </button>
          {/* VERIFY */}
          <button
            onClick={() => setCurrentPage("resultsVerification")}
            style={{ marginTop: "20px" }}
          >
            Go to ResultsVerification
          </button>
        </div>
      )}

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