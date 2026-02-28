import { BrowserRouter, Routes, Route } from 'react-router-dom'
import RootLayout from './components/layout/RootLayout'
import DashboardPage from './pages/DashboardPage'
import TrainingPage from './pages/TrainingPage'
import AnalysisPage from './pages/AnalysisPage'
import AlertsPage from './pages/AlertsPage'
import ModelsPage from './pages/ModelsPage'
import SettingsPage from './pages/SettingsPage'

export default function App() {
  return (
    <BrowserRouter>
      <RootLayout>
        <Routes>
          <Route path="/" element={<DashboardPage />} />
          <Route path="/training" element={<TrainingPage />} />
          <Route path="/analysis" element={<AnalysisPage />} />
          <Route path="/alerts" element={<AlertsPage />} />
          <Route path="/models" element={<ModelsPage />} />
          <Route path="/settings" element={<SettingsPage />} />
        </Routes>
      </RootLayout>
    </BrowserRouter>
  )
}
