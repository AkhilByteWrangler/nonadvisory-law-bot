import React from 'react';
import { Link } from 'react-router-dom';
import './App.css';

const features = [
  {
    title: 'AI-Powered Legal Chat',
    desc: 'Get instant, non-advisory legal information from a state-of-the-art language model trained on legal data.'
  },
  {
    title: 'Private & Secure',
    desc: 'Your conversations are confidential and never shared. Enjoy peace of mind with secure chat.'
  },
  {
    title: 'Emoji Feedback',
    desc: 'React to bot answers with emojis and help us improve the service with your feedback.'
  },
  {
    title: 'Modern iMessages UI',
    desc: 'Experience a beautiful, animated, Apple-inspired chat interface with dark mode and smooth transitions.'
  },
  {
    title: 'Easy Access',
    desc: 'No complex signup. Use a simple sign-in to get started instantly.'
  },
];

function Landing() {
  return (
    <div className="landing-container landing-animate-bg">
      <div className="landing-hero landing-fade-in">
        <img
          src="https://images.unsplash.com/photo-1506744038136-46273834b3fb?auto=format&fit=crop&w=800&q=80"
          alt="Modern Law Bot Hero"
          className="landing-hero-img landing-img-animate"
        />
        <div className="landing-hero-content">
          <h1 className="landing-title landing-title-animate">Welcome to <span className="landing-title-gradient">LawBot</span></h1>
          <p className="landing-subtitle landing-subtitle-animate">
            Your trusted, AI-powered legal assistant.<br />
            Get instant, non-advisory legal information in a secure, private chat.
          </p>
          <Link to="/login" className="landing-btn landing-btn-animate">Sign In</Link>
        </div>
      </div>
      <div className="landing-features-row">
        {features.map((f, i) => (
          <div className="landing-feature-card landing-fade-in" key={i} style={{ animationDelay: `${0.2 + i * 0.15}s` }}>
            <h3 className="feature-title">{f.title}</h3>
            <p className="feature-desc">{f.desc}</p>
          </div>
        ))}
      </div>
      <footer className="landing-footer landing-footer-animate">
        <span>© {new Date().getFullYear()} LawBot. All rights reserved.</span>
      </footer>
    </div>
  );
}

export default Landing;
