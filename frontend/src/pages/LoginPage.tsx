import { useState, FormEvent } from 'react';
import axios from 'axios';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../contexts/AuthContext';
import { Sparkles } from 'lucide-react';

export default function LoginPage() {
  const { login } = useAuth();
  const navigate = useNavigate();

  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);

  const handleSubmit = async (e: FormEvent) => {
    e.preventDefault();
    setError('');
    setLoading(true);
    try {
      await login(username, password);
      navigate('/', { replace: true });
    } catch (err: unknown) {
      if (axios.isAxiosError(err)) {
        if (err.response?.status === 401 || err.response?.status === 400) {
          setError('Invalid username or password.');
        } else if (err.response) {
          setError(`Server error ${err.response.status}: ${JSON.stringify(err.response.data)}`);
        } else {
          setError(`Network error — could not reach the server. (${err.message})`);
        }
      } else {
        setError('Unexpected error. Check the browser console.');
      }
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-[#f5f7f4] flex items-center justify-center px-4">
      <div className="w-full max-w-sm">
        {/* Logo */}
        <div className="flex items-center gap-2 justify-center mb-8 text-[#1f2a1d]">
          <Sparkles className="w-5 h-5 text-[#336443]" />
          <span
            className="text-2xl font-semibold tracking-tight"
            style={{ fontFamily: '"Neue Haas Grotesk Display Pro 55 Roman", "Helvetica Neue", sans-serif' }}
          >
            OriginESG
          </span>
        </div>

        <div className="bg-white rounded-2xl shadow-sm border border-[#e8ede6] px-8 py-10">
          <h1
            className="text-xl font-semibold text-[#1f2a1d] mb-1"
            style={{ fontFamily: '"Neue Haas Grotesk Display Pro 55 Roman", "Helvetica Neue", sans-serif' }}
          >
            Sign in
          </h1>
          <p className="text-sm text-[#4b5b47] mb-8">
            Access your emissions dashboard
          </p>

          <form onSubmit={handleSubmit} className="flex flex-col gap-5">
            <div className="flex flex-col gap-1.5">
              <label className="text-xs font-medium text-[#4b5b47]">Username</label>
              <input
                type="text"
                value={username}
                onChange={(e) => setUsername(e.target.value)}
                required
                autoFocus
                className="w-full border border-[#dde5db] rounded-lg px-3.5 py-2.5 text-sm text-[#1f2a1d] placeholder:text-[#9bab97] focus:outline-none focus:ring-2 focus:ring-[#336443]/30 focus:border-[#336443] transition-colors"
                placeholder="your username"
              />
            </div>

            <div className="flex flex-col gap-1.5">
              <label className="text-xs font-medium text-[#4b5b47]">Password</label>
              <input
                type="password"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                required
                className="w-full border border-[#dde5db] rounded-lg px-3.5 py-2.5 text-sm text-[#1f2a1d] placeholder:text-[#9bab97] focus:outline-none focus:ring-2 focus:ring-[#336443]/30 focus:border-[#336443] transition-colors"
                placeholder="••••••••"
              />
            </div>

            {error && (
              <p className="text-xs text-red-600 bg-red-50 border border-red-100 rounded-lg px-3 py-2">
                {error}
              </p>
            )}

            <button
              type="submit"
              disabled={loading}
              className="w-full bg-[#1f2a1d] hover:bg-[#2a3827] disabled:opacity-60 text-white text-sm font-semibold py-2.5 rounded-full transition-colors mt-1"
            >
              {loading ? 'Signing in…' : 'Sign in'}
            </button>
          </form>
        </div>

        <p className="text-center text-xs text-[#7a8f76] mt-6">
          OriginESG · Emissions tracking &amp; audit
        </p>
      </div>
    </div>
  );
}
