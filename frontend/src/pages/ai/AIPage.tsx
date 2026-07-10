import { useState } from 'react';
import { apiPost } from '../../api/client';
import { Bot, Send, Loader2, Shield, TrendingUp, FileText, AlertTriangle } from 'lucide-react';

interface ChatMessage {
  role: 'user' | 'assistant';
  content: string;
}

const SUGGESTIONS = [
  { icon: Shield, text: 'Which suppliers have the highest risk score?', color: 'text-rose-500' },
  { icon: FileText, text: 'What contracts are expiring this quarter?', color: 'text-amber-500' },
  { icon: TrendingUp, text: 'Show me spend by category', color: 'text-emerald-500' },
  { icon: AlertTriangle, text: 'Are there any invoice exceptions?', color: 'text-red-500' },
];

export default function AIPage() {
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [input, setInput] = useState('');
  const [loading, setLoading] = useState(false);

  const sendMessage = async () => {
    if (!input.trim() || loading) return;
    const userMsg: ChatMessage = { role: 'user', content: input };
    setMessages(prev => [...prev, userMsg]);
    setInput('');
    setLoading(true);
    try {
      const data = await apiPost<{ response: string; sources: string[] }>('/api/v1/copilot/chat', { message: input });
      setMessages(prev => [...prev, { role: 'assistant', content: data.response }]);
    } catch {
      setMessages(prev => [...prev, { role: 'assistant', content: 'Sorry, I encountered an error processing your request. The AI service may not be available yet.' }]);
    } finally {
      setLoading(false);
    }
  };

  const handleSuggestion = (text: string) => {
    setInput(text);
  };

  return (
    <div className="max-w-4xl mx-auto">
      <div className="flex items-center gap-3 mb-6">
        <div className="p-2.5 bg-gradient-to-br from-indigo-500 to-purple-600 rounded-xl">
          <Bot className="w-6 h-6 text-white" />
        </div>
        <div>
          <h1 className="text-2xl font-bold text-gray-900">AI Procurement Copilot</h1>
          <p className="text-sm text-gray-500">Natural-language assistant for your Source-to-Pay operations</p>
        </div>
      </div>

      {messages.length === 0 ? (
        /* ── Placeholder / Welcome state ── */
        <div className="bg-white rounded-xl shadow-sm border border-gray-200">
          <div className="p-10 text-center">
            <div className="w-16 h-16 mx-auto mb-4 bg-gradient-to-br from-indigo-100 to-purple-100 rounded-2xl flex items-center justify-center">
              <Bot className="w-8 h-8 text-indigo-600" />
            </div>
            <h2 className="text-xl font-semibold text-gray-900 mb-2">OpenS2P Assistant</h2>
            <p className="text-gray-500 text-sm max-w-md mx-auto mb-8">
              Ask questions about your procurement data — suppliers, contracts, spend, approvals, and more.
            </p>

            <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 max-w-xl mx-auto">
              {SUGGESTIONS.map((s) => (
                <button
                  key={s.text}
                  onClick={() => handleSuggestion(s.text)}
                  className="flex items-center gap-3 p-3 rounded-lg border border-gray-200 hover:border-indigo-200 hover:bg-indigo-50/50 transition text-left group"
                >
                  <s.icon className={`w-5 h-5 ${s.color} shrink-0`} />
                  <span className="text-sm text-gray-600 group-hover:text-gray-900">{s.text}</span>
                </button>
              ))}
            </div>

          </div>

          {/* Feature preview */}
          <div className="border-t border-gray-100 px-10 py-6">
            <p className="text-xs font-semibold text-gray-400 uppercase tracking-wider mb-3">Coming in v0.8</p>
            <div className="grid grid-cols-2 sm:grid-cols-4 gap-4">
              {[
                { icon: Shield, label: 'Supplier Risk', desc: 'Assess vendor risk profiles' },
                { icon: FileText, label: 'Contract Q&A', desc: 'Ask about obligations & clauses' },
                { icon: TrendingUp, label: 'Spend Insights', desc: 'Find saving opportunities' },
                { icon: AlertTriangle, label: 'Bottleneck Alerts', desc: 'Identify approval delays' },
              ].map((feat) => (
                <div key={feat.label} className="text-center">
                  <div className="w-10 h-10 mx-auto mb-2 bg-gray-50 rounded-lg flex items-center justify-center">
                    <feat.icon className="w-5 h-5 text-gray-400" />
                  </div>
                  <p className="text-xs font-medium text-gray-700">{feat.label}</p>
                  <p className="text-[10px] text-gray-400 mt-0.5">{feat.desc}</p>
                </div>
              ))}
            </div>
          </div>
        </div>
      ) : (
        /* ── Chat interface ── */
        <div className="bg-white rounded-xl shadow-sm border h-[600px] flex flex-col">
          <div className="flex-1 overflow-y-auto p-4 space-y-4">
            {messages.map((msg, i) => (
              <div key={i} className={`flex ${msg.role === 'user' ? 'justify-end' : 'justify-start'}`}>
                <div className={`max-w-[80%] rounded-lg p-3 ${msg.role === 'user' ? 'bg-indigo-600 text-white' : 'bg-gray-100 text-gray-800'}`}>
                  <p className="text-sm whitespace-pre-wrap">{msg.content}</p>
                </div>
              </div>
            ))}
            {loading && (
              <div className="flex justify-start">
                <div className="bg-gray-100 rounded-lg p-3 flex items-center gap-2">
                  <Loader2 className="w-4 h-4 animate-spin" />
                  <span className="text-sm text-gray-500">Thinking...</span>
                </div>
              </div>
            )}
          </div>
          <div className="border-t p-4">
            <div className="flex gap-2">
              <input
                type="text"
                value={input}
                onChange={e => setInput(e.target.value)}
                onKeyDown={e => e.key === 'Enter' && sendMessage()}
                placeholder="Ask about suppliers, contracts, spend..."
                className="flex-1 border rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-indigo-500"
              />
              <button onClick={sendMessage} disabled={loading || !input.trim()} className="bg-indigo-600 text-white rounded-lg px-4 py-2 hover:bg-indigo-700 disabled:opacity-50">
                <Send className="w-4 h-4" />
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
