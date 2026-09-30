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
const StudentJobsPage = lazy(() => import('@/features/student/pages/StudentJobsPage'));
const StaffDashboard = lazy(() => import('@/features/staff/pages/StaffDashboard'));
const StaffDepartmentsPage = lazy(() => import('@/features/staff/pages/StaffDepartmentsPage'));
const StaffSkillsPage = lazy(() => import('@/features/staff/pages/StaffSkillsPage'));
const StaffCompaniesPage = lazy(() => import('@/features/staff/pages/StaffCompaniesPage'));
const StaffStudentsPage = lazy(() => import('@/features/staff/pages/StaffStudentsPage'));
const StaffJobsPage = lazy(() => import('@/features/staff/pages/StaffJobsPage'));
const StudentApplicationsPage = lazy(() => import('@/features/student/pages/StudentApplicationsPage'));
const StaffApplicationsPage = lazy(() => import('@/features/staff/pages/StaffApplicationsPage'));
const StudentPlacementsPage = lazy(() => import('@/features/student/pages/StudentPlacementsPage'));
const StudentReadinessPage = lazy(() => import('@/features/student/pages/StudentReadinessPage'));
const StaffPlacementsPage = lazy(() => import('@/features/staff/pages/StaffPlacementsPage'));

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
        <Route path="/student/jobs" element={<ProtectedRoute allowedRoles={['student']}><StudentJobsPage /></ProtectedRoute>} />

        <Route path="/student/applications" element={<ProtectedRoute allowedRoles={['student']}><StudentApplicationsPage /></ProtectedRoute>} />
        <Route path="/student/placements" element={<ProtectedRoute allowedRoles={['student']}><StudentPlacementsPage /></ProtectedRoute>} />
        <Route path="/student/readiness" element={<ProtectedRoute allowedRoles={['student']}><StudentReadinessPage /></ProtectedRoute>} />

        {/* Staff module */}
        <Route path="/staff/dashboard" element={<ProtectedRoute allowedRoles={['staff']}><StaffDashboard /></ProtectedRoute>} />
        <Route path="/staff/students" element={<ProtectedRoute allowedRoles={['staff']}><StaffStudentsPage /></ProtectedRoute>} />
        <Route path="/staff/departments" element={<ProtectedRoute allowedRoles={['staff']}><StaffDepartmentsPage /></ProtectedRoute>} />
        <Route path="/staff/skills" element={<ProtectedRoute allowedRoles={['staff']}><StaffSkillsPage /></ProtectedRoute>} />
        <Route path="/staff/companies" element={<ProtectedRoute allowedRoles={['staff']}><StaffCompaniesPage /></ProtectedRoute>} />
        <Route path="/staff/jobs" element={<ProtectedRoute allowedRoles={['staff']}><StaffJobsPage /></ProtectedRoute>} />

        <Route path="/staff/applications" element={<ProtectedRoute allowedRoles={['staff']}><StaffApplicationsPage /></ProtectedRoute>} />
        <Route path="/staff/placements" element={<ProtectedRoute allowedRoles={['staff']}><StaffPlacementsPage /></ProtectedRoute>} />

        {/* Placeholder routes for remaining staff pages */}
        {/* Placeholder routes for remaining staff pages */}
        {['analytics'].map((p) => (
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
