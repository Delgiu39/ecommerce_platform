import React, { useState, useEffect } from 'react';
import { useAuth, API_URL } from '../context/AuthContext';
import { Receipt, Calendar, CreditCard, ChevronRight, Package, RefreshCw, AlertCircle, CheckCircle, Clock, XCircle } from 'lucide-react';

const Orders = ({ onPayOrder }) => {
  const { token } = useAuth();
  const [orders, setOrders] = useState([]);
  const [productsMap, setProductsMap] = useState({});
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  const fetchOrdersAndProducts = async () => {
    setLoading(true);
    setError('');
    try {
      // 1. Recupera gli ordini
      const ordersResponse = await fetch(`${API_URL}/orders/`, {
        headers: {
          'Authorization': `Bearer ${token}`,
        },
      });

      if (!ordersResponse.ok) {
        throw new Error('Impossibile caricare lo storico degli ordini.');
      }

      const ordersData = await ordersResponse.json();

      // Ordina per data decrescente (i più recenti prima)
      ordersData.sort((a, b) => new Date(b.created_at) - new Date(a.created_at));

      // 2. Recupera tutti i prodotti per mappare gli ID ai nomi
      const productsResponse = await fetch(`${API_URL}/products/`);
      let productsData = [];
      if (productsResponse.ok) {
        productsData = await productsResponse.json();
      }

      const pMap = {};
      productsData.forEach((p) => {
        pMap[p.id] = p;
      });

      setProductsMap(pMap);
      setOrders(ordersData);
    } catch (err) {
      setError(err.message || 'Errore durante il recupero dei dati.');
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchOrdersAndProducts();
  }, [token]);

  const formatDate = (dateString) => {
    return new Date(dateString).toLocaleDateString('it-IT', {
      year: 'numeric',
      month: 'long',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit',
    });
  };

  const getStatusBadge = (status) => {
    switch (status) {
      case 'paid':
        return (
          <span style={{ display: 'inline-flex', alignItems: 'center', gap: '6px', background: 'rgba(16, 185, 129, 0.12)', color: 'var(--success)', border: '1px solid rgba(16, 185, 129, 0.25)', padding: '4px 10px', borderRadius: '20px', fontSize: '13px', fontWeight: '500' }}>
            <CheckCircle size={14} />
            Pagato
          </span>
        );
      case 'pending':
        return (
          <span style={{ display: 'inline-flex', alignItems: 'center', gap: '6px', background: 'rgba(245, 158, 11, 0.12)', color: 'var(--warning)', border: '1px solid rgba(245, 158, 11, 0.25)', padding: '4px 10px', borderRadius: '20px', fontSize: '13px', fontWeight: '500' }}>
            <Clock size={14} />
            In Attesa
          </span>
        );
      case 'failed':
        return (
          <span style={{ display: 'inline-flex', alignItems: 'center', gap: '6px', background: 'rgba(239, 68, 68, 0.12)', color: 'var(--error)', border: '1px solid rgba(239, 68, 68, 0.25)', padding: '4px 10px', borderRadius: '20px', fontSize: '13px', fontWeight: '500' }}>
            <XCircle size={14} />
            Fallito
          </span>
        );
      default:
        return (
          <span style={{ display: 'inline-flex', alignItems: 'center', gap: '6px', background: 'rgba(255,255,255,0.05)', color: 'var(--text-secondary)', border: '1px solid var(--border-color)', padding: '4px 10px', borderRadius: '20px', fontSize: '13px', fontWeight: '500' }}>
            {status}
          </span>
        );
    }
  };

  const handlePayNow = async (order) => {
    try {
      // Chiama l'endpoint per ottenere il client secret
      const response = await fetch(`${API_URL}/payments/create-intent/${order.id}`, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${token}`,
        },
      });

      const data = await response.json();
      if (!response.ok) {
        throw new Error(data.detail || 'Impossibile completare il pagamento per questo ordine.');
      }

      // Invoca il callback fornito dal genitore per andare alla schermata di pagamento
      onPayOrder(order.id, data.client_secret, parseFloat(order.total_amount));
    } catch (err) {
      alert(err.message);
    }
  };

  return (
    <div className="container animate-fade-in">
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '32px' }}>
        <div>
          <h1 style={{ fontSize: '32px', marginBottom: '8px' }}>I Miei Ordini</h1>
          <p style={{ color: 'var(--text-secondary)' }}>Visualizza lo storico e traccia lo stato dei tuoi acquisti.</p>
        </div>
        <button 
          onClick={fetchOrdersAndProducts} 
          className="btn-secondary" 
          style={{ padding: '8px 16px' }}
          disabled={loading}
        >
          <RefreshCw size={16} className={loading ? 'animate-spin' : ''} />
          Aggiorna
        </button>
      </div>

      {loading ? (
        <div style={{ display: 'flex', flexDirection: 'column', gap: '20px' }}>
          {[1, 2].map((i) => (
            <div key={i} className="glass-card" style={{ height: '220px', animation: 'pulse 1.5s infinite ease-in-out', opacity: 0.6 }} />
          ))}
        </div>
      ) : error ? (
        <div className="glass-card" style={{ padding: '40px', textAlign: 'center', border: '1px solid var(--error)' }}>
          <AlertCircle size={40} style={{ color: 'var(--error)', margin: '0 auto 16px auto' }} />
          <p style={{ color: 'var(--error)', fontSize: '16px', marginBottom: '16px' }}>{error}</p>
          <button onClick={fetchOrdersAndProducts} className="btn-primary">Riprova</button>
        </div>
      ) : orders.length === 0 ? (
        <div className="glass-card" style={{ padding: '60px', textAlign: 'center' }}>
          <Receipt size={48} style={{ color: 'var(--text-muted)', marginBottom: '16px', margin: '0 auto 16px auto' }} />
          <p style={{ color: 'var(--text-secondary)', fontSize: '18px', marginBottom: '24px' }}>
            Non hai ancora effettuato nessun ordine.
          </p>
        </div>
      ) : (
        <div style={{ display: 'flex', flexDirection: 'column', gap: '24px' }}>
          {orders.map((order) => (
            <div key={order.id} className="glass-card" style={{ padding: '24px', display: 'flex', flexDirection: 'column', gap: '20px' }}>
              {/* Intestazione Ordine */}
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: '16px', borderBottom: '1px solid var(--border-color)', paddingBottom: '16px' }}>
                <div style={{ display: 'flex', alignItems: 'center', gap: '16px', flexWrap: 'wrap' }}>
                  <div>
                    <span style={{ fontSize: '12px', color: 'var(--text-muted)', display: 'block', textTransform: 'uppercase', fontWeight: '600' }}>ID ORDINE</span>
                    <span style={{ fontSize: '14px', fontFamily: 'monospace', color: 'var(--text-primary)' }}>{order.id}</span>
                  </div>
                  <div style={{ display: 'flex', alignItems: 'center', gap: '6px', color: 'var(--text-secondary)', fontSize: '14px' }}>
                    <Calendar size={16} style={{ color: 'var(--text-muted)' }} />
                    {formatDate(order.created_at)}
                  </div>
                </div>
                <div>
                  {getStatusBadge(order.status)}
                </div>
              </div>

              {/* Elementi Ordine */}
              <div style={{ display: 'flex', flexDirection: 'column', gap: '12px' }}>
                {order.items.map((item) => {
                  const product = productsMap[item.product_id];
                  return (
                    <div key={item.id} style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', fontSize: '15px' }}>
                      <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
                        <Package size={16} style={{ color: 'var(--text-muted)' }} />
                        <div>
                          <span style={{ color: 'var(--text-primary)', fontWeight: '500' }}>
                            {product ? product.name : 'Articolo non più disponibile'}
                          </span>
                          <span style={{ color: 'var(--text-muted)', fontSize: '13px', marginLeft: '8px' }}>
                            x {item.quantity}
                          </span>
                        </div>
                      </div>
                      <div style={{ color: 'var(--text-secondary)' }}>
                        €{(parseFloat(item.price_at_purchase) * item.quantity).toFixed(2)}
                      </div>
                    </div>
                  );
                })}
              </div>

              {/* Piè di pagina Ordine */}
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', borderTop: '1px solid var(--border-color)', paddingTop: '16px', marginTop: '4px' }}>
                <div>
                  <span style={{ fontSize: '14px', color: 'var(--text-secondary)' }}>Totale ordine: </span>
                  <span style={{ fontSize: '20px', fontWeight: '700', color: 'var(--accent-cyan)' }}>
                    €{parseFloat(order.total_amount).toFixed(2)}
                  </span>
                </div>

                {order.status === 'pending' && (
                  <button 
                    onClick={() => handlePayNow(order)}
                    className="btn-primary"
                    style={{ padding: '8px 16px', fontSize: '14px', gap: '6px' }}
                  >
                    <CreditCard size={16} />
                    Completa Pagamento
                  </button>
                )}
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
};

export default Orders;
