import React, { useState, useEffect } from 'react';
import { useCart } from '../context/CartContext';
import { API_URL } from '../context/AuthContext';
import { ShoppingCart, RefreshCw, Layers } from 'lucide-react';

const ProductList = () => {
  const [products, setProducts] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const { addToCart, cartItems } = useCart();

  const fetchProducts = async () => {
    setLoading(true);
    setError('');
    try {
      const response = await fetch(`${API_URL}/products/`);
      if (response.ok) {
        const data = await response.json();
        setProducts(data);
      } else {
        setError('Impossibile caricare il catalogo dei prodotti.');
      }
    } catch (err) {
      setError('Errore di rete nell\'interrogare il catalogo.');
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchProducts();
  }, []);

  const getProductImage = (name) => {
    const lower = name.toLowerCase();
    if (lower.includes('phone') || lower.includes('smartphone')) {
      return 'https://images.unsplash.com/photo-1511707171634-5f897ff02aa9?w=500&auto=format&fit=crop&q=60';
    }
    if (lower.includes('laptop') || lower.includes('computer') || lower.includes('pc')) {
      return 'https://images.unsplash.com/photo-1496181130204-755241524eab?w=500&auto=format&fit=crop&q=60';
    }
    if (lower.includes('headphone') || lower.includes('cuffie') || lower.includes('audio')) {
      return 'https://images.unsplash.com/photo-1505740420928-5e560c06d30e?w=500&auto=format&fit=crop&q=60';
    }
    if (lower.includes('watch') || lower.includes('orologio') || lower.includes('smartwatch')) {
      return 'https://images.unsplash.com/photo-1523275335684-37898b6baf30?w=500&auto=format&fit=crop&q=60';
    }
    // Default image
    return 'https://images.unsplash.com/photo-1526738549149-8e07eca6c147?w=500&auto=format&fit=crop&q=60';
  };

  const getRemainingStock = (product) => {
    const cartItem = cartItems.find((item) => item.product.id === product.id);
    const inCart = cartItem ? cartItem.quantity : 0;
    return product.stock - inCart;
  };

  return (
    <div className="container animate-fade-in">
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '32px' }}>
        <div>
          <h1 style={{ fontSize: '32px', marginBottom: '8px' }}>Catalogo Prodotti</h1>
          <p style={{ color: 'var(--text-secondary)' }}>Esplora la nostra selezione di articoli tecnologici premium.</p>
        </div>
        <button 
          onClick={fetchProducts} 
          className="btn-secondary" 
          style={{ padding: '8px 16px' }}
          disabled={loading}
        >
          <RefreshCw size={16} className={loading ? 'animate-spin' : ''} />
          Aggiorna
        </button>
      </div>

      {loading ? (
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(280px, 1fr))', gap: '30px' }}>
          {[1, 2, 3, 4].map((i) => (
            <div key={i} className="glass-card" style={{ height: '380px', animation: 'pulse 1.5s infinite ease-in-out', opacity: 0.6 }} />
          ))}
        </div>
      ) : error ? (
        <div className="glass-card" style={{ padding: '40px', textAlign: 'center', border: '1px solid var(--error)' }}>
          <p style={{ color: 'var(--error)', fontSize: '16px', marginBottom: '16px' }}>{error}</p>
          <button onClick={fetchProducts} className="btn-primary">Riprova</button>
        </div>
      ) : products.length === 0 ? (
        <div className="glass-card" style={{ padding: '60px', textAlign: 'center' }}>
          <p style={{ color: 'var(--text-secondary)', fontSize: '18px', marginBottom: '16px' }}>Nessun prodotto disponibile al momento.</p>
        </div>
      ) : (
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(280px, 1fr))', gap: '30px' }}>
          {products.map((product) => {
            const remainingStock = getRemainingStock(product);
            const isOutOfStock = remainingStock <= 0;

            return (
              <div key={product.id} className="glass-card" style={{ display: 'flex', flexDirection: 'column', height: '100%', overflow: 'hidden' }}>
                {/* Product Image */}
                <div style={{ position: 'relative', width: '100%', height: '180px', overflow: 'hidden', background: '#111' }}>
                  <img 
                    src={getProductImage(product.name)} 
                    alt={product.name} 
                    style={{ width: '100%', height: '100%', objectFit: 'cover', transition: 'transform var(--transition-normal)' }}
                    onMouseOver={(e) => e.currentTarget.style.transform = 'scale(1.05)'}
                    onMouseOut={(e) => e.currentTarget.style.transform = 'scale(1)'}
                  />
                  {isOutOfStock && (
                    <div 
                      style={{ 
                        position: 'absolute', 
                        top: '12px', 
                        right: '12px', 
                        background: 'var(--error)', 
                        color: 'white', 
                        fontSize: '11px', 
                        fontWeight: '700', 
                        padding: '4px 8px', 
                        borderRadius: '4px',
                        textTransform: 'uppercase'
                      }}
                    >
                      Esaurito
                    </div>
                  )}
                </div>

                {/* Card Content */}
                <div style={{ padding: '20px', display: 'flex', flexDirection: 'column', flexGrow: 1 }}>
                  <h3 style={{ fontSize: '18px', marginBottom: '8px', color: 'var(--text-primary)' }}>{product.name}</h3>
                  <p style={{ fontSize: '14px', color: 'var(--text-secondary)', marginBottom: '16px', flexGrow: 1 }}>
                    {product.description || 'Nessuna descrizione fornita.'}
                  </p>

                  <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginTop: 'auto' }}>
                    <div>
                      <div style={{ fontSize: '20px', fontWeight: '700', color: 'var(--accent-cyan)' }}>
                        €{parseFloat(product.price).toFixed(2)}
                      </div>
                      <div style={{ fontSize: '12px', color: isOutOfStock ? 'var(--error)' : 'var(--text-muted)' }}>
                        {isOutOfStock ? 'Non disponibile' : `Disponibili: ${remainingStock}`}
                      </div>
                    </div>

                    <button 
                      onClick={() => addToCart(product, 1)}
                      className="btn-primary"
                      style={{ padding: '8px 12px', borderRadius: '6px' }}
                      disabled={isOutOfStock}
                    >
                      <ShoppingCart size={16} />
                      Aggiungi
                    </button>
                  </div>
                </div>
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
};

export default ProductList;
