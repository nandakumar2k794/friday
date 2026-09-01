import React, { useState } from 'react'
import { createRoot } from 'react-dom/client'
import './styles.css'

const API = import.meta.env.VITE_API_URL || 'http://127.0.0.1:8000'

function App() {
  const [query, setQuery] = useState('')
  const [results, setResults] = useState([])
  const [selected, setSelected] = useState(null)
  const [map, setMap] = useState(null)
  const [saved, setSaved] = useState(null)
  const [error, setError] = useState('')

  async function search(value) {
    setQuery(value); setError(''); setSaved(null)
    if (!value.trim()) return setResults([])
    try { const body = await fetch(`${API}/search?q=${encodeURIComponent(value)}`).then(r => r.json()); setResults(body.results || []) }
    catch { setError('API unavailable. Start FastAPI on port 8000.'); }
  }
  function choose(item) {
    setSelected(item); setMap(null); setSaved(null)
  }
  async function save() {
    if (!selected) return
    const response = await fetch(`${API}/Condition`, {method: 'POST', headers: {'Content-Type': 'application/json', Authorization: 'Bearer demo-abha-token'},
      body: JSON.stringify({patient_id: 'Patient/demo-live-001', encounter_id: 'Encounter/demo-live-001', namaste_code: selected.namaste_code, note: 'Saved during live SIH demo.'})})
    const body = await response.json(); if (!response.ok) return setError(body.detail || 'Unable to save')
    setSaved(body)
  }
  const targets = selected?.icd11_tm2_code ? [{code: selected.icd11_tm2_code, display: selected.icd11_tm2_title, equivalence: selected.equivalence}] : []
  return <main className="min-h-screen bg-slate-50 p-6 text-slate-900"><section className="mx-auto max-w-4xl">
    <p className="text-sm font-semibold text-teal-700">SIH25026 · MOCK TERMINOLOGY DEMO</p><h1 className="mt-1 text-3xl font-bold">NAMASTE → ICD-11 TM2</h1>
    <p className="mt-2 text-slate-600">Search a mock Ayurveda/Siddha/Unani diagnosis, inspect its FHIR ConceptMap, then save a dual-coded Condition.</p>
    <input className="mt-6 w-full rounded-lg border border-slate-300 bg-white p-3 shadow-sm" value={query} onChange={e => search(e.target.value)} placeholder="Try: SR11, Amavata, Vatha Suronitham..." />
    {results.length > 0 && <div className="mt-2 overflow-hidden rounded-lg border bg-white">{results.map(r => <button key={`${r.namaste_code}-${r.icd11_tm2_code || 'none'}`} onClick={() => choose(r)} className="block w-full border-b p-3 text-left hover:bg-teal-50"><span className="mr-2 rounded bg-slate-100 px-2 py-1 text-xs font-bold">{r.system}</span><span className="font-semibold">{r.namaste_title}</span><span className="ml-2 text-sm text-slate-500">{r.namaste_code} → {r.icd11_tm2_code || 'No mapping'}</span></button>)}</div>}
    {selected && <section className="mt-6 rounded-xl bg-white p-5 shadow"><h2 className="text-lg font-bold">Selected: {selected.namaste_title}</h2><p className="mt-1 font-mono text-sm">{selected.system} · {selected.namaste_code}</p>
      {targets.length > 0 && <div className="mt-4"><p className="font-semibold">Mapped ICD-11 TM2</p>{targets.map(t => <div key={t.code} className="mt-2 rounded border-l-4 border-teal-500 bg-teal-50 p-3"><b>{t.display}</b> <span className="font-mono text-sm">{t.code}</span><span className="ml-2 text-sm">({t.equivalence})</span></div>)}</div>}
      {!selected.icd11_tm2_code && <p className="mt-4 rounded bg-amber-50 p-3 text-amber-800">No ICD-11 mapping found.</p>}
      <button onClick={save} className="mt-5 rounded-lg bg-teal-700 px-4 py-2 font-semibold text-white hover:bg-teal-800">Save to Problem List</button>
    </section>}
    {error && <p className="mt-4 rounded bg-red-50 p-3 text-red-700">{error}</p>}
    {saved && <section className="mt-6"><h2 className="font-bold">Saved FHIR R4 Condition</h2><pre className="mt-2 max-h-96 overflow-auto rounded-lg bg-slate-900 p-4 text-xs text-emerald-200">{JSON.stringify(saved, null, 2)}</pre></section>}
  </section></main>
}
createRoot(document.getElementById('root')).render(<App />)
