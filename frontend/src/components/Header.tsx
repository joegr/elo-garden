import { Sprout, LayoutGrid, BarChart3 } from 'lucide-react'

export function Header({
  activeTab,
  setActiveTab
}: {
  activeTab: 'builder' | 'dashboard'
  setActiveTab: (tab: 'builder' | 'dashboard') => void
}) {
  return (
    <header className="bg-slate-900/80 backdrop-blur border-b border-purple-500/20 sticky top-0 z-50">
      <div className="container mx-auto px-4 py-4">
        <div className="flex items-center justify-between">
          {/* Logo */}
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-lg bg-gradient-to-br from-purple-500 to-pink-500 flex items-center justify-center">
              <Sprout className="w-6 h-6 text-white" />
            </div>
            <div>
              <h1 className="text-xl font-bold text-white">Garden</h1>
              <p className="text-xs text-purple-300">Model Arena Platform</p>
            </div>
          </div>

          {/* Navigation */}
          <nav className="flex gap-2">
            <button
              onClick={() => setActiveTab('builder')}
              className={`
                px-4 py-2 rounded-lg font-semibold flex items-center gap-2 transition-all
                ${activeTab === 'builder'
                  ? 'bg-purple-500 text-white'
                  : 'text-slate-400 hover:text-white hover:bg-slate-800'
                }
              `}
            >
              <LayoutGrid className="w-4 h-4" />
              Arena Builder
            </button>
            <button
              onClick={() => setActiveTab('dashboard')}
              className={`
                px-4 py-2 rounded-lg font-semibold flex items-center gap-2 transition-all
                ${activeTab === 'dashboard'
                  ? 'bg-purple-500 text-white'
                  : 'text-slate-400 hover:text-white hover:bg-slate-800'
                }
              `}
            >
              <BarChart3 className="w-4 h-4" />
              Dashboard
            </button>
          </nav>

          {/* MLflow Link */}
          <a
            href="http://localhost:5000"
            target="_blank"
            rel="noopener noreferrer"
            className="px-4 py-2 bg-gradient-to-r from-blue-500 to-blue-600 text-white rounded-lg font-semibold hover:shadow-lg hover:shadow-blue-500/50 transition-all"
          >
            Open MLflow UI →
          </a>
        </div>
      </div>
    </header>
  )
}
