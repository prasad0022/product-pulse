import React, { useEffect, useMemo, useState } from "react";
import { createRoot } from "react-dom/client";
import {
  ResponsiveContainer, LineChart, Line, XAxis, YAxis, Tooltip,
  BarChart, Bar, CartesianGrid, Legend
} from "recharts";
import "./styles.css";

const API_BASE = import.meta.env.VITE_API_BASE || "http://localhost:8000";
const fallbackProducts = [
  { product_id:"P1029", product_name:"Orbit Food Storage Set", category:"Home & Kitchen", risk_signal_score:85, risk_level:"High", return_rate:0.17, avg_rating:3.3 },
  { product_id:"P1024", product_name:"Lumio Trimmer", category:"Personal Care", risk_signal_score:80, risk_level:"High", return_rate:0.15, avg_rating:3.4 },
  { product_id:"P1005", product_name:"Orbit Tablet", category:"Electronics", risk_signal_score:75, risk_level:"High", return_rate:0.14, avg_rating:3.5 },
];

async function getJson(path, options) {
  const response = await fetch(`${API_BASE}${path}`, options);
  if (!response.ok) throw new Error(`${response.status} ${response.statusText}`);
  return response.json();
}

function mapProduct(row) {
  return {
    ...row,
    id: row.product_id,
    name: row.product_name,
    score: Number(row.risk_signal_score || 0),
    level: row.risk_level || "Low",
    returns: Number(row.return_rate || 0) * 100,
    rating: Number(row.avg_rating || 0),
    mlProbability: row.predicted_next_month_high_risk_probability == null
      ? null : Number(row.predicted_next_month_high_risk_probability),
  };
}

function App() {
  const [products, setProducts] = useState(fallbackProducts.map(mapProduct));
  const [selected, setSelected] = useState(mapProduct(fallbackProducts[0]));
  const [portfolio, setPortfolio] = useState({ product_count: 40, high_risk_count: 8, overall_return_rate: 0.0678, average_rating: 4.11 });
  const [selectedRisk, setSelectedRisk] = useState(null);
  const [selectedTrend, setSelectedTrend] = useState([]);
  const [question, setQuestion] = useState("Why is this product high risk and what should we investigate?");
  const [investigation, setInvestigation] = useState(null);
  const [loadingInvestigation, setLoadingInvestigation] = useState(false);
  const [tab, setTab] = useState("overview");
  const [status, setStatus] = useState("Connecting...");
  const [error, setError] = useState("");

  useEffect(() => {
    let mounted = true;
    (async () => {
      try {
        const [health, rows, summary] = await Promise.all([
          getJson("/health"), getJson("/products?limit=40"), getJson("/portfolio/summary")
        ]);
        if (!mounted) return;
        setStatus(health.status === "ok" ? "● System healthy" : "● Degraded");
        setPortfolio(summary);
        const mapped = rows.map(mapProduct);
        if (mapped.length) {
          setProducts(mapped);
          const preferred = mapped.find(p => p.id === selected.id) || mapped[0];
          setSelected(preferred);
        }
        setError("");
      } catch (err) {
        if (!mounted) return;
        setStatus("● Demo mode");
        setError("API is unavailable; showing fallback demo rows. Start the backend to load the full portfolio.");
      }
    })();
    return () => { mounted = false; };
  }, []);

  useEffect(() => {
    let mounted = true;
    (async () => {
      try {
        const [risk, trend] = await Promise.all([
          getJson(`/products/${selected.id}/risk`),
          getJson(`/products/${selected.id}/trend`),
        ]);
        if (!mounted) return;
        setSelectedRisk(risk);
        setSelectedTrend(trend.map(row => ({
          month: String(row.month), returns: Number(row.return_rate || 0) * 100,
          rating: Number(row.avg_rating || 0), tickets: Number(row.support_ticket_count || 0),
        })));
      } catch {
        if (!mounted) return;
        setSelectedRisk(null);
        setSelectedTrend([]);
      }
    })();
    return () => { mounted = false; };
  }, [selected.id]);

  const riskBuckets = useMemo(() => {
    const counts = { Low: 0, Medium: 0, High: 0 };
    products.forEach(p => { counts[p.level] = (counts[p.level] || 0) + 1; });
    return Object.entries(counts).map(([label, value]) => ({ label, value }));
  }, [products]);

  const runInvestigation = async () => {
    setLoadingInvestigation(true);
    setInvestigation(null);
    setError("");
    try {
      const result = await getJson("/investigate", {
        method: "POST", headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ product_id: selected.id, question }),
      });
      setInvestigation(result);
    } catch (err) {
      setError(`Investigation failed: ${err.message}. Check the API logs and RAG setup.`);
    } finally {
      setLoadingInvestigation(false);
    }
  };

  const riskScore = Number(selectedRisk?.risk_signal_score ?? selected.score);
  const riskLevel = selectedRisk?.risk_level ?? selected.level;
  const answer = investigation?.response;
  const trendRows = selectedTrend;

  return (
    <div className="app">
      <aside className="sidebar">
        <div className="brand"><div className="logo">P</div><div><div className="brand-title">Product Pulse</div><div className="brand-sub">Product Risk Intelligence</div></div></div>
        <nav>
          <button className={tab === "overview" ? "nav active" : "nav"} onClick={() => setTab("overview")}>Overview</button>
          <button className={tab === "investigate" ? "nav active" : "nav"} onClick={() => setTab("investigate")}>AI Investigation</button>
        </nav>
        <div className="sidebar-foot">Synthetic demo data · Jan–Dec 2025</div>
      </aside>

      <main className="content">
        <header className="topbar"><div><div className="eyebrow">PRODUCT RISK DETECTION PLATFORM</div><h1>Product Pulse</h1><p>Identify products at risk, understand the evidence, and decide what to investigate next.</p></div><span className="status">{status}</span></header>
        {error && <div className="notice">{error}</div>}

        {tab === "overview" && <>
          <section className="kpi-grid">
            <div className="kpi"><span>Products monitored</span><strong>{portfolio.product_count ?? products.length}</strong><small>across product categories</small></div>
            <div className="kpi"><span>High-risk products</span><strong>{portfolio.high_risk_count ?? riskBuckets.find(x => x.label === "High")?.value ?? 0}</strong><small>prioritized for review</small></div>
            <div className="kpi"><span>Overall return rate</span><strong>{(Number(portfolio.overall_return_rate || 0) * 100).toFixed(2)}%</strong><small>{portfolio.data_period || "2025 portfolio"}</small></div>
            <div className="kpi"><span>Average rating</span><strong>{Number(portfolio.average_rating || 0).toFixed(2)}</strong><small>out of 5</small></div>
          </section>

          <section className="grid-2">
            <div className="card"><div className="card-head"><div><h2>Portfolio risk distribution</h2><p>Risk bands for all loaded products</p></div></div><div className="chart"><ResponsiveContainer width="100%" height={260}><BarChart data={riskBuckets}><CartesianGrid strokeDasharray="3 3" /><XAxis dataKey="label" /><YAxis allowDecimals={false} /><Tooltip /><Bar dataKey="value" radius={[7,7,0,0]} /></BarChart></ResponsiveContainer></div></div>
            <div className="card"><div className="card-head"><div><h2>Selected product trend</h2><p>Return rate and rating over time</p></div></div><div className="chart"><ResponsiveContainer width="100%" height={260}><LineChart data={trendRows}><CartesianGrid strokeDasharray="3 3" /><XAxis dataKey="month" /><YAxis yAxisId="left" /><YAxis yAxisId="right" orientation="right" domain={[0, 5]} /><Tooltip /><Legend /><Line yAxisId="left" type="monotone" dataKey="returns" name="Return rate (%)" strokeWidth={2.5} dot={false} /><Line yAxisId="right" type="monotone" dataKey="rating" name="Rating" strokeWidth={2.5} dot={false} /></LineChart></ResponsiveContainer></div></div>
          </section>

          <section className="card"><div className="card-head"><div><h2>Products requiring attention</h2><p>Prioritized by trailing product-risk signals</p></div></div><div className="table-wrap"><table><thead><tr><th>Product</th><th>Category</th><th>Risk</th><th>Return rate</th><th>Rating</th><th>ML probability</th><th></th></tr></thead><tbody>
            {products.map(p => <tr key={p.id}><td><strong>{p.name}</strong><div className="muted">{p.id}</div></td><td>{p.category}</td><td><span className={`risk ${p.level.toLowerCase()}`}>{p.level} · {p.score.toFixed(1)}</span></td><td>{p.returns.toFixed(1)}%</td><td>{p.rating.toFixed(2)}</td><td>{p.mlProbability == null ? "—" : `${(p.mlProbability * 100).toFixed(1)}%`}</td><td><button className="small-btn" onClick={() => { setSelected(p); setTab("investigate"); setInvestigation(null); }}>Investigate</button></td></tr>)}
          </tbody></table></div></section>
        </>}

        {tab === "investigate" && <>
          <section className="investigate-head"><div><div className="eyebrow">AI INVESTIGATION</div><h2>{selected.name}</h2><p>{selected.id} · {selected.category}</p></div><div className="risk-box"><span>Risk score</span><strong>{riskScore.toFixed(1)}/100</strong><em>{riskLevel}</em></div></section>
          <section className="card select-card"><label htmlFor="product-select">Product</label><select id="product-select" value={selected.id} onChange={e => { const p = products.find(x => x.id === e.target.value); if (p) { setSelected(p); setInvestigation(null); } }}>{products.map(p => <option key={p.id} value={p.id}>{p.id} — {p.name}</option>)}</select></section>
          <section className="grid-2">
            <div className="card"><h3>Ask Product Pulse</h3><div className="query-row"><input value={question} onChange={e => setQuestion(e.target.value)} onKeyDown={e => { if (e.key === "Enter") runInvestigation(); }} /><button className="primary" onClick={runInvestigation} disabled={loadingInvestigation}>{loadingInvestigation ? "Investigating…" : "Investigate"}</button></div>
              {!answer && <p className="muted">Ask a question to retrieve product knowledge and generate an evidence-backed investigation.</p>}
              {answer && <div className="answer"><h4>Findings</h4><ul>{(answer.findings || []).map((x, i) => <li key={i}>{x}</li>)}</ul><h4>Likely root-cause candidates</h4><ul>{(answer.root_cause_candidates || []).map((x, i) => <li key={i}>{x}</li>)}</ul><h4>Recommended actions</h4><ul>{(answer.recommended_actions || []).map((x, i) => <li key={i}>{x}</li>)}</ul><p className="muted">{answer.disclaimer}</p></div>}
            </div>
            <div className="card"><h3>Evidence & sources</h3>{!answer ? <div className="evidence-list"><div className="evidence"><span>•</span>Risk score: {riskScore.toFixed(1)}/100</div><div className="evidence"><span>•</span>Trailing return rate: {(Number(selectedRisk?.return_rate ?? selected.returns / 100) * 100).toFixed(1)}%</div><div className="evidence"><span>•</span>Average rating: {Number(selectedRisk?.avg_rating ?? selected.rating).toFixed(2)}/5</div></div> : <><h4>Evidence</h4><ul>{(answer.evidence || []).map((x, i) => <li key={i}>{x}</li>)}</ul><h4>Retrieved sources</h4><div className="evidence-list">{(investigation.retrieved_sources || []).map(s => <div className="evidence" key={s.document_id}><span>↳</span><div><strong>{s.title}</strong><div className="muted">{s.document_id} · {s.document_type} · score {Number(s.score || 0).toFixed(3)}</div></div></div>)}</div></>}</div>
          </section>
          <section className="card"><div className="card-head"><div><h2>Product trend</h2><p>Return rate, customer rating, and support volume by month</p></div></div><div className="chart"><ResponsiveContainer width="100%" height={300}><LineChart data={trendRows}><CartesianGrid strokeDasharray="3 3" /><XAxis dataKey="month" /><YAxis yAxisId="left" /><YAxis yAxisId="right" orientation="right" domain={[0, 5]} /><Tooltip /><Legend /><Line yAxisId="left" type="monotone" dataKey="returns" name="Return rate (%)" strokeWidth={2.5} dot={false} /><Line yAxisId="right" type="monotone" dataKey="rating" name="Rating" strokeWidth={2.5} dot={false} /></LineChart></ResponsiveContainer></div></section>
          <div className="disclaimer">Decision support only. Risk scores and generated root-cause candidates are not proof of causality and should be validated by the product-quality team.</div>
        </>}
      </main>
    </div>
  );
}

createRoot(document.getElementById("root")).render(<App />);
