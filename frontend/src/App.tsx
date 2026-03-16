import { useState } from 'react'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { DndProvider } from 'react-dnd'
import { HTML5Backend } from 'react-dnd-html5-backend'
import { ModelLibrary } from './components/ModelLibrary'
import { ArenaBuilder } from './components/ArenaBuilder'
import { ExperimentDashboard } from './components/ExperimentDashboard'
import { Header } from './components/Header'
import './App.css'

const queryClient = new QueryClient()

function App() {
  const [activeTab, setActiveTab] = useState<'builder' | 'dashboard'>('builder')

  return (
    <QueryClientProvider client={queryClient}>
      <DndProvider backend={HTML5Backend}>
        <div className="min-h-screen bg-gradient-to-br from-slate-900 via-purple-900 to-slate-900">
          <Header activeTab={activeTab} setActiveTab={setActiveTab} />
          
          <main className="container mx-auto px-4 py-8">
            {activeTab === 'builder' ? (
              <div className="grid grid-cols-12 gap-6">
                {/* Model Library - Left Sidebar */}
                <div className="col-span-3">
                  <ModelLibrary />
                </div>

                {/* Arena Builder - Main Area */}
                <div className="col-span-9">
                  <ArenaBuilder />
                </div>
              </div>
            ) : (
              <ExperimentDashboard />
            )}
          </main>
        </div>
      </DndProvider>
    </QueryClientProvider>
  )
}

export default App
