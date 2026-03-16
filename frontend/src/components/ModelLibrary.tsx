import { useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import { useDrag } from 'react-dnd'
import { Brain, Sparkles, Plus } from 'lucide-react'
import { api } from '../lib/api'
import type { Model } from '../types'
import { CreateModelModal } from './CreateModelModal'

export function ModelLibrary() {
  const [isModalOpen, setIsModalOpen] = useState(false)
  
  const { data: models, isLoading } = useQuery({
    queryKey: ['models'],
    queryFn: api.getModels,
    refetchInterval: 5000
  })

  if (isLoading) {
    return (
      <>
        <div className="bg-slate-800/50 backdrop-blur rounded-xl p-6 border border-purple-500/20">
          <div className="animate-pulse space-y-4">
            <div className="h-4 bg-slate-700 rounded w-3/4"></div>
            <div className="h-20 bg-slate-700 rounded"></div>
            <div className="h-20 bg-slate-700 rounded"></div>
          </div>
        </div>
        <CreateModelModal isOpen={isModalOpen} onClose={() => setIsModalOpen(false)} />
      </>
    )
  }

  return (
    <>
      <div className="bg-slate-800/50 backdrop-blur rounded-xl p-6 border border-purple-500/20 sticky top-8">
        <div className="flex items-center justify-between mb-6">
          <div className="flex items-center gap-2">
            <Brain className="w-6 h-6 text-purple-400" />
            <h2 className="text-xl font-bold text-white">Model Garden</h2>
          </div>
          <button
            onClick={() => setIsModalOpen(true)}
            className="px-3 py-1.5 bg-gradient-to-r from-purple-500 to-pink-500 hover:from-purple-600 hover:to-pink-600 text-white text-sm rounded-lg font-medium transition-all flex items-center gap-1.5"
          >
            <Plus className="w-4 h-4" />
            Add
          </button>
        </div>

      <div className="space-y-3 max-h-[calc(100vh-200px)] overflow-y-auto pr-2">
        {models?.map((model) => (
          <ModelCard key={model.model_id} model={model} />
        ))}
      </div>

        {models?.length === 0 && (
          <div className="text-center text-slate-400 py-8">
            <p>No models registered</p>
            <p className="text-sm mt-2">Click "Add" to create a model</p>
          </div>
        )}
      </div>
      
      <CreateModelModal isOpen={isModalOpen} onClose={() => setIsModalOpen(false)} />
    </>
  )
}

function ModelCard({ model }: { model: Model }) {
  const [{ isDragging }, drag] = useDrag(() => ({
    type: 'MODEL',
    item: model,
    collect: (monitor) => ({
      isDragging: !!monitor.isDragging(),
    }),
  }))

  const winRate = model.stats.win_rate * 100
  const hasOntology = !!model.ontology
  const eloRating = model.average_rating || 1500
  
  // ELO color coding
  const getEloColor = (rating: number) => {
    if (rating >= 1700) return 'text-yellow-400'
    if (rating >= 1600) return 'text-green-400'
    if (rating >= 1500) return 'text-blue-400'
    if (rating >= 1400) return 'text-purple-400'
    return 'text-slate-400'
  }

  return (
    <div
      ref={drag}
      className={`
        bg-gradient-to-br from-slate-700/50 to-slate-800/50 
        rounded-lg p-4 border border-purple-500/30
        cursor-move transition-all duration-200
        hover:border-purple-400/50 hover:shadow-lg hover:shadow-purple-500/20
        ${isDragging ? 'opacity-50 scale-95' : 'opacity-100'}
      `}
    >
      <div className="flex items-start justify-between mb-2">
        <div className="flex-1">
          <h3 className="text-white font-semibold text-sm flex items-center gap-2">
            {model.name}
            {hasOntology && (
              <Sparkles className="w-3 h-3 text-yellow-400" />
            )}
          </h3>
          <p className="text-slate-400 text-xs">v{model.version}</p>
        </div>
        <div className="text-right">
          <div className={`font-bold text-lg ${getEloColor(eloRating)}`}>
            {Math.round(eloRating)}
          </div>
          <div className="text-xs text-slate-500">ELO</div>
        </div>
      </div>

      {model.stats.total_matches > 0 && (
        <div className="mt-3 space-y-1">
          <div className="flex justify-between text-xs">
            <span className="text-slate-400">Win Rate</span>
            <span className={`font-semibold ${
              winRate >= 60 ? 'text-green-400' : 
              winRate >= 40 ? 'text-yellow-400' : 
              'text-red-400'
            }`}>
              {winRate.toFixed(1)}%
            </span>
          </div>
          <div className="w-full bg-slate-700 rounded-full h-1.5">
            <div
              className="bg-gradient-to-r from-purple-500 to-pink-500 h-1.5 rounded-full transition-all"
              style={{ width: `${winRate}%` }}
            />
          </div>
          <div className="flex justify-between text-xs text-slate-500">
            <span>{model.stats.total_matches} matches</span>
            <span>{model.stats.wins}W {model.stats.losses}L {model.stats.draws}D</span>
          </div>
        </div>
      )}

      {hasOntology && model.ontology && (
        <div className="mt-2 text-xs text-purple-300 bg-purple-900/20 rounded px-2 py-1">
          {model.ontology.task_type}
        </div>
      )}
    </div>
  )
}
