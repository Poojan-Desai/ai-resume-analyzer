import { useEffect, useState } from 'react'
import { api } from '../api/client'
import type { AIStatus } from '../types'

export type AIProvider = 'local' | 'openai'

type Props = {
  provider: AIProvider
  consent: boolean
  allowFallback: boolean
  disabled?: boolean
  onProviderChange: (provider: AIProvider) => void
  onConsentChange: (consent: boolean) => void
  onFallbackChange: (allow: boolean) => void
}

export function AIProviderControls({
  provider,
  consent,
  allowFallback,
  disabled = false,
  onProviderChange,
  onConsentChange,
  onFallbackChange,
}: Props) {
  const [status, setStatus] = useState<AIStatus | null>(null)

  useEffect(() => {
    api
      .get<AIStatus>('/api/ai/status')
      .then((response) => setStatus(response.data))
      .catch(() => setStatus(null))
  }, [])

  return (
    <div className="mt-4 rounded-lg border border-slate-700 bg-slate-950/60 p-4">
      <label className="text-xs font-semibold uppercase tracking-wide text-slate-400">
        Result provider
      </label>
      <select
        className="mt-2 w-full rounded-lg border border-slate-700 bg-slate-950 px-3 py-2 text-sm text-white"
        value={provider}
        disabled={disabled}
        onChange={(event) => {
          const next = event.target.value as AIProvider
          onProviderChange(next)
          onConsentChange(false)
        }}
      >
        <option value="local">Local deterministic demo (free)</option>
        <option value="openai" disabled={!status?.enabled}>
          OpenAI Responses API
        </option>
      </select>
      <p className="mt-2 text-xs leading-5 text-slate-500">
        {status?.enabled
          ? `${status.model} · ${status.requests_this_month}/${status.monthly_request_limit} requests · ${status.monthly_reserved_or_spent_cents}¢/${status.monthly_budget_cents}¢ reserved or spent this month.`
          : 'OpenAI is disabled until backend/.env contains a key and a positive monthly budget. The local demo remains available.'}
      </p>
      {provider === 'openai' && (
        <div className="mt-3 space-y-3 text-xs leading-5">
          <label className="flex items-start gap-2 rounded-md border border-amber-400/20 bg-amber-400/5 p-3 text-amber-100">
            <input
              className="mt-1"
              type="checkbox"
              checked={consent}
              disabled={disabled}
              onChange={(event) => onConsentChange(event.target.checked)}
            />
            <span>
              I choose to send the selected resume text and, when applicable,
              job-description text to OpenAI for this request. The API key stays
              on the backend. Responses use store=false; OpenAI&apos;s current data
              controls, including abuse-monitoring retention, still apply.
            </span>
          </label>
          <label className="flex items-start gap-2 text-slate-400">
            <input
              className="mt-1"
              type="checkbox"
              checked={allowFallback}
              disabled={disabled}
              onChange={(event) => onFallbackChange(event.target.checked)}
            />
            <span>
              If OpenAI is unavailable or a local cap blocks the call, return a
              clearly labeled local fallback instead of failing.
            </span>
          </label>
        </div>
      )}
    </div>
  )
}
