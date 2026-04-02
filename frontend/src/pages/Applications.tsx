import { useCallback, useEffect, useState } from 'react'
import { api } from '../api/client'
import type { Application, JobPosting, ResumeListItem } from '../types'

const STATUSES = ['draft', 'applied', 'interview', 'offer', 'rejected']

/**
 * CRUD for application tracker; links optional resume / job posting IDs.
 */
export function ApplicationsPage() {
  const [items, setItems] = useState<Application[]>([])
  const [resumes, setResumes] = useState<ResumeListItem[]>([])
  const [jobs, setJobs] = useState<JobPosting[]>([])
  const [company, setCompany] = useState('')
  const [role, setRole] = useState('')
  const [status, setStatus] = useState('draft')
  const [notes, setNotes] = useState('')
  const [url, setUrl] = useState('')
  const [resumeId, setResumeId] = useState<number | ''>('')
  const [jobId, setJobId] = useState<number | ''>('')
  const [msg, setMsg] = useState<string | null>(null)

  const load = useCallback(() => {
    api.get<Application[]>('/api/applications').then((r) => setItems(r.data))
    api.get<ResumeListItem[]>('/api/resumes').then((r) => setResumes(r.data))
    api.get<JobPosting[]>('/api/jobs').then((r) => setJobs(r.data))
  }, [])

  useEffect(() => {
    load()
  }, [load])

  async function add(e: React.FormEvent) {
    e.preventDefault()
    setMsg(null)
    try {
      await api.post('/api/applications', {
        company_name: company,
        role_title: role,
        status,
        notes,
        job_url: url,
        resume_id: resumeId === '' ? null : resumeId,
        job_posting_id: jobId === '' ? null : jobId,
      })
      setCompany('')
      setRole('')
      setNotes('')
      setUrl('')
      setResumeId('')
      setJobId('')
      setMsg('Application added.')
      load()
    } catch {
      setMsg('Could not add application.')
    }
  }

  async function patchStatus(id: number, next: string) {
    await api.patch(`/api/applications/${id}`, { status: next })
    load()
  }

  async function remove(id: number) {
    if (!confirm('Delete this application?')) return
    await api.delete(`/api/applications/${id}`)
    load()
  }

  return (
    <div className="space-y-8">
      <div>
        <h2 className="text-2xl font-semibold text-white">Applications</h2>
        <p className="mt-1 text-slate-400">
          Track where you applied; optionally link a saved resume or job posting.
        </p>
      </div>

      <form
        onSubmit={add}
        className="grid gap-3 rounded-xl border border-slate-800 bg-slate-900/50 p-5 sm:grid-cols-2"
      >
        <div className="sm:col-span-2">
          <h3 className="font-medium text-white">Add application</h3>
        </div>
        <div>
          <label className="text-xs text-slate-400">Company</label>
          <input
            required
            className="mt-1 w-full rounded-lg border border-slate-700 bg-slate-950 px-3 py-2 text-sm text-white"
            value={company}
            onChange={(e) => setCompany(e.target.value)}
          />
        </div>
        <div>
          <label className="text-xs text-slate-400">Role</label>
          <input
            className="mt-1 w-full rounded-lg border border-slate-700 bg-slate-950 px-3 py-2 text-sm text-white"
            value={role}
            onChange={(e) => setRole(e.target.value)}
          />
        </div>
        <div>
          <label className="text-xs text-slate-400">Status</label>
          <select
            className="mt-1 w-full rounded-lg border border-slate-700 bg-slate-950 px-3 py-2 text-sm text-white"
            value={status}
            onChange={(e) => setStatus(e.target.value)}
          >
            {STATUSES.map((s) => (
              <option key={s} value={s}>
                {s}
              </option>
            ))}
          </select>
        </div>
        <div>
          <label className="text-xs text-slate-400">Job URL</label>
          <input
            className="mt-1 w-full rounded-lg border border-slate-700 bg-slate-950 px-3 py-2 text-sm text-white"
            value={url}
            onChange={(e) => setUrl(e.target.value)}
            placeholder="https://…"
          />
        </div>
        <div>
          <label className="text-xs text-slate-400">Resume (optional)</label>
          <select
            className="mt-1 w-full rounded-lg border border-slate-700 bg-slate-950 px-3 py-2 text-sm text-white"
            value={resumeId}
            onChange={(e) =>
              setResumeId(e.target.value === '' ? '' : Number(e.target.value))
            }
          >
            <option value="">—</option>
            {resumes.map((r) => (
              <option key={r.id} value={r.id}>
                {r.filename}
              </option>
            ))}
          </select>
        </div>
        <div>
          <label className="text-xs text-slate-400">Job posting (optional)</label>
          <select
            className="mt-1 w-full rounded-lg border border-slate-700 bg-slate-950 px-3 py-2 text-sm text-white"
            value={jobId}
            onChange={(e) =>
              setJobId(e.target.value === '' ? '' : Number(e.target.value))
            }
          >
            <option value="">—</option>
            {jobs.map((j) => (
              <option key={j.id} value={j.id}>
                {j.company} — {j.title}
              </option>
            ))}
          </select>
        </div>
        <div className="sm:col-span-2">
          <label className="text-xs text-slate-400">Notes</label>
          <textarea
            className="mt-1 min-h-[72px] w-full rounded-lg border border-slate-700 bg-slate-950 px-3 py-2 text-sm text-white"
            value={notes}
            onChange={(e) => setNotes(e.target.value)}
          />
        </div>
        <div className="sm:col-span-2">
          <button
            type="submit"
            className="rounded-lg bg-indigo-600 px-4 py-2 text-sm font-medium text-white hover:bg-indigo-500"
          >
            Save
          </button>
          {msg && <span className="ml-3 text-sm text-slate-400">{msg}</span>}
        </div>
      </form>

      <div className="overflow-x-auto rounded-xl border border-slate-800">
        <table className="w-full min-w-[640px] text-left text-sm">
          <thead className="border-b border-slate-800 bg-slate-900/80 text-xs uppercase text-slate-500">
            <tr>
              <th className="px-4 py-3">Company</th>
              <th className="px-4 py-3">Role</th>
              <th className="px-4 py-3">Status</th>
              <th className="px-4 py-3">Actions</th>
            </tr>
          </thead>
          <tbody>
            {items.length === 0 && (
              <tr>
                <td colSpan={4} className="px-4 py-8 text-center text-slate-500">
                  No applications yet.
                </td>
              </tr>
            )}
            {items.map((a) => (
              <tr key={a.id} className="border-b border-slate-800/80 hover:bg-slate-900/40">
                <td className="px-4 py-3 font-medium text-white">{a.company_name}</td>
                <td className="px-4 py-3 text-slate-300">{a.role_title}</td>
                <td className="px-4 py-3">
                  <select
                    className="rounded border border-slate-700 bg-slate-950 px-2 py-1 text-xs text-white"
                    value={a.status}
                    onChange={(e) => patchStatus(a.id, e.target.value)}
                  >
                    {STATUSES.map((s) => (
                      <option key={s} value={s}>
                        {s}
                      </option>
                    ))}
                  </select>
                </td>
                <td className="px-4 py-3">
                  <button
                    type="button"
                    onClick={() => remove(a.id)}
                    className="text-xs text-red-400 hover:text-red-300"
                  >
                    Delete
                  </button>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  )
}
