import { NavLink, Outlet } from 'react-router-dom'

/**
 * Shell: top navigation + main content area.
 * Uses Tailwind for a dark, readable layout.
 */
export function Layout() {
  const linkClass = ({ isActive }: { isActive: boolean }) =>
    `rounded-lg px-3 py-2 text-sm font-medium transition-colors ${
      isActive
        ? 'bg-indigo-500/20 text-indigo-200'
        : 'text-slate-400 hover:bg-slate-800 hover:text-slate-100'
    }`

  return (
    <div className="min-h-screen flex flex-col">
      <header className="border-b border-slate-800 bg-slate-900/80 backdrop-blur">
        <div className="mx-auto flex max-w-6xl flex-wrap items-center justify-between gap-4 px-4 py-4">
          <div>
            <p className="text-xs uppercase tracking-widest text-indigo-400">
              Portfolio project
            </p>
            <h1 className="text-lg font-semibold text-white">
              AI Career Assistant
            </h1>
          </div>
          <nav className="flex flex-wrap gap-1">
            <NavLink to="/" className={linkClass} end>
              Dashboard
            </NavLink>
            <NavLink to="/resumes" className={linkClass}>
              Resumes
            </NavLink>
            <NavLink to="/jobs" className={linkClass}>
              Jobs &amp; AI
            </NavLink>
            <NavLink to="/applications" className={linkClass}>
              Applications
            </NavLink>
          </nav>
        </div>
      </header>

      <main className="mx-auto w-full max-w-6xl flex-1 px-4 py-8">
        <Outlet />
      </main>

      <footer className="border-t border-slate-800 py-6 text-center text-xs text-slate-500">
        Built with FastAPI · React · OpenAI — keep API keys on the server only.
      </footer>
    </div>
  )
}
