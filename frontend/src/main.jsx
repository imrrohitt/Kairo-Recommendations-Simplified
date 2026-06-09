import React, { useEffect, useMemo, useState } from "react";
import { createRoot } from "react-dom/client";
import { RefreshCw, ShoppingCart, Sparkles, Trash2 } from "lucide-react";
import "./styles.css";

const API_URL = import.meta.env.VITE_API_URL ?? "http://localhost:8000";

async function api(path, options = {}) {
  const response = await fetch(`${API_URL}${path}`, {
    headers: { "Content-Type": "application/json" },
    ...options,
  });
  if (!response.ok) {
    const error = await response.json().catch(() => ({ detail: "Request failed" }));
    throw new Error(error.detail ?? "Request failed");
  }
  return response.json();
}

function App() {
  const [users, setUsers] = useState([]);
  const [products, setProducts] = useState([]);
  const [userId, setUserId] = useState(1);
  const [cart, setCart] = useState([]);
  const [recommendations, setRecommendations] = useState([]);
  const [selectedProductId, setSelectedProductId] = useState("");
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  const user = useMemo(() => users.find((item) => item.id === Number(userId)), [users, userId]);

  async function loadInitial() {
    setError("");
    setLoading(true);
    try {
      const [userRows, productRows] = await Promise.all([api("/users"), api("/products")]);
      setUsers(userRows);
      setProducts(productRows);
      if (!userRows.some((item) => item.id === Number(userId)) && userRows.length > 0) {
        setUserId(userRows[0].id);
      }
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  }

  async function refreshRecommendations(nextUserId = userId) {
    setError("");
    try {
      const result = await api("/recommend", {
        method: "POST",
        body: JSON.stringify({ user_id: Number(nextUserId), top_k: 10 }),
      });
      setCart(result.cart);
      setRecommendations(result.recommendations);
    } catch (err) {
      setError(err.message);
    }
  }

  async function addToCart() {
    if (!selectedProductId) return;
    setError("");
    try {
      const nextCart = await api("/cart", {
        method: "POST",
        body: JSON.stringify({
          user_id: Number(userId),
          product_id: Number(selectedProductId),
          quantity: 1,
        }),
      });
      setCart(nextCart);
      setSelectedProductId("");
      await refreshRecommendations(userId);
    } catch (err) {
      setError(err.message);
    }
  }

  async function removeFromCart(productId) {
    setError("");
    try {
      const nextCart = await api(`/cart/${userId}/${productId}`, { method: "DELETE" });
      setCart(nextCart);
      await refreshRecommendations(userId);
    } catch (err) {
      setError(err.message);
    }
  }

  useEffect(() => {
    loadInitial();
  }, []);

  useEffect(() => {
    if (users.length > 0) {
      refreshRecommendations(userId);
    }
  }, [userId, users.length]);

  const cartProductIds = new Set(cart.map((item) => item.product.id));
  const addableProducts = products.filter((product) => !cartProductIds.has(product.id));

  return (
    <main className="app">
      <section className="topbar">
        <div>
          <p className="eyebrow">Retrieval to ranking</p>
          <h1>Kairo</h1>
        </div>
        <button className="iconButton" onClick={() => refreshRecommendations(userId)} aria-label="Refresh recommendations">
          <RefreshCw size={18} />
        </button>
      </section>

      {error && <div className="error">{error}</div>}

      <section className="controls">
        <label>
          User
          <select value={userId} onChange={(event) => setUserId(Number(event.target.value))}>
            {users.map((item) => (
              <option key={item.id} value={item.id}>
                {item.name} - {item.city}
              </option>
            ))}
          </select>
        </label>
        <label>
          Add product
          <div className="inlineControl">
            <select value={selectedProductId} onChange={(event) => setSelectedProductId(event.target.value)}>
              <option value="">Choose product</option>
              {addableProducts.map((product) => (
                <option key={product.id} value={product.id}>
                  {product.name} - Rs {product.price}
                </option>
              ))}
            </select>
            <button onClick={addToCart}>Add</button>
          </div>
        </label>
      </section>

      <section className="grid">
        <div className="panel">
          <div className="panelTitle">
            <ShoppingCart size={18} />
            <h2>{user ? `${user.name}'s Cart` : "Cart"}</h2>
          </div>
          {loading ? (
            <p className="muted">Loading cart...</p>
          ) : cart.length === 0 ? (
            <p className="muted">Cart is empty. Recommendations will use popular products.</p>
          ) : (
            <div className="list">
              {cart.map((item) => (
                <article className="row" key={item.id}>
                  <div>
                    <strong>{item.product.name}</strong>
                    <span>{item.product.category} · {item.product.brand}</span>
                  </div>
                  <div className="rowActions">
                    <b>Rs {item.product.price}</b>
                    <button className="ghostButton" onClick={() => removeFromCart(item.product.id)} aria-label={`Remove ${item.product.name}`}>
                      <Trash2 size={16} />
                    </button>
                  </div>
                </article>
              ))}
            </div>
          )}
        </div>

        <div className="panel">
          <div className="panelTitle">
            <Sparkles size={18} />
            <h2>Top 10 Recommendations</h2>
          </div>
          {recommendations.length === 0 ? (
            <p className="muted">No recommendations yet.</p>
          ) : (
            <div className="list">
              {recommendations.map((item, index) => (
                <article className="row recommendation" key={item.product.id}>
                  <div className="rank">{index + 1}</div>
                  <div>
                    <strong>{item.product.name}</strong>
                    <span>{item.reason}</span>
                  </div>
                  <div className="score">
                    <b>{Math.round(item.score * 100)}%</b>
                    <small>score</small>
                  </div>
                </article>
              ))}
            </div>
          )}
        </div>
      </section>
    </main>
  );
}

createRoot(document.getElementById("root")).render(<App />);
