import React from "react";
import { useNavigate } from "react-router-dom";

const Shomepage = () => {
  const navigate = useNavigate();

  const handleLogout = () => {
    localStorage.removeItem("authToken"); // Remove stored authentication token
    navigate("/login"); // Redirect to login page
  };

  return (
    <div style={{ display: "flex", flexDirection: "column", justifyContent: "center", alignItems: "center", height: "100vh" }}>
      <h1>Hello Manager!</h1>
      <button onClick={handleLogout} style={{ marginTop: "20px", padding: "10px 20px", fontSize: "16px", cursor: "pointer" }}>
        Logout
      </button>
    </div>
  );
};

export default Shomepage;
