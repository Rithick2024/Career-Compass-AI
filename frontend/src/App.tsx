import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import { Suspense, lazy } from 'react';
import { AuthProvider } from '@/features/auth/context/AuthContext';
import { ProtectedRoute } from '@/features/auth/components/ProtectedRoute';
import LoginPage from '@/features/auth/pages/LoginPage';
import RegisterPage from '@/features/auth/pages/RegisterPage';
import { Toaster } from 'react-hot-toast';

// Lazy loaded routes
const StudentDashboard = lazy(() => import('@/features/student/pages/StudentDashboard'));
const StudentProfile = lazy(() => import('@/features/student/pages/StudentProfile'));
const StudentSkills = lazy(() => import('@/features/student/pages/StudentSkills'));
const StudentResume = lazy(() => import('@/features/student/pages/StudentResume'));
const StaffDashboard = lazy(() => import('@/features/staff/pages/StaffDashboard'));
const StaffDepartmentsPage = lazy(() => import('@/features/staff/pages/StaffDepartmentsPage'));
const StaffSkillsPage = lazy(() => import('@/features/staff/pages/StaffSkillsPage'));
const StaffCompaniesPage = lazy(() => import('@/features/staff/pages/StaffCompaniesPage'));
const StaffStudentsPage = lazy(() => import('@/features/staff/pages/StaffStudentsPage'));

// Loading fallback
const PageLoader = () => (
  <div className="flex min-h-screen items-center justify-center">
    <div className="h-8 w-8 animate-spin rounded-full border-b-2 border-primary"></div>
  </div>
);

function AppRoutes() {
  return (
    <Suspense fallback={<PageLoader />}>
      <Routes>
        <Route path="/" element={<Navigate to="/login" replace />} />
        <Route path="/login" element={<LoginPage />} />
        <Route path="/register" element={<RegisterPage />} />

        {/* Student module */}
        <Route path="/student/dashboard" element={<ProtectedRoute allowedRoles={['student']}><StudentDashboard /></ProtectedRoute>} />
        <Route path="/student/profile" element={<ProtectedRoute allowedRoles={['student']}><StudentProfile /></ProtectedRoute>} />
        <Route path="/student/skills" element={<ProtectedRoute allowedRoles={['student']}><StudentSkills /></ProtectedRoute>} />
        <Route path="/student/resume" element={<ProtectedRoute allowedRoles={['student']}><StudentResume /></ProtectedRoute>} />

        {/* Placeholder routes for remaining student pages */}
        {['jobs', 'applications', 'readiness'].map((p) => (
          <Route
            key={p}
            path={`/student/${p}`}
            element={<ProtectedRoute allowedRoles={['student']}><StudentDashboard /></ProtectedRoute>}
          />
        ))}

        {/* Staff module */}
        <Route path="/staff/dashboard" element={<ProtectedRoute allowedRoles={['staff']}><StaffDashboard /></ProtectedRoute>} />
        <Route path="/staff/students" element={<ProtectedRoute allowedRoles={['staff']}><StaffStudentsPage /></ProtectedRoute>} />
        <Route path="/staff/departments" element={<ProtectedRoute allowedRoles={['staff']}><StaffDepartmentsPage /></ProtectedRoute>} />
        <Route path="/staff/skills" element={<ProtectedRoute allowedRoles={['staff']}><StaffSkillsPage /></ProtectedRoute>} />
        <Route path="/staff/companies" element={<ProtectedRoute allowedRoles={['staff']}><StaffCompaniesPage /></ProtectedRoute>} />

        {/* Placeholder routes for remaining staff pages */}
        {['jobs', 'applications', 'placements'].map((p) => (
          <Route
            key={p}
            path={`/staff/${p}`}
            element={<ProtectedRoute allowedRoles={['staff']}><StaffDashboard /></ProtectedRoute>}
          />
        ))}

        <Route path="*" element={<Navigate to="/login" replace />} />
      </Routes>
    </Suspense>
  );
}

function App() {
  return (
    <BrowserRouter>
      <AuthProvider>
        <AppRoutes />
        <Toaster position="top-right" />
      </AuthProvider>
    </BrowserRouter>
  );
}


export default App;
