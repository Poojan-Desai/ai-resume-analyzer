import { useCallback, useEffect, useState } from 'react'
import { api } from '../api/client'
import type { Resume, ResumeFeedback, ResumeListItem } from '../types'

/**
 * Upload PDF/DOCX, list resumes, run AI feedback (POST /api/resumes/:id/analyze).
 */
export function ResumesPage() {
  const [list, setList] = useState<ResumeListItem[]>([])
  const [selectedId, setSelectedId] = useState<number | null>(null)
  const [detail, setDetail] = useState<Resume | null>(null)
  const [feedbacks, setFeedbacks] = useState<ResumeFeedback[]>([])
  const [targetRole, setTargetRole] = useState('')
  const [loading, setLoading] = useState(false)
  const [msg, setMsg] = useState<string | null>(null)

  const refreshList = useCallback(() => {
    api
      .get<ResumeListItem[]>('/api/resumes')
      .then((r) => setList(r.data))
      .catch(() => setMsg('Failed to load resumes'))
  }, [])

  useEffect(() => {
    refreshList()
  }, [refreshList])

  useEffect(() => {
    if (!selectedId) {
      setDetail(null)
      setFeedbacks([])
      return
    }
    api.get<Resume>(`/api/resumes/${selectedId}`).then((r) => setDetail(r.data))
    api
      .get<ResumeFeedback[]>(`/api/resumes/${selectedId}/feedbacks`)
      .then((r) => setFeedbacks(r.data))
      .catch(() => setFeedbacks([]))
  }, [selectedId])

  async function onUpload(e: React.ChangeEvent<HTMLInputElement>) {
    const file = e.target.files?.[0]
    if (!file) return
    setLoading(true)
    setMsg(null)
    const fd = new FormData()
    fd.append('file', file)
    try {
      const { data } = await api.post<Resume>('/api/resumes/upload', fd, {
        headers: { 'Content-Type': 'multipart/form-data' },
      })
      setMsg(`Uploaded: ${data.filename}`)
      setSelectedId(data.id)
      refreshList()
    } catch (err: unknown) {
      const ax = err as { response?: { data?: { detail?: string } } }
      setMsg(ax.response?.data?.detail ?? 'Upload failed')
    } finally {
      setLoading(false)
      e.target.value = ''
    }
  }

  async function runAnalyze() {
    if (!selectedId) return
    setLoading(true)
    setMsg(null)
    try {
      await api.post(`/api/resumes/${selectedId}/analyze`, {
        target_role: targetRole,
      })
      const fb = await api.get<ResumeFeedback[]>(
        `/api/resumes/${selectedId}/feedbacks`,
      )
      setFeedbacks(fb.data)
      setMsg('Analysis complete.')
    } catch (err: unknown) {
      const ax = err as { response?: { data?: { detail?: string } } }
      setMsg(ax.response?.data?.detail ?? 'Analysis failed — check OPENAI_API_KEY on server')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="space-y-8">
      <div>
        <h2 className="text-2xl font-semibold text-white">Resumes</h2>
        <p className="mt-1 text-slate-400">
          Upload a PDF or Word file. Text is extracted on the server; nothing is
          sent to OpenAI until you click Analyze.
        </p>
      </div>

      <div className="rounded-xl border border-slate-800 bg-slate-900/50 p-5">
        <label className="block text-sm font-medium text-slate-300">
          Upload resume
        </label>
        <input
          type="file"
          accept=".pdf,.docx"
          onChange={onUpload}
          disabled={loading}
          className="mt-2 block w-full text-sm text-slate-300 file:mr-4 file:rounded-lg file:border-0 file:bg-indigo-600 file:px-4 file:py-2 file:text-sm file:font-medium file:text-white hover:file:bg-indigo-500"
        />
        {msg && (
          <p className="mt-3 text-sm text-slate-300" role="status">
            {msg}
          </p>
        )}
      </div>

      <div className="grid gap-6 lg:grid-cols-2">
        <section className="rounded-xl border border-slate-800 bg-slate-900/50 p-5">
          <h3 className="font-medium text-white">Your files</h3>
          <ul className="mt-3 max-h-64 space-y-2 overflow-y-auto">
            {list.length === 0 && (
              <li className="text-sm text-slate-500">No resumes yet.</li>
            )}
            {list.map((r) => (
              <li key={r.id}>
                <button
                  type="button"
                  onClick={() => setSelectedId(r.id)}
                  className={`w-full rounded-lg border px-3 py-2 text-left text-sm transition-colors ${
                    selectedId === r.id
                      ? 'border-indigo-500 bg-indigo-500/10 text-white'
                      : 'border-slate-700 bg-slate-950/50 text-slate-300 hover:border-slate-600'
                  }`}
                >
                  {r.filename}
                  <span className="mt-1 block text-xs text-slate-500">
                    {new Date(r.created_at).toLocaleString()}
                  </span>
                </button>
              </li>
            ))}
          </ul>
        </section>

        <section className="rounded-xl border border-slate-800 bg-slate-900/50 p-5">
          <h3 className="font-medium text-white">AI feedback</h3>
          <p className="mt-1 text-sm text-slate-500">
            Optional: target role helps the model tailor advice.
          </p>
          <input
            type="text"
            placeholder="e.g. Software Engineer Intern"
            value={targetRole}
            onChange={(e) => setTargetRole(e.target.value)}
            className="mt-3 w-full rounded-lg border border-slate-700 bg-slate-950 px-3 py-2 text-sm text-white placeholder:text-slate-600 focus:border-indigo-500 focus:outline-none focus:ring-1 focus:ring-indigo-500"
          />
          <button
            type="button"
            disabled={!selectedId || loading}
            onClick={runAnalyze}
            className="mt-3 rounded-lg bg-indigo-600 px-4 py-2 text-sm font-medium text-white hover:bg-indigo-500 disabled:cursor-not-allowed disabled:opacity-50"
          >
            {loading ? 'Working…' : 'Run AI analysis'}
          </button>

          {feedbacks[0] && (
            <div className="mt-6 space-y-4 text-sm">
              <div className="flex items-baseline justify-between gap-2">
                <span className="text-slate-400">Overall score</span>
                <span className="text-2xl font-semibold text-indigo-300">
                  {feedbacks[0].overall_score}
                </span>
              </div>
              <p className="text-slate-300">{feedbacks[0].summary}</p>
              <div>
                <h4 className="text-xs font-semibold uppercase text-emerald-400">
                  Strengths
                </h4>
                <ul className="mt-1 list-inside list-disc text-slate-300">
                  {feedbacks[0].strengths.map((s, i) => (
                    <li key={i}>{s}</li>
                  ))}
                </ul>
              </div>
              <div>
                <h4 className="text-xs font-semibold uppercase text-amber-400">
                  Weaknesses
                </h4>
                <ul className="mt-1 list-inside list-disc text-slate-300">
                  {feedbacks[0].weaknesses.map((s, i) => (
                    <li key={i}>{s}</li>
                  ))}
                </ul>
              </div>
              <div>
                <h4 className="text-xs font-semibold uppercase text-sky-400">
                  Improvements
                </h4>
                <ul className="mt-1 list-inside list-disc text-slate-300">
                  {feedbacks[0].improvements.map((s, i) => (
                    <li key={i}>{s}</li>
                  ))}
                </ul>
              </div>
            </div>
          )}
        </section>
      </div>

      {detail && (
        <section className="rounded-xl border border-slate-800 bg-slate-900/50 p-5">
          <h3 className="font-medium text-white">Extracted text preview</h3>
          <p className="mt-1 text-xs text-slate-500">
            First ~2000 characters — full text stays in SQLite on the server.
          </p>
          <pre className="mt-3 max-h-64 overflow-auto whitespace-pre-wrap rounded-lg bg-slate-950 p-4 text-xs text-slate-400">
            {detail.extracted_text.slice(0, 2000)}
            {detail.extracted_text.length > 2000 ? '…' : ''}
          </pre>
        </section>
      )}
    </div>
  )
}
