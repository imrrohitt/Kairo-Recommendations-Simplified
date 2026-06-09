import React, { useEffect, useMemo, useState } from "react";
import { createRoot } from "react-dom/client";
import {
  Activity,
  BarChart3,
  BookOpen,
  Boxes,
  Brain,
  CheckCircle2,
  Database,
  FlaskConical,
  Gauge,
  GitBranch,
  Rocket,
  Settings2,
  ShoppingCart,
  Sparkles,
  Trash2,
} from "lucide-react";
import "./styles.css";

const API_URL = import.meta.env.VITE_API_URL ?? "http://localhost:8000";

const studioIcons = {
  dataset: Database,
  features: Settings2,
  models: Brain,
  evaluation: BarChart3,
  deployment: Rocket,
  learning: BookOpen,
  monitoring: Activity,
};

const workflow = [
  "Connect Data",
  "Create Dataset",
  "Build Features",
  "Train Model",
  "Evaluate",
  "Deploy API",
];

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
  const [overview, setOverview] = useState(null);
  const [users, setUsers] = useState([]);
  const [products, setProducts] = useState([]);
  const [userId, setUserId] = useState(1);
  const [cart, setCart] = useState([]);
  const [recommendations, setRecommendations] = useState([]);
  const [selectedProductId, setSelectedProductId] = useState("");
  const [selectedStudio, setSelectedStudio] = useState("dataset");
  const [loading, setLoading] = useState(true);
  const [busyAction, setBusyAction] = useState("");
  const [error, setError] = useState("");

  const user = useMemo(() => users.find((item) => item.id === Number(userId)), [users, userId]);
  const selectedStudioInfo = overview?.studios.find((studio) => studio.id === selectedStudio);
  const cartProductIds = new Set(cart.map((item) => item.product.id));
  const addableProducts = products.filter((product) => !cartProductIds.has(product.id));

  async function loadInitial() {
    setError("");
    setLoading(true);
    try {
      const [overviewData, userRows, productRows] = await Promise.all([
        api("/platform/overview"),
        api("/users"),
        api("/products"),
      ]);
      setOverview(overviewData);
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

  async function refreshOverview() {
    const overviewData = await api("/platform/overview");
    setOverview(overviewData);
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

  async function createVersion(kind) {
    if (!overview?.project?.id) return;
    setBusyAction(kind);
    setError("");
    try {
      await api(`/platform/projects/${overview.project.id}/versions/${kind}`, { method: "POST" });
      await refreshOverview();
    } catch (err) {
      setError(err.message);
    } finally {
      setBusyAction("");
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

  return (
    <main className="appShell">
      <header className="hero">
        <div className="heroCopy">
          <img className="logo" src="/kairo-logo.svg" alt="Kairo" />
          <p className="eyebrow">Recommendation Development Platform</p>
          <h1>Build recommendation systems, not recommendation pipelines.</h1>
          <p className="heroText">
            Kairo guides non-ML engineers through datasets, features, ranking, evaluation, deployment,
            and learning in one project-based workflow.
          </p>
        </div>
        <div className="heroPanel">
          <div className="panelTitle compact">
            <GitBranch size={18} />
            <h2>{overview?.project?.name ?? "Kairo Project"}</h2>
          </div>
          <p className="muted">{overview?.project?.description ?? "Loading project state..."}</p>
          <div className="stats">
            <Stat label="Domain" value={overview?.project?.domain ?? "E-commerce"} />
            <Stat label="Datasets" value={overview?.versions.datasets.length ?? 0} />
            <Stat label="Experiments" value={overview?.versions.experiments.length ?? 0} />
          </div>
        </div>
      </header>

      {error && <div className="error">{error}</div>}

      <section className="workflow">
        {workflow.map((step, index) => (
          <div className="workflowStep" key={step}>
            <span>{index + 1}</span>
            <strong>{step}</strong>
          </div>
        ))}
      </section>

      <section className="layout">
        <aside className="sidebar">
          <p className="sectionLabel">Studios</p>
          {overview?.studios.map((studio) => {
            const Icon = studioIcons[studio.id] ?? Boxes;
            return (
              <button
                className={`navItem ${selectedStudio === studio.id ? "active" : ""}`}
                key={studio.id}
                onClick={() => setSelectedStudio(studio.id)}
              >
                <Icon size={18} />
                <span>{studio.name}</span>
              </button>
            );
          })}
        </aside>

        <section className="workspace">
          <div className="studioHeader">
            <div>
              <p className="eyebrow">{selectedStudioInfo?.status ?? "Ready"}</p>
              <h2>{selectedStudioInfo?.name ?? "Dataset Studio"}</h2>
              <p>{selectedStudioInfo?.tagline}</p>
            </div>
          </div>

          <div className="learnBox">
            <BookOpen size={20} />
            <div>
              <strong>Why this step?</strong>
              <p>{selectedStudioInfo?.why}</p>
            </div>
          </div>

          {selectedStudio === "dataset" && <DatasetStudio overview={overview} onCreate={createVersion} busy={busyAction} />}
          {selectedStudio === "features" && <FeatureStudio overview={overview} onCreate={createVersion} busy={busyAction} />}
          {selectedStudio === "models" && <ModelStudio overview={overview} onCreate={createVersion} busy={busyAction} />}
          {selectedStudio === "evaluation" && <EvaluationStudio overview={overview} />}
          {selectedStudio === "deployment" && <DeploymentStudio overview={overview} onCreate={createVersion} busy={busyAction} />}
          {selectedStudio === "learning" && <LearningCenter />}
          {selectedStudio === "monitoring" && <Monitoring />}
        </section>
      </section>

      <section className="recommendationLab">
        <div className="studioHeader">
          <div>
            <p className="eyebrow">Serving Preview</p>
            <h2>Recommendation API Lab</h2>
            <p>Test the live `POST /recommend` endpoint with a cart-aware product recommendation flow.</p>
          </div>
        </div>

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
      </section>
    </main>
  );
}

function DatasetStudio({ overview, onCreate, busy }) {
  const latest = overview?.versions.datasets[0];
  const detected = latest?.metadata?.detected_columns ?? {};
  return (
    <div className="studioGrid">
      <div className="panel">
        <div className="panelTitle">
          <Database size={18} />
          <h2>Connected Data</h2>
        </div>
        <div className="uploadGrid">
          {["users.csv", "products.csv", "interactions.csv"].map((file) => (
            <div className="uploadTile" key={file}>
              <CheckCircle2 size={18} />
              <strong>{file}</strong>
              <span>Detected from sample project</span>
            </div>
          ))}
        </div>
      </div>
      <div className="panel">
        <div className="panelTitle">
          <Gauge size={18} />
          <h2>Dataset Version</h2>
        </div>
        <VersionSummary item={latest} />
        <div className="detectedColumns">
          {Object.entries(detected).map(([label, value]) => (
            <div key={label}>
              <span>{label}</span>
              <strong>{value}</strong>
            </div>
          ))}
        </div>
        <button onClick={() => onCreate("dataset")} disabled={busy === "dataset"}>
          {busy === "dataset" ? "Creating..." : "Create Dataset Version"}
        </button>
      </div>
    </div>
  );
}

function FeatureStudio({ overview, onCreate, busy }) {
  return (
    <div className="studioGrid">
      <div className="panel wide">
        <div className="panelTitle">
          <Settings2 size={18} />
          <h2>Available Features</h2>
        </div>
        <div className="featureGrid">
          {overview?.features.map((feature) => (
            <article className="featureCard" key={feature.key}>
              <div>
                <span className="pill">{feature.group}</span>
                <h3>{feature.name}</h3>
              </div>
              <p><strong>Meaning:</strong> {feature.meaning}</p>
              <p><strong>Why it matters:</strong> {feature.why}</p>
              <label className="checkRow">
                <input type="checkbox" checked={feature.enabled} readOnly />
                {feature.key}
              </label>
            </article>
          ))}
        </div>
        <button onClick={() => onCreate("feature_set")} disabled={busy === "feature_set"}>
          {busy === "feature_set" ? "Creating..." : "Create Feature Set Version"}
        </button>
      </div>
    </div>
  );
}

function ModelStudio({ overview, onCreate, busy }) {
  const latestExperiment = overview?.versions.experiments[0];
  const strategies = [
    ["Fast Training", "Small model, quick feedback loop"],
    ["Balanced", "Good default for most projects"],
    ["Best Accuracy", "More trees and deeper search"],
  ];
  return (
    <div className="studioGrid">
      <div className="panel">
        <div className="panelTitle">
          <Brain size={18} />
          <h2>Training Strategy</h2>
        </div>
        <div className="strategyList">
          {strategies.map(([name, description]) => (
            <label className="strategy" key={name}>
              <input type="radio" checked={name === "Balanced"} readOnly />
              <span>
                <strong>{name}</strong>
                <small>{description}</small>
              </span>
            </label>
          ))}
        </div>
        <button onClick={() => onCreate("experiment")} disabled={busy === "experiment"}>
          {busy === "experiment" ? "Queueing..." : "Run Experiment"}
        </button>
      </div>
      <div className="panel">
        <div className="panelTitle">
          <FlaskConical size={18} />
          <h2>Latest Experiment</h2>
        </div>
        <VersionSummary item={latestExperiment} />
        <pre className="codeBlock">{JSON.stringify(latestExperiment?.config ?? { algorithm: "XGBoost" }, null, 2)}</pre>
        <button onClick={() => onCreate("model")} disabled={busy === "model"}>
          {busy === "model" ? "Registering..." : "Register Model Version"}
        </button>
      </div>
    </div>
  );
}

function EvaluationStudio({ overview }) {
  return (
    <div className="metricGrid">
      {overview?.metrics.map((metric) => (
        <article className="metricCard" key={metric.name}>
          <span>{metric.name}</span>
          <strong>{metric.value.toFixed(2)}</strong>
          <p>{metric.explanation}</p>
        </article>
      ))}
    </div>
  );
}

function DeploymentStudio({ overview, onCreate, busy }) {
  const latest = overview?.versions.deployments[0];
  return (
    <div className="studioGrid">
      <div className="panel">
        <div className="panelTitle">
          <Rocket size={18} />
          <h2>Deployment</h2>
        </div>
        <VersionSummary item={latest} />
        <button onClick={() => onCreate("deployment")} disabled={busy === "deployment"}>
          {busy === "deployment" ? "Creating..." : "Create Deployment Version"}
        </button>
      </div>
      <div className="panel">
        <div className="panelTitle">
          <Boxes size={18} />
          <h2>Generated API</h2>
        </div>
        <pre className="codeBlock">{JSON.stringify(overview?.serving_example, null, 2)}</pre>
      </div>
    </div>
  );
}

function LearningCenter() {
  const lessons = [
    ["Why negative samples?", "Recommendation systems mostly know what users clicked or bought. Negative samples teach the model what users ignored."],
    ["Why candidate generation?", "Ranking every item is slow and noisy. Candidate generation narrows the search to likely items first."],
    ["Why ranking metrics?", "Recommendations care about ordering. NDCG and Precision@K evaluate the top of the list where users actually look."],
  ];
  return (
    <div className="lessonList">
      {lessons.map(([title, body]) => (
        <article className="lesson" key={title}>
          <BookOpen size={18} />
          <div>
            <strong>{title}</strong>
            <p>{body}</p>
          </div>
        </article>
      ))}
    </div>
  );
}

function Monitoring() {
  return (
    <div className="metricGrid">
      <Metric label="API latency" value="42ms" note="Serving health" />
      <Metric label="Feature freshness" value="Live" note="Redis optional" />
      <Metric label="Model status" value="Ready" note="XGBoost or fallback" />
      <Metric label="Drift checks" value="Planned" note="Roadmap item" />
    </div>
  );
}

function VersionSummary({ item }) {
  if (!item) return <p className="muted">No version created yet.</p>;
  return (
    <div className="versionSummary">
      <strong>{item.name}</strong>
      <span>Version {item.version}</span>
      <span className="pill">{item.status}</span>
    </div>
  );
}

function Stat({ label, value }) {
  return (
    <div className="stat">
      <span>{label}</span>
      <strong>{value}</strong>
    </div>
  );
}

function Metric({ label, value, note }) {
  return (
    <article className="metricCard">
      <span>{label}</span>
      <strong>{value}</strong>
      <p>{note}</p>
    </article>
  );
}

createRoot(document.getElementById("root")).render(<App />);
