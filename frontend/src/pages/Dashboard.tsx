import { useEffect, useState } from 'react'
import { api } from '../api/client'
import type { Dashboard as DashboardType } from '../types'

/**
 * Home page: counts and recent AI activity from GET /api/dashboard.
 */
export function DashboardPage() {
  const [data, setData] = useState<DashboardType | null>(null)
  const [error, setError] = useState<string | null>(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    api
      .get<DashboardType>('/api/dashboard')
      .then((r) => setData(r.data))
      .catch((e) => setError(e?.response?.data?.detail ?? e.message))
      .finally(() => setLoading(false))
  }, [])

  if (loading) {
    return <p className="text-slate-400">Loading dashboard…</p>
  }
  if (error) {
    return (
      <div className="rounded-xl border border-red-500/40 bg-red-950/40 p-4 text-red-200">
        <p className="font-medium">Could not load dashboard</p>
        <p className="mt-1 text-sm opacity-90">{error}</p>
        <p className="mt-3 text-sm text-slate-400">
          Is the API running? From the project folder run:{' '}
          <code className="rounded bg-slate-800 px-1 py-0.5">
            cd backend && source .venv/bin/activate && uvicorn app.main:app
            --reload
          </code>
        </p>
      </div>
    )
  }
  if (!data) return null

  return (
    <div className="space-y-8">
      <div>
        <h2 className="text-2xl font-semibold text-white">Overview</h2>
        <p className="mt-1 text-slate-400">
          Quick snapshot of your resumes, jobs, and applications.
        </p>
      </div>

      <div className="grid gap-4 sm:grid-cols-3">
        <StatCard label="Resumes" value={data.resume_count} />
        <StatCard label="Job descriptions" value={data.job_count} />
        <StatCard label="Applications" value={data.application_count} />
      </div>

      <div className="grid gap-6 lg:grid-cols-2">
        <section className="rounded-xl border border-slate-800 bg-slate-900/50 p-5">
          <h3 className="text-sm font-semibold uppercase tracking-wide text-slate-400">
            Recent resume feedback
          </h3>
          <ul className="mt-4 space-y-3">
            {data.recent_feedbacks.length === 0 && (
              <li className="text-sm text-slate-500">No analyses yet.</li>
            )}
            {data.recent_feedbacks.map((f) => (
              <li
                key={f.id}
                className="rounded-lg border border-slate-800 bg-slate-950/60 p-3 text-sm"
              >
                <div className="flex justify-between gap-2">
                  <span className="text-indigo-300">
                    Score: {f.overall_score ?? '—'}
                  </span>
                  <span className="text-xs text-slate-500">
                    {new Date(f.created_at).toLocaleString()}
                  </span>
                </div>
                <p className="mt-2 text-slate-300 line-clamp-3">{f.summary}</p>
              </li>
            ))}
          </ul>
        </section>

        <section className="rounded-xl border border-slate-800 bg-slate-900/50 p-5">
          <h3 className="text-sm font-semibold uppercase tracking-wide text-slate-400">
            Recent job matches
          </h3>
          <ul className="mt-4 space-y-3">
            {data.recent_matches.length === 0 && (
              <li className="text-sm text-slate-500">No matches yet.</li>
            )}
            {data.recent_matches.map((m) => (
              <li
                key={m.id}
                className="rounded-lg border border-slate-800 bg-slate-950/60 p-3 text-sm"
              >
                <div className="flex justify-between gap-2">
                  <span className="text-emerald-300">Match: {m.score}%</span>
                  <span className="text-xs text-slate-500">
                    {new Date(m.created_at).toLocaleString()}
                  </span>
                </div>
                <p className="mt-2 text-slate-300 line-clamp-3">{m.summary}</p>
              </li>
            ))}
          </ul>
        </section>
      </div>

      <section className="rounded-xl border border-slate-800 bg-slate-900/50 p-5">
        <h3 className="text-sm font-semibold uppercase tracking-wide text-slate-400">
          Applications by status
        </h3>
        <div className="mt-4 flex flex-wrap gap-2">
          {Object.keys(data.applications_by_status).length === 0 && (
            <span className="text-sm text-slate-500">No applications yet.</span>
          )}
          {Object.entries(data.applications_by_status).map(([k, v]) => (
            <span
              key={k}
              className="rounded-full border border-slate-700 bg-slate-950 px-3 py-1 text-sm text-slate-200"
            >
              {k}: <strong>{v}</strong>
            </span>
          ))}
        </div>
      </section>
    </div>
  )
}

function StatCard({ label, value }: { label: string; value: number }) {
  return (
    <div className="rounded-xl border border-slate-800 bg-gradient-to-br from-slate-900 to-slate-950 p-5 shadow-inner">
      <p className="text-xs uppercase tracking-wide text-slate-500">{label}</p>
      <p className="mt-2 text-3xl font-semibold text-white">{value}</p>
    </div>
  )
}
