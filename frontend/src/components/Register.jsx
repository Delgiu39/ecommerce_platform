import React, { useState } from 'react';
import { useAuth } from '../context/AuthContext';
import { KeyRound, Mail, User, UserPlus, Loader2 } from 'lucide-react';

const Register = ({ setCurrentView }) => {
  const { register, login } = useAuth();
  const [fullName, setFullName] = useState('');
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);
    setError('');

    if (password !== confirmPassword) {
      setError('Le password non coincidono.');
      setLoading(false);
      return;
    }

    if (password.length < 6) {
      setError('La password deve contenere almeno 6 caratteri.');
      setLoading(false);
      return;
    }

    try {
      // 1. Registra l'account
      await register(email, password, fullName);
      // 2. Effettua l'accesso automatico
      await login(email, password);
      setCurrentView('catalog');
    } catch (err) {
      setError(err.message || 'Si è verificato un errore durante la registrazione.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="container animate-fade-in" style={{ display: 'flex', justifyContent: 'center', alignItems: 'center', minHeight: '80vh' }}>
      <div className="glass-card" style={{ maxWidth: '440px', width: '100%', padding: '40px' }}>
        <div style={{ textAlign: 'center', marginBottom: '28px' }}>
          <h1 style={{ fontSize: '28px', marginBottom: '8px' }}>Crea un Account</h1>
          <p style={{ color: 'var(--text-secondary)', fontSize: '14px' }}>Inizia subito a fare acquisti sulla nostra piattaforma.</p>
        </div>

        {error && (
          <div style={{ color: 'var(--error)', background: 'rgba(239, 68, 68, 0.1)', padding: '12px', borderRadius: '8px', marginBottom: '20px', fontSize: '14px' }}>
            {error}
          </div>
        )}

        <form onSubmit={handleSubmit}>
          <div className="form-group">
            <label style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
              <User size={16} style={{ color: 'var(--text-muted)' }} />
              Nome Completo
            </label>
            <input 
              type="text" 
              className="form-control" 
              placeholder="Mario Rossi" 
              value={fullName}
              onChange={(e) => setFullName(e.target.value)}
              required 
              disabled={loading}
            />
          </div>

          <div className="form-group">
            <label style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
              <Mail size={16} style={{ color: 'var(--text-muted)' }} />
              Indirizzo Email
            </label>
            <input 
              type="email" 
              className="form-control" 
              placeholder="esempio@mail.com" 
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              required 
              disabled={loading}
            />
          </div>

          <div className="form-group">
            <label style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
              <KeyRound size={16} style={{ color: 'var(--text-muted)' }} />
              Password
            </label>
            <input 
              type="password" 
              className="form-control" 
              placeholder="Minimo 6 caratteri" 
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              required 
              disabled={loading}
            />
          </div>

          <div className="form-group" style={{ marginBottom: '28px' }}>
            <label style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
              <KeyRound size={16} style={{ color: 'var(--text-muted)' }} />
              Conferma Password
            </label>
            <input 
              type="password" 
              className="form-control" 
              placeholder="••••••••" 
              value={confirmPassword}
              onChange={(e) => setConfirmPassword(e.target.value)}
              required 
              disabled={loading}
            />
          </div>

          <button 
            type="submit" 
            className="btn-primary" 
            style={{ width: '100%', justifyContent: 'center', height: '46px', fontSize: '15px', marginBottom: '20px' }}
            disabled={loading}
          >
            {loading ? (
              <>
                <Loader2 className="animate-spin" size={18} />
                Creazione in corso...
              </>
            ) : (
              <>
                <UserPlus size={18} />
                Registrati
              </>
            )}
          </button>
        </form>

        <div style={{ textAlign: 'center', fontSize: '14px', color: 'var(--text-secondary)' }}>
          Hai già un account?{' '}
          <button 
            onClick={() => setCurrentView('login')} 
            style={{ background: 'none', border: 'none', color: 'var(--accent-cyan)', fontWeight: '600', cursor: 'pointer', padding: '0 4px' }}
          >
            Accedi
          </button>
        </div>
      </div>
    </div>
  );
};

export default Register;
