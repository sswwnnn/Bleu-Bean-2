import React, { useState } from "react";
import { Link, useNavigate } from "react-router-dom"; 
import "./login.css";
import logo from "../assets/bleu_logo1.jpg";
import coffeeImage from "../assets/coffee/CaramelMachiatto.jpg";


const Login = () => {
  const [credentials, setCredentials] = useState({ username: "", password: "" });
  const [passwordVisible, setPasswordVisible] = useState(false);
  const navigate = useNavigate();

  const handleLogin = async(e) => {
    e.preventDefault();

    try {
      const response = await fetch("http://localhost:8000/auth/token", {
        method: "POST",
        headers: { "Content-Type": "application/x-www-form-urlencoded" },
        body: new URLSearchParams({
          username: credentials.username,
          password: credentials.password,
        })
      });

      const data = await response.json();
      
      if (response.ok) {
        console.log("Login successful:", data);

        const token = data.access_token;
        localStorage.setItem("token", token);

        const payload = JSON.parse(atob(token.split(".")[1]));
        const userRole = payload.role;
        
        if (userRole === "admin") navigate("/admin-home");
        else if (userRole === "staff") navigate("/staff-home");
        else if (userRole === "manager") navigate("/manager-home");
      } else {
        alert(data.message || "Incorrect username or password");
      }
    } catch (error) {
      console.error("Error during login:", error);
      alert("An error occurred. Please try again.");
    }
  };

  return (
    <div className="login-page">
      <div className="login-container">
        <div className="login-box">
          <img src={logo} alt="Bleu Bean Cafe" className="logo" />
          <h2>Welcome Back</h2>
          <p>Please Enter Your Details To Log In.</p>

          <form onSubmit={handleLogin}>
            <label>Username</label>
            <input
              type="text"
              placeholder="Enter your username"
              value={credentials.username}
              onChange={(e) => setCredentials({ ...credentials, username: e.target.value })}
            />

            <label>Password</label>
            <div className="password-container">
              <input
                type={passwordVisible ? "text" : "password"}
                placeholder="Enter your password"
                value={credentials.password}
                onChange={(e) => setCredentials({ ...credentials, password: e.target.value })}
              />
              <span
                className="eye-icon material-symbols-outlined"
                onClick={() => setPasswordVisible(!passwordVisible)}
              >
                {passwordVisible ? "visibility_off" : "visibility"}
              </span>
            </div>

            <div className="remember-me">
              <input type="checkbox" id="remember" />
              <label htmlFor="remember">Remember Me</label>
            </div>

            <button type="submit">Log In</button>

            <p className="forgot-password">
              Forgot Password? <Link to="/reset-password">Reset Here</Link>
            </p>
          </form>
        </div>
      </div>

      <div className="image-container">
        <img src={coffeeImage} alt="Caramel Macchiato" className="coffee-image" />
      </div>
    </div>
  );
};

export default Login;