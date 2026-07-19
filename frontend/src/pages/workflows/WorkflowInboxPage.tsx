import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { apiGet, apiPost } from '../../api/client';
import type { ApprovalTask } from '../../api/types';
import { CheckCircle, XCircle, UserPlus } from 'lucide-react';
import { useState } from 'react';
import { useAuth } from '../../context/AuthContext';
import { useToast } from '../../components/Toast';

export default function WorkflowInboxPage() {
  const queryClient = useQueryClient();
  const { user } = useAuth();
  const { toast } = useToast();
  const [action, setAction] = useState<{ taskId: string; decision: string } | null>(null);

  const userId = user?.id;

  const { data: tasks, isLoading } = useQuery({
    queryKey: ['pending-tasks', userId],
    queryFn: () => apiGet<ApprovalTask[]>(`/api/v1/workflows/tasks/pending?user_id=${userId}`),
    enabled: !!userId,
  });

  const decideMutation = useMutation({
    mutationFn: ({ taskId, decision }: { taskId: string; decision: 'approve' | 'reject' }) =>
      apiPost(`/api/v1/workflows/tasks/${taskId}/decide`, { decision }),
    onSuccess: (_data, vars) => {
      queryClient.invalidateQueries({ queryKey: ['pending-tasks'] });
      setAction(null);
      toast('success', vars.decision === 'approve' ? 'Task approved' : 'Task rejected');
    },
    onError: (err: Error) => toast('error', err.message || 'Decision failed'),
  });

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-gray-900">My Tasks</h1>
        <p className="text-gray-500 mt-1">{tasks?.length ?? 0} pending approvals</p>
      </div>

      {isLoading && (
        <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-8 text-center text-sm text-gray-500">
          Loading tasks…
        </div>
      )}

      {!isLoading && tasks?.length === 0 && (
        <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-12 text-center">
          <CheckCircle className="h-12 w-12 text-green-400 mx-auto mb-3" />
          <h3 className="text-lg font-medium text-gray-900">All caught up!</h3>
          <p className="text-gray-500 mt-1">No pending tasks requiring your attention.</p>
        </div>
      )}

      <div className="space-y-3">
        {tasks?.map((task) => (
          <div key={task.id} className="bg-white rounded-xl shadow-sm border border-gray-200 p-5">
            <div className="flex items-start justify-between">
              <div>
                <h3 className="font-medium text-gray-900">Approval Task</h3>
                <p className="text-sm text-gray-500 mt-1">ID: {task.id.slice(0, 8)}…</p>
                <p className="text-sm text-gray-400 mt-0.5">Status: {task.status ?? 'pending'}</p>
              </div>
              <span className="inline-flex items-center gap-1 bg-blue-100 text-blue-700 px-3 py-1 rounded-full text-xs font-medium">
                <UserPlus className="h-3 w-3" /> Action Required
              </span>
            </div>

            {action?.taskId === task.id ? (
              <div className="flex gap-3 mt-4 pt-4 border-t border-gray-100">
                <button
                  onClick={() => decideMutation.mutate({ taskId: task.id, decision: 'approve' })}
                  disabled={decideMutation.isPending}
                  className="flex items-center gap-2 bg-green-600 text-white px-4 py-2 rounded-lg text-sm font-medium hover:bg-green-700 disabled:opacity-50"
                >
                  <CheckCircle className="h-4 w-4" /> Approve
                </button>
                <button
                  onClick={() => decideMutation.mutate({ taskId: task.id, decision: 'reject' })}
                  disabled={decideMutation.isPending}
                  className="flex items-center gap-2 bg-red-600 text-white px-4 py-2 rounded-lg text-sm font-medium hover:bg-red-700 disabled:opacity-50"
                >
                  <XCircle className="h-4 w-4" /> Reject
                </button>
                <button
                  onClick={() => setAction(null)}
                  className="px-4 py-2 text-sm text-gray-600 hover:bg-gray-100 rounded-lg"
                >
                  Cancel
                </button>
              </div>
            ) : (
              <div className="mt-4 pt-4 border-t border-gray-100">
                <button
                  onClick={() => setAction({ taskId: task.id, decision: '' })}
                  className="bg-indigo-600 text-white px-4 py-2 rounded-lg text-sm font-medium hover:bg-indigo-700"
                >
                  Review
                </button>
              </div>
            )}
          </div>
        ))}
      </div>
    </div>
  );
}
