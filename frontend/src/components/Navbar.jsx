import React from 'react';
import { useAuth } from '../context/AuthContext';
import { useCart } from '../context/CartContext';
import { ShoppingCart, LogOut, Receipt, Compass, User } from 'lucide-react';

const Navbar = ({ currentView, setCurrentView }) => {
  const { user, logout } = useAuth();
  const { cartCount } = useCart();

  const handleNavClick = (view) => {
    setCurrentView(view);
  };

  return (
    <nav className="glass-nav">
      <div className="container" style={{ padding: '0 20px', height: '100%', display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
        {/* Logo */}
        <div 
          onClick={() => handleNavClick('catalog')} 
          style={{ 
            fontSize: '22px', 
            fontWeight: '700', 
            background: 'var(--accent-gradient)', 
            WebkitBackgroundClip: 'text', 
            WebkitTextFillColor: 'transparent',
            cursor: 'pointer',
            letterSpacing: '-0.03em'
          }}
        >
          AETHER STORE
        </div>

        {/* Links */}
        <div style={{ display: 'flex', alignItems: 'center', gap: '24px' }}>
          <button 
            onClick={() => handleNavClick('catalog')}
            style={{
              background: 'none',
              border: 'none',
              color: currentView === 'catalog' ? 'var(--accent-cyan)' : 'var(--text-primary)',
              display: 'flex',
              alignItems: 'center',
              gap: '6px',
              cursor: 'pointer',
              fontSize: '15px',
              fontWeight: '500',
              fontFamily: 'var(--font-main)'
            }}
          >
            <Compass size={18} />
            Catalogo
          </button>

          {user && (
            <button 
              onClick={() => handleNavClick('orders')}
              style={{
                background: 'none',
                border: 'none',
                color: currentView === 'orders' ? 'var(--accent-cyan)' : 'var(--text-primary)',
                display: 'flex',
                alignItems: 'center',
                gap: '6px',
                cursor: 'pointer',
                fontSize: '15px',
                fontFamily: 'var(--font-main)',
                fontWeight: '500'
              }}
            >
              <Receipt size={18} />
              I Miei Ordini
            </button>
          )}

          {/* Cart Icon */}
          <button 
            onClick={() => handleNavClick('cart')}
            style={{
              background: 'none',
              border: 'none',
              color: currentView === 'cart' ? 'var(--accent-cyan)' : 'var(--text-primary)',
              display: 'flex',
              alignItems: 'center',
              gap: '6px',
              cursor: 'pointer',
              fontSize: '15px',
              fontFamily: 'var(--font-main)',
              fontWeight: '500',
              position: 'relative'
            }}
          >
            <ShoppingCart size={18} />
            Carrello
            {cartCount > 0 && (
              <span 
                style={{
                  position: 'absolute',
                  top: '-8px',
                  right: '-12px',
                  background: 'var(--accent-gradient)',
                  color: '#08090e',
                  fontSize: '11px',
                  fontWeight: '700',
                  borderRadius: '50%',
                  width: '18px',
                  height: '18px',
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                  boxShadow: '0 0 10px rgba(0, 242, 254, 0.3)'
                }}
              >
                {cartCount}
              </span>
            )}
          </button>

          {/* Auth section */}
          <div style={{ display: 'flex', alignItems: 'center', gap: '16px', marginLeft: '12px', borderLeft: '1px solid var(--border-color)', paddingLeft: '24px' }}>
            {user ? (
              <>
                <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                  <div 
                    style={{ 
                      width: '32px', 
                      height: '32px', 
                      borderRadius: '50%', 
                      background: 'rgba(255, 255, 255, 0.05)', 
                      border: '1px solid var(--border-color)',
                      display: 'flex', 
                      alignItems: 'center', 
                      justifyContent: 'center',
                      color: 'var(--accent-cyan)'
                    }}
                  >
                    <User size={16} />
                  </div>
                  <div style={{ display: 'flex', flexDirection: 'column' }}>
                    <span style={{ fontSize: '13px', fontWeight: '500', color: 'var(--text-primary)' }}>{user.full_name}</span>
                    {user.is_superuser && (
                      <span style={{ fontSize: '10px', color: 'var(--accent-cyan)', fontWeight: '600', textTransform: 'uppercase' }}>Admin</span>
                    )}
                  </div>
                </div>
                <button 
                  onClick={logout}
                  style={{
                    background: 'none',
                    border: 'none',
                    color: 'var(--text-muted)',
                    cursor: 'pointer',
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'center'
                  }}
                  title="Logout"
                >
                  <LogOut size={18} />
                </button>
              </>
            ) : (
              <button 
                onClick={() => handleNavClick('login')}
                className="btn-primary"
                style={{ padding: '8px 16px', fontSize: '14px' }}
              >
                Accedi
              </button>
            )}
          </div>
        </div>
      </div>
    </nav>
  );
};

export default Navbar;
