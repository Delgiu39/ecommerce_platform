import React, { useState } from 'react';
import { AuthProvider, useAuth } from './context/AuthContext';
import { CartProvider } from './context/CartContext';
import Navbar from './components/Navbar';
import ProductList from './components/ProductList';
import Cart from './components/Cart';
import Orders from './components/Orders';
import Login from './components/Login';
import Register from './components/Register';
import './App.css';

const AppContent = () => {
  const [currentView, setCurrentView] = useState('catalog'); // 'catalog' | 'cart' | 'orders' | 'login' | 'register'
  const [initialPaymentInfo, setInitialPaymentInfo] = useState(null);
  const { loading } = useAuth();

  const handlePayOrder = (orderId, clientSecret, amount, items) => {
    setInitialPaymentInfo({ orderId, clientSecret, amount, items });
    setCurrentView('cart');
  };

  const handleClearInitialPaymentInfo = () => {
    setInitialPaymentInfo(null);
  };

  const renderView = () => {
    if (loading) {
      return (
        <div style={{ display: 'flex', justifyContent: 'center', alignItems: 'center', minHeight: '60vh', flexDirection: 'column', gap: '16px' }}>
          <div className="animate-spin" style={{ width: '40px', height: '40px', borderRadius: '50%', border: '3px solid rgba(255,255,255,0.05)', borderTopColor: 'var(--accent-cyan)' }}></div>
          <span style={{ color: 'var(--text-secondary)', fontSize: '15px' }}>Caricamento profilo...</span>
        </div>
      );
    }

    switch (currentView) {
      case 'catalog':
        return <ProductList />;
      case 'cart':
        return (
          <Cart 
            setCurrentView={setCurrentView} 
            initialPaymentInfo={initialPaymentInfo}
            onClearInitialPaymentInfo={handleClearInitialPaymentInfo}
          />
        );
      case 'orders':
        return <Orders onPayOrder={handlePayOrder} />;
      case 'login':
        return <Login setCurrentView={setCurrentView} />;
      case 'register':
        return <Register setCurrentView={setCurrentView} />;
      default:
        return <ProductList />;
    }
  };

  return (
    <>
      <Navbar currentView={currentView} setCurrentView={setCurrentView} />
      <main style={{ minHeight: 'calc(100vh - 70px)' }}>
        {renderView()}
      </main>
      
      {/* Background glow animations */}
      <div className="ticks"></div>
      
      <footer style={{ borderTop: '1px solid var(--border-color)', padding: '24px 0', textAlign: 'center', fontSize: '13px', color: 'var(--text-muted)', background: 'rgba(8,9,14,0.9)' }}>
        <div className="container" style={{ padding: '0 20px' }}>
          <p>© 2026 Aether Store. Tutti i diritti riservati. Piattaforma di E-Commerce con Gateway di Pagamento Stripe integrato.</p>
        </div>
      </footer>
    </>
  );
};

function App() {
  return (
    <AuthProvider>
      <CartProvider>
        <AppContent />
      </CartProvider>
    </AuthProvider>
  );
}

export default App;
