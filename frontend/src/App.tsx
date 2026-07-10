import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { AuthProvider, useAuth } from './context/AuthContext';
import { DashboardLayout } from './layouts/DashboardLayout';
import LoginPage from './pages/LoginPage';
import DashboardPage from './pages/DashboardPage';
import { SupplierListPage } from './pages/suppliers/SupplierListPage';
import SupplierDetailPage from './pages/suppliers/SupplierDetailPage';
import ContractListPage from './pages/contracts/ContractListPage';
import ContractDetailPage from './pages/contracts/ContractDetailPage';
import InvoiceDetailPage from './pages/invoices/InvoiceDetailPage';
import PRListPage from './pages/procurement/PRListPage';
import POListPage from './pages/procurement/POListPage';
import CreatePOPage from './pages/procurement/CreatePOPage';
import InvoiceListPage from './pages/invoices/InvoiceListPage';
import WorkflowInboxPage from './pages/workflows/WorkflowInboxPage';
import ReceivingPage from './pages/receiving/ReceivingPage';
import AIPage from './pages/ai/AIPage';
import AnalyticsDashboard from './pages/analytics/AnalyticsDashboard';
import SpendAnalytics from './pages/analytics/SpendAnalytics';
import SupplierAnalytics from './pages/analytics/SupplierAnalytics';
import { IntegrationListPage } from './pages/integrations/IntegrationListPage';
import { IntegrationDetailPage } from './pages/integrations/IntegrationDetailPage';
import SettingsPage from './pages/SettingsPage';
import ProfilePage from './pages/ProfilePage';
import { ToastProvider } from './components/Toast';

const queryClient = new QueryClient({
  defaultOptions: {
    queries: { retry: 1, staleTime: 30_000 },
  },
});

function ProtectedRoute({ children }: { children: React.ReactNode }) {
  const { isAuthenticated, loading } = useAuth();
  if (loading) return <div className="p-8 text-gray-500">Loading…</div>;
  if (!isAuthenticated) return <Navigate to="/login" replace />;
  return <DashboardLayout>{children}</DashboardLayout>;
}

function AppRoutes() {
  return (
    <Routes>
      <Route path="/login" element={<LoginPage />} />
      <Route path="/dashboard" element={<ProtectedRoute><DashboardPage /></ProtectedRoute>} />
      <Route path="/suppliers" element={<ProtectedRoute><SupplierListPage /></ProtectedRoute>} />
      <Route path="/suppliers/:id" element={<ProtectedRoute><SupplierDetailPage /></ProtectedRoute>} />
      <Route path="/contracts" element={<ProtectedRoute><ContractListPage /></ProtectedRoute>} />
      <Route path="/contracts/:id" element={<ProtectedRoute><ContractDetailPage /></ProtectedRoute>} />
      <Route path="/invoices/:id" element={<ProtectedRoute><InvoiceDetailPage /></ProtectedRoute>} />
      <Route path="/procurement/prs" element={<ProtectedRoute><PRListPage /></ProtectedRoute>} />
      <Route path="/procurement/pos" element={<ProtectedRoute><POListPage /></ProtectedRoute>} />
      <Route path="/procurement/create-po" element={<ProtectedRoute><CreatePOPage /></ProtectedRoute>} />
      <Route path="/receiving" element={<ProtectedRoute><ReceivingPage /></ProtectedRoute>} />
      <Route path="/invoices" element={<ProtectedRoute><InvoiceListPage /></ProtectedRoute>} />
      <Route path="/workflows" element={<ProtectedRoute><WorkflowInboxPage /></ProtectedRoute>} />
      <Route path="/ai" element={<ProtectedRoute><AIPage /></ProtectedRoute>} />

      {/* Analytics routes */}
      <Route path="/analytics" element={<ProtectedRoute><AnalyticsDashboard /></ProtectedRoute>} />
      <Route path="/analytics/spend" element={<ProtectedRoute><SpendAnalytics /></ProtectedRoute>} />
      <Route path="/analytics/suppliers" element={<ProtectedRoute><SupplierAnalytics /></ProtectedRoute>} />

      {/* Integration routes */}
      <Route path="/integrations" element={<ProtectedRoute><IntegrationListPage /></ProtectedRoute>} />
      <Route path="/integrations/connections/:id" element={<ProtectedRoute><IntegrationDetailPage /></ProtectedRoute>} />

      {/* User routes */}
      <Route path="/settings" element={<ProtectedRoute><SettingsPage /></ProtectedRoute>} />
      <Route path="/profile" element={<ProtectedRoute><ProfilePage /></ProtectedRoute>} />

      <Route path="/" element={<Navigate to="/dashboard" replace />} />
      <Route path="*" element={<Navigate to="/dashboard" replace />} />
    </Routes>
  );
}

export default function App() {
  return (
    <QueryClientProvider client={queryClient}>
      <BrowserRouter>
        <AuthProvider>
          <ToastProvider>
            <AppRoutes />
          </ToastProvider>
        </AuthProvider>
      </BrowserRouter>
    </QueryClientProvider>
  );
}
