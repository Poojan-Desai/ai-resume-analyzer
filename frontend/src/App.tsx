import { BrowserRouter, Navigate, Route, Routes } from 'react-router-dom'
import { Layout } from './components/Layout'
import { ApplicationsPage } from './pages/Applications'
import { DashboardPage } from './pages/Dashboard'
import { JobsPage } from './pages/Jobs'
import { ResumesPage } from './pages/Resumes'

/**
 * Top-level routes. The API base URL is empty in dev so Vite can proxy /api to FastAPI.
 */
function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/" element={<Layout />}>
          <Route index element={<DashboardPage />} />
          <Route path="resumes" element={<ResumesPage />} />
          <Route path="jobs" element={<JobsPage />} />
          <Route path="applications" element={<ApplicationsPage />} />
          <Route path="*" element={<Navigate to="/" replace />} />
        </Route>
      </Routes>
    </BrowserRouter>
  )
}

export default App
