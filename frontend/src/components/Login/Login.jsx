import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../../context/AuthContext';
import { Mail, Lock, User, ArrowRight, ArrowLeft } from 'lucide-react';
import './Login.css';

const Login = () => {
  const [page, setPage] = useState('signIn');
  const [formData, setFormData] = useState({
    name: '',
    email: '',
    password: '',
    confirmPassword: '',
  });
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);
  const [resetEmail, setResetEmail] = useState('');
  const [showResetSuccess, setShowResetSuccess] = useState(false);
  
  const { login, signup } = useAuth();
  const navigate = useNavigate();

  const handleChange = (e) => {
    setFormData({ ...formData, [e.target.name]: e.target.value });
    setError('');
  };

  const handleSignIn = async (e) => {
    e.preventDefault();
    setLoading(true);
    setError('');

    try {
      await login(formData.email, formData.password);
      navigate('/dashboard');
    } catch (err) {
      setError(err.response?.data?.error || 'Login failed');
    } finally {
      setLoading(false);
    }
  };

  const handleSignUp = async (e) => {
    e.preventDefault();
    setError('');

    if (formData.password !== formData.confirmPassword) {
      setError('Passwords do not match');
      return;
    }

    setLoading(true);
    try {
      await signup(formData.name, formData.email, formData.password);
      setPage('signIn');
      setError('');
      setFormData({ name: '', email: '', password: '', confirmPassword: '' });
      alert('Account created. Please sign in.');
    } catch (err) {
      setError(err.response?.data?.error || 'Signup failed');
    } finally {
      setLoading(false);
    }
  };

  const handleForgotPassword = async (e) => {
    e.preventDefault();
    // Placeholder - backend doesn't have this endpoint yet
    setShowResetSuccess(true);
  };

  const resetForgotPassword = () => {
    setShowResetSuccess(false);
    setResetEmail('');
  };

  return (
    <div className="min-h-screen bg-gradient">
      <div className="container">
        <div className="auth-card">
          {/* Sign In Page */}
          {page === 'signIn' && (
            <>
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
                      value={formData.email}
                      onChange={handleChange}
                      required
                    />
                    <Mail size={20} />
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
                      value={formData.password}
                      onChange={handleChange}
                      required
                    />
                    <Lock size={20} />
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
                    onClick={() => setPage('forgotPassword')}
                  >
                    Forgot password?
                  </button>
                </div>

                {error && <div className="error-message">{error}</div>}

                <button type="submit" className="btn-primary" disabled={loading}>
                  {loading ? 'Signing in...' : 'Sign In'}
                </button>
              </form>

              <p className="text-center mt-6">
                Don't have an account?{' '}
                <button className="link" onClick={() => setPage('signUp')}>
                  Sign up
                </button>
              </p>
            </>
          )}

          {/* Sign Up Page */}
          {page === 'signUp' && (
            <>
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
                      value={formData.name}
                      onChange={handleChange}
                      required
                    />
                    <User size={20} />
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
                      value={formData.email}
                      onChange={handleChange}
                      required
                    />
                    <Mail size={20} />
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
                      value={formData.password}
                      onChange={handleChange}
                      required
                    />
                    <Lock size={20} />
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
                      value={formData.confirmPassword}
                      onChange={handleChange}
                      required
                    />
                    <Lock size={20} />
                  </div>
                </div>

                <div className="checkbox-container">
                  <input type="checkbox" id="terms" required />
                  <label htmlFor="terms">
                    I agree to the <a href="#" className="link">Terms of Service</a>
                    {' '}and <a href="#" className="link">Privacy Policy</a>
                  </label>
                </div>

                {error && <div className="error-message">{error}</div>}

                <button type="submit" className="btn-primary" disabled={loading}>
                  {loading ? 'Creating...' : 'Create Account'} <ArrowRight size={20} />
                </button>
              </form>

              <p className="text-center mt-6">
                Already have an account?{' '}
                <button className="link" onClick={() => setPage('signIn')}>
                  Sign in
                </button>
              </p>
            </>
          )}

          {/* Forgot Password Page */}
          {page === 'forgotPassword' && (
            <>
              <button 
                className="back-link" 
                onClick={() => {
                  setPage('signIn');
                  setShowResetSuccess(false);
                  setResetEmail('');
                }}
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
                          type="email"
                          placeholder="Enter your email"
                          value={resetEmail}
                          onChange={(e) => setResetEmail(e.target.value)}
                          required
                        />
                        <Mail size={20} />
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
                    <span>{resetEmail}</span>
                  </p>
                  <button onClick={resetForgotPassword} className="btn-link">
                    Try another email address
                  </button>
                </div>
              )}
            </>
          )}
        </div>
      </div>
    </div>
  );
};

export default Login;
