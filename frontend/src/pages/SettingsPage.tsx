import { useAuth } from '../context/AuthContext';
import { Settings, User, Shield, Bell } from 'lucide-react';

export default function SettingsPage() {
  const { user, roles, tenantId } = useAuth();

  return (
    <div className="max-w-2xl space-y-8">
      <div>
        <h1 className="text-2xl font-bold text-gray-900 flex items-center gap-2">
          <Settings className="h-6 w-6 text-gray-400" /> Settings
        </h1>
        <p className="text-gray-500 mt-1">Manage your account and application settings</p>
      </div>

      {/* Profile Section */}
      <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-6 space-y-4">
        <h2 className="text-lg font-semibold text-gray-900 flex items-center gap-2">
          <User className="h-5 w-5 text-indigo-500" /> Profile
        </h2>
        <dl className="grid grid-cols-2 gap-4 text-sm">
          <div>
            <dt className="text-gray-500">Username</dt>
            <dd className="font-medium text-gray-900">{user?.username}</dd>
          </div>
          <div>
            <dt className="text-gray-500">Email</dt>
            <dd className="font-medium text-gray-900">{user?.email}</dd>
          </div>
          <div>
            <dt className="text-gray-500">Name</dt>
            <dd className="font-medium text-gray-900">
              {[user?.first_name, user?.last_name].filter(Boolean).join(' ') || '—'}
            </dd>
          </div>
          <div>
            <dt className="text-gray-500">Tenant ID</dt>
            <dd className="font-medium text-gray-900 text-xs font-mono">{tenantId ?? '—'}</dd>
          </div>
        </dl>
      </div>

      {/* Roles Section */}
      <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-6 space-y-4">
        <h2 className="text-lg font-semibold text-gray-900 flex items-center gap-2">
          <Shield className="h-5 w-5 text-indigo-500" /> Roles & Permissions
        </h2>
        <div className="flex flex-wrap gap-2">
          {roles.map((role) => (
            <span key={role} className="inline-flex px-3 py-1 rounded-full text-xs font-medium bg-indigo-50 text-indigo-700">
              {role}
            </span>
          ))}
        </div>
        <p className="text-xs text-gray-400">
          Your access level determines what modules and actions are available.
        </p>
      </div>

      {/* Notifications placeholder */}
      <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-6 space-y-4">
        <h2 className="text-lg font-semibold text-gray-900 flex items-center gap-2">
          <Bell className="h-5 w-5 text-indigo-500" /> Notifications
        </h2>
        <p className="text-sm text-gray-500">Notification preferences are not yet configurable in this version.</p>
      </div>
    </div>
  );
}
