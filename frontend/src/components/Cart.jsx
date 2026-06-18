import React, { useState, useEffect } from 'react';
import { useCart } from '../context/CartContext';
import { useAuth, API_URL } from '../context/AuthContext';
import { loadStripe } from '@stripe/stripe-js';
import { Elements } from '@stripe/react-stripe-js';
import CheckoutForm from './CheckoutForm';
import { Trash2, Plus, Minus, ShoppingBag, CreditCard, ChevronLeft, CheckCircle, XCircle } from 'lucide-react';

// Inizializza Stripe con una chiave fittizia per consentire il caricamento del componente in modalità mock.
// Se l'utente configura una chiave Stripe reale, questa chiave fittizia verrà ignorata o sovrascritta.
const stripePromise = loadStripe('pk_test_51MockKey00000000000000000000000000000000000000000000000000000000000000000000');

const Cart = ({ setCurrentView, initialPaymentInfo, onClearInitialPaymentInfo }) => {
  const { cartItems, updateQuantity, removeFromCart, clearCart, cartTotal } = useCart();
  const { token, user } = useAuth();

  const [checkoutStep, setCheckoutStep] = useState('cart'); // 'cart' | 'payment' | 'success' | 'failure'
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [orderId, setOrderId] = useState(null);
  const [clientSecret, setClientSecret] = useState(null);
  
  const [paymentAmount, setPaymentAmount] = useState(0);
  const [paymentItems, setPaymentItems] = useState([]);
  const [productsMap, setProductsMap] = useState({});

  // Recupera i prodotti all'avvio per mappare i nomi degli articoli
  useEffect(() => {
    const fetchProducts = async () => {
      try {
        const res = await fetch(`${API_URL}/products/`);
        if (res.ok) {
          const data = await res.json();
          const pMap = {};
          data.forEach(p => { pMap[p.id] = p; });
          setProductsMap(pMap);
        }
      } catch (err) {
        console.error('Errore nel recupero prodotti per carrello:', err);
      }
    };
    fetchProducts();
  }, []);

  // Gestione del re-indirizzamento da "I Miei Ordini" per completare un pagamento in sospeso
  useEffect(() => {
    if (initialPaymentInfo) {
      setOrderId(initialPaymentInfo.orderId);
      setClientSecret(initialPaymentInfo.clientSecret);
      setPaymentAmount(initialPaymentInfo.amount);
      setPaymentItems(initialPaymentInfo.items || []);
      setCheckoutStep('payment');
      
      if (onClearInitialPaymentInfo) {
        onClearInitialPaymentInfo();
      }
    }
  }, [initialPaymentInfo, onClearInitialPaymentInfo]);

  const handleStartCheckout = async () => {
    if (!user) {
      setCurrentView('login');
      return;
    }

    setLoading(true);
    setError('');

    try {
      // 1. Crea l'ordine sul backend
      const orderItems = cartItems.map((item) => ({
        product_id: item.product.id,
        quantity: item.quantity,
      }));

      const orderResponse = await fetch(`${API_URL}/orders/`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`,
        },
        body: JSON.stringify({ items: orderItems }),
      });

      const orderData = await orderResponse.json();

      if (!orderResponse.ok) {
        throw new Error(orderData.detail || 'Impossibile creare l\'ordine.');
      }

      setOrderId(orderData.id);

      // 2. Crea il Payment Intent per l'ordine
      const intentResponse = await fetch(`${API_URL}/payments/create-intent/${orderData.id}`, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${token}`,
        },
      });

      const intentData = await intentResponse.json();

      if (!intentResponse.ok) {
        throw new Error(intentData.detail || 'Impossibile creare l\'intento di pagamento.');
      }

      setClientSecret(intentData.client_secret);
      setPaymentAmount(cartTotal);
      setPaymentItems(cartItems.map(item => ({
        id: item.product.id,
        product_id: item.product.id,
        quantity: item.quantity,
        price_at_purchase: item.product.price
      })));
      setCheckoutStep('payment');
    } catch (err) {
      setError(err.message || 'Si è verificato un errore durante la preparazione del checkout.');
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  const handlePaymentSuccess = () => {
    clearCart();
    setCheckoutStep('success');
  };

  const handlePaymentFailure = () => {
    setCheckoutStep('failure');
  };

  if (checkoutStep === 'success') {
    return (
      <div className="container animate-fade-in" style={{ display: 'flex', justifyContent: 'center', alignItems: 'center', minHeight: '60vh' }}>
        <div className="glass-card" style={{ maxWidth: '500px', width: '100%', padding: '40px', textAlign: 'center' }}>
          <CheckCircle size={64} style={{ color: 'var(--success)', marginBottom: '24px', margin: '0 auto 24px auto' }} />
          <h2 style={{ fontSize: '28px', marginBottom: '12px' }}>Pagamento Completato!</h2>
          <p style={{ color: 'var(--text-secondary)', marginBottom: '32px', fontSize: '15px' }}>
            Il tuo pagamento è stato elaborato con successo. Riceverai presto una mail di conferma con i dettagli della spedizione.
          </p>
          <div style={{ display: 'flex', flexDirection: 'column', gap: '12px' }}>
            <button onClick={() => setCurrentView('orders')} className="btn-primary" style={{ justifyContent: 'center' }}>
              Visualizza I Miei Ordini
            </button>
            <button onClick={() => setCurrentView('catalog')} className="btn-secondary" style={{ justifyContent: 'center' }}>
              Continua lo Shopping
            </button>
          </div>
        </div>
      </div>
    );
  }

  if (checkoutStep === 'failure') {
    return (
      <div className="container animate-fade-in" style={{ display: 'flex', justifyContent: 'center', alignItems: 'center', minHeight: '60vh' }}>
        <div className="glass-card" style={{ maxWidth: '500px', width: '100%', padding: '40px', textAlign: 'center', border: '1px solid var(--error)' }}>
          <XCircle size={64} style={{ color: 'var(--error)', marginBottom: '24px', margin: '0 auto 24px auto' }} />
          <h2 style={{ fontSize: '28px', marginBottom: '12px' }}>Pagamento Fallito</h2>
          <p style={{ color: 'var(--text-secondary)', marginBottom: '32px', fontSize: '15px' }}>
            Si è verificato un problema durante l'elaborazione del pagamento. Verifica i dati della carta o riprova più tardi.
          </p>
          <div style={{ display: 'flex', flexDirection: 'column', gap: '12px' }}>
            <button onClick={() => setCheckoutStep('payment')} className="btn-primary" style={{ justifyContent: 'center' }}>
              Riprova il Pagamento
            </button>
            <button onClick={() => setCheckoutStep('cart')} className="btn-secondary" style={{ justifyContent: 'center' }}>
              Torna al Carrello
            </button>
          </div>
        </div>
      </div>
    );
  }

  if (checkoutStep === 'payment') {
    return (
      <div className="container animate-fade-in">
        <button 
          onClick={() => setCheckoutStep('cart')} 
          className="btn-secondary" 
          style={{ marginBottom: '24px', padding: '8px 16px', fontSize: '14px', gap: '4px' }}
        >
          <ChevronLeft size={16} />
          Indietro
        </button>

        <div style={{ display: 'grid', gridTemplateColumns: '1fr 450px', gap: '40px', alignItems: 'start' }}>
          {/* Dettagli Ordine */}
          <div className="glass-card" style={{ padding: '30px' }}>
            <h2 style={{ fontSize: '22px', marginBottom: '20px', display: 'flex', alignItems: 'center', gap: '8px' }}>
              Riepilogo Ordine
            </h2>
            <div style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}>
              {paymentItems.map((item) => {
                const product = productsMap[item.product_id] || cartItems.find(c => c.product.id === item.product_id)?.product;
                return (
                  <div key={item.id || item.product_id} style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', borderBottom: '1px solid var(--border-color)', paddingBottom: '16px' }}>
                    <div>
                      <h4 style={{ fontSize: '15px', color: 'var(--text-primary)' }}>
                        {product ? product.name : 'Articolo'}
                      </h4>
                      <span style={{ fontSize: '13px', color: 'var(--text-secondary)' }}>
                        Qta: {item.quantity} x €{parseFloat(item.price_at_purchase || product?.price || 0).toFixed(2)}
                      </span>
                    </div>
                    <div style={{ fontWeight: '600', color: 'var(--text-primary)' }}>
                      €{(parseFloat(item.price_at_purchase || product?.price || 0) * item.quantity).toFixed(2)}
                    </div>
                  </div>
                );
              })}
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', paddingTop: '10px', fontSize: '18px', fontWeight: '700' }}>
                <span>Totale da Pagare</span>
                <span style={{ color: 'var(--accent-cyan)' }}>€{paymentAmount.toFixed(2)}</span>
              </div>
            </div>
          </div>

          {/* Form Stripe */}
          <div className="glass-card" style={{ padding: '30px' }}>
            <h2 style={{ fontSize: '22px', marginBottom: '20px', display: 'flex', alignItems: 'center', gap: '8px' }}>
              <CreditCard size={20} style={{ color: 'var(--accent-cyan)' }} />
              Dettagli di Pagamento
            </h2>
            {clientSecret && (
              <Elements stripe={stripePromise} options={{ clientSecret }}>
                <CheckoutForm 
                  orderId={orderId} 
                  clientSecret={clientSecret} 
                  amount={paymentAmount} 
                  onPaymentSuccess={handlePaymentSuccess} 
                  onPaymentFailure={handlePaymentFailure} 
                />
              </Elements>
            )}
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="container animate-fade-in">
      <h1 style={{ fontSize: '32px', marginBottom: '8px' }}>Carrello</h1>
      <p style={{ color: 'var(--text-secondary)', marginBottom: '32px' }}>Gestisci gli articoli prima di procedere al pagamento sicuro.</p>

      {error && (
        <div style={{ color: 'var(--error)', background: 'rgba(239, 68, 68, 0.1)', padding: '16px', borderRadius: '8px', marginBottom: '24px' }}>
          {error}
        </div>
      )}

      {cartItems.length === 0 ? (
        <div className="glass-card" style={{ padding: '60px', textAlign: 'center' }}>
          <ShoppingBag size={48} style={{ color: 'var(--text-muted)', marginBottom: '16px', margin: '0 auto 16px auto' }} />
          <p style={{ color: 'var(--text-secondary)', fontSize: '18px', marginBottom: '24px' }}>
            Il tuo carrello è vuoto.
          </p>
          <button onClick={() => setCurrentView('catalog')} className="btn-primary">
            Esplora il Catalogo
          </button>
        </div>
      ) : (
        <div style={{ display: 'grid', gridTemplateColumns: '1fr 380px', gap: '30px', alignItems: 'start' }}>
          {/* Tabella Elementi Carrello */}
          <div style={{ display: 'flex', flexDirection: 'column', gap: '20px' }}>
            {cartItems.map((item) => (
              <div key={item.product.id} className="glass-card" style={{ padding: '20px', display: 'flex', gap: '20px', alignItems: 'center' }}>
                {/* Dettagli Prodotto */}
                <div style={{ flexGrow: 1 }}>
                  <h3 style={{ fontSize: '18px', marginBottom: '4px' }}>{item.product.name}</h3>
                  <p style={{ fontSize: '13px', color: 'var(--text-secondary)', marginBottom: '8px' }}>
                    {item.product.description || 'Nessuna descrizione.'}
                  </p>
                  <div style={{ fontSize: '16px', fontWeight: '600', color: 'var(--accent-cyan)' }}>
                    €{parseFloat(item.product.price).toFixed(2)}
                  </div>
                </div>

                {/* Modifica Quantità */}
                <div style={{ display: 'flex', alignItems: 'center', gap: '12px', background: 'rgba(0,0,0,0.2)', padding: '6px 12px', borderRadius: '6px', border: '1px solid var(--border-color)' }}>
                  <button 
                    onClick={() => updateQuantity(item.product.id, item.quantity - 1, item.product.stock)} 
                    style={{ background: 'none', border: 'none', color: 'var(--text-primary)', cursor: 'pointer', display: 'flex' }}
                  >
                    <Minus size={16} />
                  </button>
                  <span style={{ fontSize: '15px', fontWeight: '600', width: '20px', textAlign: 'center' }}>{item.quantity}</span>
                  <button 
                    onClick={() => updateQuantity(item.product.id, item.quantity + 1, item.product.stock)} 
                    style={{ background: 'none', border: 'none', color: 'var(--text-primary)', cursor: 'pointer', display: 'flex' }}
                  >
                    <Plus size={16} />
                  </button>
                </div>

                {/* Subtotale */}
                <div style={{ width: '100px', textAlign: 'right', fontWeight: '600', fontSize: '16px' }}>
                  €{(parseFloat(item.product.price) * item.quantity).toFixed(2)}
                </div>

                {/* Rimuovi */}
                <button 
                  onClick={() => removeFromCart(item.product.id)}
                  style={{ background: 'none', border: 'none', color: 'var(--error)', cursor: 'pointer', padding: '8px' }}
                  title="Rimuovi prodotto"
                >
                  <Trash2 size={18} />
                </button>
              </div>
            ))}

            {/* Svuota Carrello */}
            <div style={{ display: 'flex', justifyContent: 'flex-start' }}>
              <button onClick={clearCart} className="btn-secondary" style={{ padding: '8px 16px', fontSize: '13px', color: 'var(--error)', borderColor: 'rgba(239, 68, 68, 0.2)' }}>
                Svuota Carrello
              </button>
            </div>
          </div>

          {/* Riepilogo di Checkout */}
          <div className="glass-card" style={{ padding: '30px', position: 'sticky', top: '100px' }}>
            <h3 style={{ fontSize: '20px', marginBottom: '20px', borderBottom: '1px solid var(--border-color)', paddingBottom: '12px' }}>
              Riepilogo dell'ordine
            </h3>
            
            <div style={{ display: 'flex', flexDirection: 'column', gap: '12px', marginBottom: '24px' }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', color: 'var(--text-secondary)' }}>
                <span>Articoli nel carrello:</span>
                <span>{cartItems.reduce((acc, item) => acc + item.quantity, 0)}</span>
              </div>
              <div style={{ display: 'flex', justifyContent: 'space-between', color: 'var(--text-secondary)' }}>
                <span>Spedizione:</span>
                <span style={{ color: 'var(--success)' }}>Gratuita</span>
              </div>
              <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '18px', fontWeight: '700', borderTop: '1px solid var(--border-color)', paddingTop: '16px', marginTop: '4px' }}>
                <span>Totale:</span>
                <span style={{ color: 'var(--accent-cyan)' }}>€{cartTotal.toFixed(2)}</span>
              </div>
            </div>

            <button 
              onClick={handleStartCheckout} 
              className="btn-primary" 
              style={{ width: '100%', justifyContent: 'center', height: '48px', fontSize: '15px' }}
              disabled={loading}
            >
              {loading ? 'Elaborazione...' : (user ? 'Procedi al Pagamento' : 'Accedi per Pagare')}
            </button>
          </div>
        </div>
      )}
    </div>
  );
};

export default Cart;
