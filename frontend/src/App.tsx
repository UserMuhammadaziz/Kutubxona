import { useEffect } from 'react'
import { Navigate, Route, Routes } from 'react-router-dom'
import { useAuthStore } from './store/auth'
import { Layout } from './components/Layout'
import { RequireAdmin, RequireAuth } from './components/RequireAuth'
import { Login } from './pages/Login'
import { Dashboard } from './pages/Dashboard'
import { Books } from './pages/Books'
import { BookDetail } from './pages/BookDetail'
import { Copies } from './pages/Copies'
import { Readers } from './pages/Readers'
import { ReaderDetail } from './pages/ReaderDetail'
import { Applications } from './pages/Applications'
import { Loans } from './pages/Loans'
import { Bandlar } from './pages/Bandlar'
import { Reservations } from './pages/Reservations'
import { Fines } from './pages/Fines'
import { Staff } from './pages/Staff'

function App() {
  const hydrate = useAuthStore((s) => s.hydrate)

  useEffect(() => {
    hydrate()
  }, [hydrate])

  return (
    <Routes>
      <Route path="/login" element={<Login />} />

      <Route element={<RequireAuth />}>
        <Route element={<Layout />}>
          <Route path="/" element={<Dashboard />} />
          <Route path="/books" element={<Books />} />
          <Route path="/books/:id" element={<BookDetail />} />
          <Route path="/copies" element={<Copies />} />
          <Route path="/readers" element={<Readers />} />
          <Route path="/readers/:id" element={<ReaderDetail />} />
          <Route path="/teachers" element={<Readers rol="oqituvchi" />} />
          <Route path="/applications" element={<Applications />} />
          <Route path="/loans" element={<Loans />} />
          <Route path="/bandlar" element={<Bandlar />} />
          <Route path="/reservations" element={<Reservations />} />
          <Route path="/fines" element={<Fines />} />

          <Route element={<RequireAdmin />}>
            <Route path="/staff" element={<Staff />} />
          </Route>
        </Route>
      </Route>

      <Route path="*" element={<Navigate to="/" replace />} />
    </Routes>
  )
}

export default App
