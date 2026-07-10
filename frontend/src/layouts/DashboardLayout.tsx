import { useNavigate, useLocation, Link } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import {
  LayoutDashboard, FileText, ShoppingCart,
  CheckCircle2, LogOut, Menu, X, PackageCheck,
  BarChart3, Plug, Settings,
  FileEdit, Send, Truck, CreditCard, Bot,
  Shield, FileSearch, FileSpreadsheet, BookOpen, ClipboardList,
  Users, Sliders, ShieldAlert, ChevronDown, User,
} from 'lucide-react';
import { useState, useRef, useEffect } from 'react';
import { cn } from '../lib/utils';

const navGroups = [
  {
    label: 'Main',
    items: [
      { path: '/dashboard', label: 'Dashboard', icon: LayoutDashboard },
    ],
  },
  {
    label: 'Source',
    items: [
      { path: '/suppliers', label: 'Suppliers', icon: Truck },
      { path: '/contracts', label: 'Contracts', icon: FileText },
      { path: '/sourcing', label: 'Sourcing Events', icon: ClipboardList },
      { path: '/rfx', label: 'RFx', icon: FileSearch },
      { path: '/supplier-risk', label: 'Supplier Risk', icon: Shield },
    ],
  },
  {
    label: 'Procure',
    items: [
      { path: '/procurement/prs', label: 'Requisitions', icon: FileEdit },
      { path: '/procurement/pos', label: 'Purchase Orders', icon: Send },
      { path: '/receiving', label: 'Receiving', icon: PackageCheck },
    ],
  },
  {
    label: 'Pay',
    items: [
      { path: '/invoices', label: 'Invoices', icon: CreditCard },
    ],
  },
  {
    label: 'Oversight',
    items: [
      { path: '/workflows', label: 'Approvals', icon: CheckCircle2 },
      { path: '/analytics', label: 'Analytics', icon: BarChart3 },
    ],
  },
  {
    label: 'Tools',
    items: [
      { path: '/documents', label: 'Documents', icon: BookOpen },
      { path: '/reports', label: 'Reports', icon: FileSpreadsheet },
      { path: '/integrations', label: 'Integrations', icon: Plug },
      { path: '/ai', label: 'AI Copilot', icon: Bot },
    ],
  },
  {
    label: 'Admin',
    items: [
      { path: '/admin/users', label: 'Users', icon: Users },
      { path: '/admin/roles', label: 'Roles', icon: Sliders },
      { path: '/admin/settings', label: 'Settings', icon: Settings },
      { path: '/admin/audit', label: 'Audit Logs', icon: ShieldAlert },
    ],
  },
];

export function DashboardLayout({ children }: { children: React.ReactNode }) {
  const { user, roles, logout } = useAuth();
  const navigate = useNavigate();
  const location = useLocation();
  const [sidebarOpen, setSidebarOpen] = useState(false);
  const [userMenuOpen, setUserMenuOpen] = useState(false);
  const userMenuRef = useRef<HTMLDivElement>(null);

  // Close user menu on outside click
  useEffect(() => {
    const handleClick = (e: MouseEvent) => {
      if (userMenuRef.current && !userMenuRef.current.contains(e.target as Node)) {
        setUserMenuOpen(false);
      }
    };
    document.addEventListener('mousedown', handleClick);
    return () => document.removeEventListener('mousedown', handleClick);
  }, []);

  const handleLogout = () => {
    logout();
    navigate('/login');
  };

  // Breadcrumb generation
  const pathParts = location.pathname.split('/').filter(Boolean);
  const breadcrumbs = pathParts.map((part, index) => {
    const path = '/' + pathParts.slice(0, index + 1).join('/');
    const label = part.replace(/-/g, ' ').replace(/\b\w/g, (c) => c.toUpperCase());
    return { path, label };
  });

  const isActive = (path: string) => {
    if (path === '/dashboard') return location.pathname === '/dashboard';
    return location.pathname.startsWith(path);
  };

  return (
    <div className="min-h-screen bg-gray-50 flex">
      {/* Mobile backdrop */}
      {sidebarOpen && (
        <div
          className="fixed inset-0 bg-black/30 z-20 lg:hidden"
          onClick={() => setSidebarOpen(false)}
        />
      )}

      {/* Sidebar */}
      <aside
        className={cn(
          'fixed inset-y-0 left-0 z-30 w-64 bg-white border-r border-gray-200 flex flex-col transform transition-transform duration-200 lg:translate-x-0 lg:static lg:z-auto',
          sidebarOpen ? 'translate-x-0' : '-translate-x-full',
        )}
      >
        {/* Logo / Branding */}
        <div className="flex items-center justify-between h-16 px-6 border-b border-gray-200 shrink-0">
          <Link to="/dashboard" className="flex items-center gap-3 group">
            <div className="h-9 w-9 rounded-lg bg-indigo-600 flex items-center justify-center group-hover:bg-indigo-700 transition-colors">
              <ShoppingCart className="h-5 w-5 text-white" />
            </div>
            <div className="flex flex-col">
              <span className="text-lg font-bold text-gray-900 leading-tight">OpenS2P</span>
              <span className="text-[10px] text-gray-400 font-medium leading-tight">Source-to-Pay Platform</span>
            </div>
          </Link>
          <div className="flex items-center gap-2">
            <span className="inline-flex items-center px-1.5 py-0.5 rounded text-[10px] font-bold bg-amber-100 text-amber-700 uppercase tracking-wider">DEV</span>
            <button className="lg:hidden" onClick={() => setSidebarOpen(false)}>
              <X className="h-5 w-5 text-gray-400" />
            </button>
          </div>
        </div>

        {/* Navigation */}
        <nav className="flex-1 overflow-y-auto px-3 py-4 space-y-6">
          {navGroups.map((group) => (
            <div key={group.label}>
              <p className="px-3 text-xs font-semibold text-gray-400 uppercase tracking-wider mb-1">
                {group.label}
              </p>
              <div className="space-y-0.5">
                {group.items.map((item) => {
                  const active = isActive(item.path);
                  return (
                    <button
                      key={item.path}
                      onClick={() => { navigate(item.path); setSidebarOpen(false); }}
                      className={cn(
                        'flex items-center gap-3 w-full px-3 py-2 rounded-lg text-sm font-medium transition-colors',
                        active
                          ? 'bg-indigo-50 text-indigo-700'
                          : 'text-gray-600 hover:bg-gray-100',
                      )}
                    >
                      <item.icon className={cn('h-4 w-4', active ? 'text-indigo-600' : 'text-gray-400')} />
                      {item.label}
                    </button>
                  );
                })}
              </div>
            </div>
          ))}
        </nav>

        {/* User footer */}
        <div className="shrink-0 p-4 border-t border-gray-200">
          <div className="flex items-center justify-between">
            <div className="text-sm min-w-0 flex-1">
              <p className="font-medium text-gray-700 truncate">{user?.username}</p>
              <p className="text-gray-400 text-xs truncate">{roles.join(', ')}</p>
            </div>
            <button
              onClick={handleLogout}
              className="p-2 text-gray-400 hover:text-red-500 rounded-lg hover:bg-gray-100 shrink-0 ml-2"
              title="Sign out"
            >
              <LogOut className="h-4 w-4" />
            </button>
          </div>
        </div>
      </aside>

      {/* Main content */}
      <div className="flex-1 flex flex-col min-w-0">
        {/* Header */}
        <header className="h-16 bg-white border-b border-gray-200 flex items-center px-4 lg:px-6 gap-4">
          <button className="lg:hidden shrink-0" onClick={() => setSidebarOpen(true)}>
            <Menu className="h-5 w-5 text-gray-500" />
          </button>

          {/* Breadcrumbs */}
          <nav className="hidden sm:flex items-center gap-1.5 text-sm text-gray-500 min-w-0">
            <Link to="/dashboard" className="hover:text-gray-700 shrink-0">Home</Link>
            {breadcrumbs.map((crumb, i) => (
              <span key={crumb.path} className="flex items-center gap-1.5 min-w-0">
                <span className="text-gray-300">/</span>
                {i === breadcrumbs.length - 1 ? (
                  <span className="text-gray-900 font-medium truncate">{crumb.label}</span>
                ) : (
                  <Link to={crumb.path} className="hover:text-gray-700 truncate">{crumb.label}</Link>
                )}
              </span>
            ))}
          </nav>

          <div className="flex-1" />

          {/* User menu */}
          <div className="relative" ref={userMenuRef}>
            <button
              onClick={() => setUserMenuOpen(!userMenuOpen)}
              className="flex items-center gap-2 px-3 py-1.5 rounded-lg hover:bg-gray-100 transition-colors"
            >
              <div className="h-8 w-8 rounded-full bg-indigo-100 flex items-center justify-center text-sm font-medium text-indigo-700">
                {user?.username?.charAt(0).toUpperCase()}
              </div>
              <div className="hidden md:block text-left">
                <p className="text-sm font-medium text-gray-700 leading-tight">{user?.username}</p>
                <p className="text-xs text-gray-400 leading-tight">{user?.email}</p>
              </div>
              <ChevronDown className="h-4 w-4 text-gray-400 hidden md:block" />
            </button>

            {userMenuOpen && (
              <div className="absolute right-0 mt-2 w-56 bg-white rounded-xl shadow-lg border border-gray-200 py-1 z-50">
                <div className="px-4 py-2 border-b border-gray-100">
                  <p className="text-sm font-medium text-gray-900">{user?.username}</p>
                  <p className="text-xs text-gray-500">{user?.email}</p>
                </div>
                <button
                  onClick={() => { navigate('/profile'); setUserMenuOpen(false); }}
                  className="flex items-center gap-2 w-full px-4 py-2 text-sm text-gray-700 hover:bg-gray-50"
                >
                  <User className="h-4 w-4 text-gray-400" /> Profile
                </button>
                <button
                  onClick={() => { navigate('/settings'); setUserMenuOpen(false); }}
                  className="flex items-center gap-2 w-full px-4 py-2 text-sm text-gray-700 hover:bg-gray-50"
                >
                  <Settings className="h-4 w-4 text-gray-400" /> Settings
                </button>
                <div className="border-t border-gray-100 mt-1 pt-1">
                  <button
                    onClick={handleLogout}
                    className="flex items-center gap-2 w-full px-4 py-2 text-sm text-red-600 hover:bg-red-50"
                  >
                    <LogOut className="h-4 w-4" /> Sign out
                  </button>
                </div>
              </div>
            )}
          </div>
        </header>

        {/* Page content */}
        <main className="flex-1 p-4 lg:p-8 overflow-auto">
          {children}
        </main>
      </div>
    </div>
  );
}
