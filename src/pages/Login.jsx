import React, { useState, useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import { ArrowRight, ArrowLeft, Mail } from 'lucide-react'
import './Login.css'

function Login() {
  const navigate = useNavigate()
  const [activePage, setActivePage] = useState('signIn')
  const [resetEmail, setResetEmail] = useState('')
  const [showResetSuccess, setShowResetSuccess] = useState(false)

  const showPage = (pageId) => {
    setActivePage(pageId)
    setShowResetSuccess(false)
  }

  const resetForgotPassword = () => {
    setShowResetSuccess(false)
  }

  const handleSignIn = async (e) => {
    e.preventDefault()
    const formData = new FormData(e.target)
    const email = formData.get('email')
    const password = formData.get('password')

    try {
      const res = await fetch('/api/login', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ email, password })
      })

      const data = await res.json()

      if (!res.ok) {
        alert(data.error)
        return
      }

      alert('Login successful')
      navigate('/dashboard')
    } catch (err) {
      alert('Login failed')
    }
  }

  const handleSignUp = async (e) => {
    e.preventDefault()
    const formData = new FormData(e.target)
    const name = formData.get('name')
    const email = formData.get('email')
    const password = formData.get('password')
    const confirmPassword = formData.get('confirmPassword')

    if (password !== confirmPassword) {
      alert('Passwords do not match')
      return
    }

    try {
      const res = await fetch('/api/signup', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ name, email, password })
      })

      const data = await res.json()

      if (!res.ok) {
        alert(data.error)
        return
      }

      alert('Account created. Please sign in.')
      setActivePage('signIn')
    } catch (err) {
      alert('Signup failed')
    }
  }

  const handleForgotPassword = async (e) => {
    e.preventDefault()
    const formData = new FormData(e.target)
    const email = formData.get('email')

    try {
      const res = await fetch('/api/forgot-password', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ email })
      })

      if (!res.ok) {
        alert('Email not registered')
        return
      }

      setResetEmail(email)
      setShowResetSuccess(true)
    } catch (err) {
      alert('Request failed')
    }
  }

  return (
    <div className="login-container">
      {/* Sign In Page */}
      {activePage === 'signIn' && (
        <div className="min-h-screen bg-gradient">
          <div className="container">
            <div className="auth-card">
              <div className="text-center mb-8">
                <h1>Welcome Back</h1>
                <p className="subtitle">Sign in to continue to MediAssist</p>
              </div>

              <form onSubmit={handleSignIn} className="space-y-6">
                <div className="form-group">
                  <label htmlFor="signInEmail">Email Address</label>
                  <div className="input-container">
                    <input
                      id="signInEmail"
                      name="email"
                      type="email"
                      placeholder="Enter your email"
                      required
                    />
                  </div>
                </div>

                <div className="form-group">
                  <label htmlFor="signInPassword">Password</label>
                  <div className="input-container">
                    <input
                      id="signInPassword"
                      name="password"
                      type="password"
                      placeholder="Enter your password"
                      required
                    />
                  </div>
                </div>

                <div className="flex-between">
                  <div className="checkbox-container">
                    <input type="checkbox" id="rememberMe" />
                    <label htmlFor="rememberMe">Remember me</label>
                  </div>
                  <button
                    type="button"
                    className="link"
                    onClick={() => setActivePage('forgotPassword')}
                  >
                    Forgot password?
                  </button>
                </div>

                <button type="submit" className="btn-primary">
                  Sign In
                </button>
              </form>

              <p className="text-center mt-6">
                Don't have an account?{' '}
                <button
                  type="button"
                  className="link"
                  onClick={() => setActivePage('signUp')}
                >
                  Sign up
                </button>
              </p>
            </div>
          </div>
        </div>
      )}

      {/* Sign Up Page */}
      {activePage === 'signUp' && (
        <div className="min-h-screen bg-gradient">
          <div className="container">
            <div className="auth-card">
              <div className="text-center mb-8">
                <h1>Create Account</h1>
                <p className="subtitle">Join MediAssist and start your journey</p>
              </div>

              <form onSubmit={handleSignUp} className="space-y-6">
                <div className="form-group">
                  <label htmlFor="fullName">Full Name</label>
                  <div className="input-container">
                    <input
                      id="fullName"
                      name="name"
                      type="text"
                      placeholder="Enter your full name"
                      required
                    />
                  </div>
                </div>

                <div className="form-group">
                  <label htmlFor="signUpEmail">Email Address</label>
                  <div className="input-container">
                    <input
                      id="signUpEmail"
                      name="email"
                      type="email"
                      placeholder="Enter your email"
                      required
                    />
                  </div>
                </div>

                <div className="form-group">
                  <label htmlFor="signUpPassword">Password</label>
                  <div className="input-container">
                    <input
                      id="signUpPassword"
                      name="password"
                      type="password"
                      placeholder="Create a password"
                      required
                    />
                  </div>
                </div>

                <div className="form-group">
                  <label htmlFor="confirmPassword">Confirm Password</label>
                  <div className="input-container">
                    <input
                      id="confirmPassword"
                      name="confirmPassword"
                      type="password"
                      placeholder="Confirm your password"
                      required
                    />
                  </div>
                </div>

                <div className="checkbox-container">
                  <input type="checkbox" id="terms" required />
                  <label htmlFor="terms">
                    I agree to the <a href="#" className="link">Terms of Service</a>
                    {' '}and <a href="#" className="link">Privacy Policy</a>
                  </label>
                </div>

                <button type="submit" className="btn-primary">
                  Create Account
                  <ArrowRight size={20} />
                </button>
              </form>

              <p className="text-center mt-6">
                Already have an account?{' '}
                <button
                  type="button"
                  className="link"
                  onClick={() => setActivePage('signIn')}
                >
                  Sign in
                </button>
              </p>
            </div>
          </div>
        </div>
      )}

      {/* Forgot Password Page */}
      {activePage === 'forgotPassword' && (
        <div className="min-h-screen bg-gradient">
          <div className="container">
            <div className="auth-card">
              <button
                type="button"
                className="back-link"
                onClick={() => setActivePage('signIn')}
              >
                <ArrowLeft size={16} />
                Back to Sign In
              </button>

              {!showResetSuccess ? (
                <div className="reset-container">
                  <div className="text-center mb-8">
                    <h1>Reset Password</h1>
                    <p className="subtitle">
                      Enter your email address and we'll send you instructions to reset your password
                    </p>
                  </div>

                  <form onSubmit={handleForgotPassword} className="space-y-6">
                    <div className="form-group">
                      <label htmlFor="resetEmail">Email Address</label>
                      <div className="input-container">
                        <input
                          id="resetEmail"
                          name="email"
                          type="email"
                          placeholder="Enter your email"
                          required
                        />
                      </div>
                    </div>

                    <button type="submit" className="btn-primary">
                      Send Reset Instructions
                      <ArrowRight size={20} />
                    </button>
                  </form>
                </div>
              ) : (
                <div className="reset-success">
                  <div className="icon-circle">
                    <Mail size={32} />
                  </div>
                  <h2>Check Your Email</h2>
                  <p className="success-message">
                    We've sent password reset instructions to:
                    <br />
                    <span id="resetEmailDisplay">{resetEmail}</span>
                  </p>
                  <button
                    type="button"
                    onClick={resetForgotPassword}
                    className="btn-link"
                  >
                    Try another email address
                  </button>
                </div>
              )}
            </div>
          </div>
        </div>
      )}
    </div>
  )
}

export default Login
