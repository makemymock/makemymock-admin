import { Navigate, Route, Routes } from 'react-router-dom';
import Login from '../pages/login/Login';
import Dashboard from '../pages/dashboard/Dashboard';
import Users from '../pages/users/Users';
import UserDetail from '../pages/users/UserDetail';
import EmailComposer from '../pages/email/EmailComposer';
import Questions from '../pages/questions/Questions';
import Contests from '../pages/contests/Contests';
import ContestForm from '../pages/contests/ContestForm';
import Observability from '../pages/observability/Observability';
import ProtectedRoute from './ProtectedRoute';
import { tokenStorage } from '../utils/token';
import AdminShell from '../components/layout/AdminShell';

const RedirectIfAuthed = ({ children }) => {
  if (tokenStorage.isAuthenticated()) {
    return <Navigate to="/dashboard" replace />;
  }
  return children;
};

const AppRoutes = () => {
  return (
    <Routes>
      <Route
        path="/login"
        element={
          <RedirectIfAuthed>
            <Login />
          </RedirectIfAuthed>
        }
      />

      {/* Authenticated area — every page sits inside the admin shell. */}
      <Route
        element={
          <ProtectedRoute>
            <AdminShell />
          </ProtectedRoute>
        }
      >
        <Route path="/" element={<Navigate to="/dashboard" replace />} />
        <Route path="/dashboard" element={<Dashboard />} />
        <Route path="/users" element={<Users />} />
        <Route path="/users/:userId" element={<UserDetail />} />
        <Route path="/email" element={<EmailComposer />} />
        <Route path="/questions" element={<Questions />} />
        <Route path="/contests" element={<Contests />} />
        <Route path="/contests/new" element={<ContestForm />} />
        <Route path="/contests/:contestId" element={<ContestForm />} />
        <Route path="/observability" element={<Observability />} />
      </Route>

      <Route path="*" element={<Navigate to="/dashboard" replace />} />
    </Routes>
  );
};

export default AppRoutes;
