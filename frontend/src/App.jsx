import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom'
import { AuthProvider } from './context/AuthContext'
import { ToastProvider } from './context/ToastContext'
import ProtectedRoute from './components/ProtectedRoute'
import Layout from './components/Layout'

import LoginPage    from './pages/LoginPage'
import RegisterPage from './pages/RegisterPage'
import SearchPage   from './pages/SearchPage'
import ResultsPage  from './pages/ResultsPage'
import HistoryPage  from './pages/HistoryPage'
import ItemPage     from './pages/ItemPage'

export default function App() {
  return (
    <BrowserRouter>
      <AuthProvider>
        <ToastProvider>
          <Routes>
            {/* Public */}
            <Route path="/login"    element={<LoginPage />} />
            <Route path="/register" element={<RegisterPage />} />

            {/* Protected — wrapped in Layout */}
            <Route element={<ProtectedRoute><Layout /></ProtectedRoute>}>
              <Route index element={<Navigate to="/search" replace />} />
              <Route path="/search"        element={<SearchPage />} />
              <Route path="/results/:id"   element={<ResultsPage />} />
              <Route path="/history"       element={<HistoryPage />} />
              <Route path="/item/:id"      element={<ItemPage />} />
            </Route>

            {/* Fallback */}
            <Route path="*" element={<Navigate to="/search" replace />} />
          </Routes>
        </ToastProvider>
      </AuthProvider>
    </BrowserRouter>
  )
}
