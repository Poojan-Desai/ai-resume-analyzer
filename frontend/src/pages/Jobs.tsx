import { useCallback, useEffect, useState } from 'react'
import { api } from '../api/client'
import type {
  CoverLetter,
  JobMatch,
  JobPosting,
  ResumeListItem,
  SkillGap,
} from '../types'

/**
 * Save job descriptions, then run match / cover letter / skill gap vs a resume.
 */
export function JobsPage() {
  const [jobs, setJobs] = useState<JobPosting[]>([])
  const [resumes, setResumes] = useState<ResumeListItem[]>([])
  const [jobId, setJobId] = useState<number | null>(null)
  const [resumeId, setResumeId] = useState<number | null>(null)
  const [title, setTitle] = useState('')
  const [company, setCompany] = useState('')
  const [description, setDescription] = useState('')
  const [tone, setTone] = useState('professional')
  const [loading, setLoading] = useState(false)
  const [msg, setMsg] = useState<string | null>(null)

  const [match, setMatch] = useState<JobMatch | null>(null)
  const [letter, setLetter] = useState<CoverLetter | null>(null)
  const [gaps, setGaps] = useState<SkillGap | null>(null)

  const load = useCallback(() => {
    api.get<JobPosting[]>('/api/jobs').then((r) => setJobs(r.data))
    api.get<ResumeListItem[]>('/api/resumes').then((r) => setResumes(r.data))
  }, [])

  useEffect(() => {
    load()
  }, [load])

  async function saveJob(e: React.FormEvent) {
    e.preventDefault()
    setLoading(true)
    setMsg(null)
    try {
      const { data } = await api.post<JobPosting>('/api/jobs', {
        title: title || 'Untitled role',
        company,
        description,
      })
      setMsg(`Saved job #${data.id}`)
      setJobId(data.id)
      setTitle('')
      setCompany('')
      setDescription('')
      load()
    } catch {
      setMsg('Could not save job')
    } finally {
      setLoading(false)
    }
  }

  async function runMatch() {
    if (!jobId || !resumeId) {
      setMsg('Select a job and a resume.')
      return
    }
    setLoading(true)
    setMsg(null)
    try {
      const { data } = await api.post<JobMatch>(`/api/jobs/${jobId}/match`, {
        resume_id: resumeId,
      })
      setMatch(data)
      setMsg('Match computed.')
    } catch (err: unknown) {
      const ax = err as { response?: { data?: { detail?: string } } }
      setMsg(ax.response?.data?.detail ?? 'Match failed')
    } finally {
      setLoading(false)
    }
  }

  async function runCover() {
    if (!jobId || !resumeId) {
      setMsg('Select a job and a resume.')
      return
    }
    setLoading(true)
    setMsg(null)
    try {
      const { data } = await api.post<CoverLetter>(
        `/api/jobs/${jobId}/cover-letter`,
        { resume_id: resumeId, tone },
      )
      setLetter(data)
      setMsg('Cover letter generated.')
    } catch (err: unknown) {
      const ax = err as { response?: { data?: { detail?: string } } }
      setMsg(ax.response?.data?.detail ?? 'Cover letter failed')
    } finally {
      setLoading(false)
    }
  }

  async function runGaps() {
    if (!jobId || !resumeId) {
      setMsg('Select a job and a resume.')
      return
    }
    setLoading(true)
    setMsg(null)
    try {
      const { data } = await api.post<SkillGap>(
        `/api/jobs/${jobId}/skill-gap`,
        { resume_id: resumeId },
      )
      setGaps(data)
      setMsg('Skill gap analysis done.')
    } catch (err: unknown) {
      const ax = err as { response?: { data?: { detail?: string } } }
      setMsg(ax.response?.data?.detail ?? 'Skill gap failed')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="space-y-8">
      <div>
        <h2 className="text-2xl font-semibold text-white">Jobs &amp; AI tools</h2>
        <p className="mt-1 text-slate-400">
          Paste a full job description, then pair it with a resume for matching,
          cover letters, and skill gaps.
        </p>
      </div>

      <form
        onSubmit={saveJob}
        className="space-y-4 rounded-xl border border-slate-800 bg-slate-900/50 p-5"
      >
        <h3 className="font-medium text-white">New job posting</h3>
        <div className="grid gap-3 sm:grid-cols-2">
          <div>
            <label className="text-xs text-slate-400">Title</label>
            <input
              className="mt-1 w-full rounded-lg border border-slate-700 bg-slate-950 px-3 py-2 text-sm text-white"
              value={title}
              onChange={(e) => setTitle(e.target.value)}
              placeholder="Role title"
            />
          </div>
          <div>
            <label className="text-xs text-slate-400">Company</label>
            <input
              className="mt-1 w-full rounded-lg border border-slate-700 bg-slate-950 px-3 py-2 text-sm text-white"
              value={company}
              onChange={(e) => setCompany(e.target.value)}
              placeholder="Company name"
            />
          </div>
        </div>
        <div>
          <label className="text-xs text-slate-400">Job description</label>
          <textarea
            className="mt-1 min-h-[140px] w-full rounded-lg border border-slate-700 bg-slate-950 px-3 py-2 text-sm text-white"
            value={description}
            onChange={(e) => setDescription(e.target.value)}
            placeholder="Paste the full description here…"
            required
          />
        </div>
        <button
          type="submit"
          disabled={loading}
          className="rounded-lg bg-indigo-600 px-4 py-2 text-sm font-medium text-white hover:bg-indigo-500 disabled:opacity-50"
        >
          Save job
        </button>
        {msg && <p className="text-sm text-slate-300">{msg}</p>}
      </form>

      <div className="grid gap-4 lg:grid-cols-2">
        <section className="rounded-xl border border-slate-800 bg-slate-900/50 p-5">
          <h3 className="font-medium text-white">Select job</h3>
          <select
            className="mt-2 w-full rounded-lg border border-slate-700 bg-slate-950 px-3 py-2 text-sm text-white"
            value={jobId ?? ''}
            onChange={(e) =>
              setJobId(e.target.value ? Number(e.target.value) : null)
            }
          >
            <option value="">— Choose —</option>
            {jobs.map((j) => (
              <option key={j.id} value={j.id}>
                {j.company} — {j.title} (#{j.id})
              </option>
            ))}
          </select>

          <h3 className="mt-6 font-medium text-white">Select resume</h3>
          <select
            className="mt-2 w-full rounded-lg border border-slate-700 bg-slate-950 px-3 py-2 text-sm text-white"
            value={resumeId ?? ''}
            onChange={(e) =>
              setResumeId(e.target.value ? Number(e.target.value) : null)
            }
          >
            <option value="">— Choose —</option>
            {resumes.map((r) => (
              <option key={r.id} value={r.id}>
                {r.filename} (#{r.id})
              </option>
            ))}
          </select>

          <div className="mt-6 flex flex-wrap gap-2">
            <button
              type="button"
              onClick={runMatch}
              disabled={loading}
              className="rounded-lg bg-slate-800 px-3 py-2 text-sm text-white hover:bg-slate-700"
            >
              Match score
            </button>
            <button
              type="button"
              onClick={runCover}
              disabled={loading}
              className="rounded-lg bg-slate-800 px-3 py-2 text-sm text-white hover:bg-slate-700"
            >
              Cover letter
            </button>
            <button
              type="button"
              onClick={runGaps}
              disabled={loading}
              className="rounded-lg bg-slate-800 px-3 py-2 text-sm text-white hover:bg-slate-700"
            >
              Skill gaps
            </button>
          </div>

          <div className="mt-4">
            <label className="text-xs text-slate-400">Cover letter tone</label>
            <select
              className="mt-1 w-full rounded-lg border border-slate-700 bg-slate-950 px-3 py-2 text-sm text-white"
              value={tone}
              onChange={(e) => setTone(e.target.value)}
            >
              <option value="professional">Professional</option>
              <option value="enthusiastic">Enthusiastic</option>
              <option value="concise">Concise</option>
            </select>
          </div>
        </section>

        <section className="space-y-4">
          {match && (
            <div className="rounded-xl border border-emerald-500/30 bg-slate-900/50 p-5">
              <h3 className="font-medium text-emerald-300">
                Match: {match.score}%
              </h3>
              <p className="mt-2 text-sm text-slate-300">{match.summary}</p>
              <p className="mt-3 text-xs uppercase text-slate-500">Keywords</p>
              <div className="mt-1 flex flex-wrap gap-1">
                {match.matched_keywords.map((k, i) => (
                  <span
                    key={i}
                    className="rounded bg-emerald-950/80 px-2 py-0.5 text-xs text-emerald-200"
                  >
                    {k}
                  </span>
                ))}
              </div>
              <p className="mt-3 text-xs uppercase text-slate-500">Gaps</p>
              <ul className="mt-1 list-inside list-disc text-sm text-slate-400">
                {match.gaps.map((g, i) => (
                  <li key={i}>{g}</li>
                ))}
              </ul>
            </div>
          )}

          {gaps && (
            <div className="rounded-xl border border-amber-500/30 bg-slate-900/50 p-5">
              <h3 className="font-medium text-amber-200">Skill gaps</h3>
              <ul className="mt-2 list-inside list-disc text-sm text-slate-300">
                {gaps.missing_skills.map((s, i) => (
                  <li key={i}>{s}</li>
                ))}
              </ul>
              <p className="mt-3 text-xs uppercase text-slate-500">Priority</p>
              <ol className="mt-1 list-inside list-decimal text-sm text-slate-400">
                {gaps.priority_order.map((s, i) => (
                  <li key={i}>{s}</li>
                ))}
              </ol>
              <p className="mt-3 text-xs uppercase text-slate-500">Resources</p>
              <ul className="mt-1 list-inside list-disc text-sm text-slate-400">
                {gaps.suggested_resources.map((s, i) => (
                  <li key={i}>{s}</li>
                ))}
              </ul>
            </div>
          )}
        </section>
      </div>

      {letter && (
        <section className="rounded-xl border border-indigo-500/30 bg-slate-900/50 p-5">
          <div className="flex items-center justify-between gap-2">
            <h3 className="font-medium text-indigo-200">Cover letter</h3>
            <button
              type="button"
              onClick={() =>
                navigator.clipboard.writeText(letter.content).then(() =>
                  setMsg('Copied to clipboard.'),
                )
              }
              className="text-xs text-indigo-400 hover:text-indigo-300"
            >
              Copy
            </button>
          </div>
          <pre className="mt-4 max-h-96 overflow-auto whitespace-pre-wrap text-sm text-slate-300">
            {letter.content}
          </pre>
        </section>
      )}
    </div>
  )
}
