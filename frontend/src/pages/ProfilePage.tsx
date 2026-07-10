import { useAuth } from '../context/AuthContext';
import { User, Shield, Calendar, Mail } from 'lucide-react';

export default function ProfilePage() {
  const { user, roles } = useAuth();

  return (
    <div className="max-w-2xl space-y-8">
      <div>
        <h1 className="text-2xl font-bold text-gray-900">My Profile</h1>
        <p className="text-gray-500 mt-1">Your account information and activity</p>
      </div>

      {/* Profile card */}
      <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-6">
        <div className="flex items-center gap-4 mb-6">
          <div className="h-16 w-16 rounded-full bg-indigo-100 flex items-center justify-center text-2xl font-bold text-indigo-700">
            {user?.username?.charAt(0).toUpperCase() ?? '?'}
          </div>
          <div>
            <h2 className="text-xl font-bold text-gray-900">{user?.username}</h2>
            <p className="text-gray-500 text-sm">{user?.email}</p>
          </div>
        </div>

        <dl className="grid grid-cols-2 gap-4 text-sm">
          <div className="bg-gray-50 rounded-lg p-4">
            <dt className="text-gray-500 text-xs flex items-center gap-1 mb-1">
              <User className="h-3 w-3" /> Username
            </dt>
            <dd className="font-medium text-gray-900">{user?.username}</dd>
          </div>
          <div className="bg-gray-50 rounded-lg p-4">
            <dt className="text-gray-500 text-xs flex items-center gap-1 mb-1">
              <Mail className="h-3 w-3" /> Email
            </dt>
            <dd className="font-medium text-gray-900">{user?.email}</dd>
          </div>
          <div className="bg-gray-50 rounded-lg p-4">
            <dt className="text-gray-500 text-xs flex items-center gap-1 mb-1">
              <Shield className="h-3 w-3" /> Roles
            </dt>
            <dd className="font-medium text-gray-900 flex gap-1 flex-wrap mt-1">
              {roles.map((r) => (
                <span key={r} className="inline-flex px-2 py-0.5 rounded-full text-xs font-medium bg-indigo-50 text-indigo-700">
                  {r}
                </span>
              ))}
            </dd>
          </div>
          <div className="bg-gray-50 rounded-lg p-4">
            <dt className="text-gray-500 text-xs flex items-center gap-1 mb-1">
              <Calendar className="h-3 w-3" /> Superuser
            </dt>
            <dd className="font-medium text-gray-900">{user?.is_superuser ? 'Yes' : 'No'}</dd>
          </div>
        </dl>
      </div>
    </div>
  );
}
