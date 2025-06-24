import React, { useState } from 'react';
import './App.css';
import { useNavigate } from 'react-router-dom';

const dummyUsers = [
  { username: 'alice', password: 'password123', name: 'Alice Johnson' },
  { username: 'bob', password: 'securepass', name: 'Bob Smith' },
];

function Login({ setUser }) {
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState('');
  const navigate = useNavigate();

  const handleSubmit = (e) => {
    e.preventDefault();
    const found = dummyUsers.find(
      (u) => u.username === username && u.password === password
    );
    if (found) {
      setUser(found);
      setError('');
      navigate('/chat');
    } else {
      setError('Invalid username or password');
    }
  };

  return (
    <div className="login-container">
      <div className="login-card">
        <img
          src="https://images.unsplash.com/photo-1515378791036-0648a3ef77b2?auto=format&fit=crop&w=400&q=80"
          alt="Sign In"
          className="login-img"
        />
        <h2 className="login-title">Sign In to LawBot</h2>
        <form onSubmit={handleSubmit} className="login-form">
          <input
            type="text"
            placeholder="Username"
            value={username}
            onChange={(e) => setUsername(e.target.value)}
            className="login-input"
            autoFocus
          />
          <input
            type="password"
            placeholder="Password"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            className="login-input"
          />
          {error && <div className="login-error">{error}</div>}
          <button type="submit" className="login-btn">Sign In</button>
        </form>
      </div>
    </div>
  );
}

export default Login;
