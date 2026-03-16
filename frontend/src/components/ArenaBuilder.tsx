import { useState } from 'react'
import { useDrop } from 'react-dnd'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { Swords, Sparkles, Play, AlertCircle, Trophy } from 'lucide-react'
import { api } from '../lib/api'
import type { Model } from '../types'

export function ArenaBuilder() {
  const queryClient = useQueryClient()
  const [selectedModels, setSelectedModels] = useState<(Model | null)[]>([null, null])
  const [selectedArena, setSelectedArena] = useState<string>('')
  const [compatibleModels, setCompatibleModels] = useState<any[]>([])
  const [showCompatibility, setShowCompatibility] = useState(false)

  const { data: arenas } = useQuery({
    queryKey: ['arenas'],
    queryFn: api.getArenas
  })

  const matchMutation = useMutation({
    mutationFn: (data: { model_a_id: string; model_b_id: string; arena_id: string }) =>
      api.createMatch(data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['models'] })
      queryClient.invalidateQueries({ queryKey: ['runs'] })
      setSelectedModels([null, null])
    }
  })

  const handleSlotDrop = async (item: Model, targetIndex: number) => {
    // Don't allow same model in both slots
    if (selectedModels.some(m => m?.model_id === item.model_id)) {
      return
    }
    
    // Check for compatibility if first model has ontology
    const hasNoModels = selectedModels.every(m => m === null)
    if (hasNoModels && item.ontology) {
      try {
        const compatible = await api.getCompatibleModels(item.model_id, 0.5)
        setCompatibleModels(compatible)
        setShowCompatibility(true)
      } catch (error) {
        console.error('Failed to fetch compatible models:', error)
      }
    }
    
    // Place model in specific slot
    const newModels: (Model | null)[] = [...selectedModels]
    newModels[targetIndex] = item
    setSelectedModels(newModels)
  }

  const removeModel = (index: number) => {
    const newModels: (Model | null)[] = [...selectedModels]
    newModels[index] = null
    setSelectedModels(newModels)
    if (newModels.every(m => m === null)) {
      setCompatibleModels([])
      setShowCompatibility(false)
    }
  }

  const runMatch = () => {
    if (selectedModels[0] && selectedModels[1] && selectedArena) {
      matchMutation.mutate({
        model_a_id: selectedModels[0].model_id,
        model_b_id: selectedModels[1].model_id,
        arena_id: selectedArena
      })
    }
  }

  const canRunMatch = selectedModels[0] !== null && selectedModels[1] !== null && selectedArena && !matchMutation.isPending

  return (
    <div className="space-y-6">
      {/* Arena Builder Container */}
      <div
        className="relative min-h-[300px] bg-slate-800/30 backdrop-blur rounded-2xl p-8 border-2 border-dashed border-slate-600/50 transition-all duration-200"
      >
        <div className="text-center mb-6">
          <div className="inline-flex items-center gap-2 bg-purple-500/10 px-4 py-2 rounded-full mb-2">
            <Swords className="w-5 h-5 text-purple-400" />
            <h2 className="text-xl font-bold text-white">Arena Builder</h2>
          </div>
          <p className="text-slate-400 text-sm">
            Drag and drop models to create an arena match
          </p>
        </div>

        {/* Model Slots */}
        <div className="grid grid-cols-2 gap-6 mb-6">
          {[0, 1].map((index) => (
            <ModelSlot
              key={index}
              model={selectedModels[index] || undefined}
              index={index}
              onRemove={() => removeModel(index)}
              isEmpty={selectedModels[index] === null}
              onDrop={handleSlotDrop}
            />
          ))}
        </div>

        {/* VS Indicator */}
        {selectedModels[0] && selectedModels[1] && (
          <div className="absolute top-1/2 left-1/2 transform -translate-x-1/2 -translate-y-1/2">
            <div className="bg-gradient-to-r from-purple-500 to-pink-500 text-white font-bold text-2xl px-6 py-3 rounded-full shadow-lg animate-pulse">
              VS
            </div>
          </div>
        )}
      </div>

      {/* Compatibility Suggestions */}
      {showCompatibility && compatibleModels.length > 0 && (selectedModels[0] !== null || selectedModels[1] !== null) && !(selectedModels[0] && selectedModels[1]) && (
        <div className="bg-gradient-to-br from-yellow-900/20 to-orange-900/20 backdrop-blur rounded-xl p-6 border border-yellow-500/30">
          <div className="flex items-center gap-2 mb-4">
            <Sparkles className="w-5 h-5 text-yellow-400" />
            <h3 className="text-lg font-semibold text-white">Suggested Compatible Models</h3>
          </div>
          <div className="grid grid-cols-3 gap-3">
            {compatibleModels.slice(0, 6).map((compatible) => {
              const compatModel = queryClient.getQueryData<Model[]>(['models'])?.find(
                m => m.model_id === compatible.model_id
              )
              const firstModel = selectedModels[0] || selectedModels[1]
              const targetElo = firstModel?.average_rating || 1500
              const compatElo = compatModel?.average_rating || 1500
              const eloDiff = Math.abs(targetElo - compatElo)
              
              return (
                <div
                  key={compatible.model_id}
                  className="bg-slate-800/50 rounded-lg p-3 border border-yellow-500/20 cursor-pointer hover:border-yellow-400/50 transition-all"
                  onClick={() => {
                    if (compatModel) {
                      // Place in the empty slot
                      const emptySlotIndex = selectedModels[0] === null ? 0 : 1
                      const newModels: (Model | null)[] = [...selectedModels]
                      newModels[emptySlotIndex] = compatModel
                      setSelectedModels(newModels)
                      setShowCompatibility(false)
                    }
                  }}
                >
                  <div className="flex justify-between items-start mb-1">
                    <p className="text-white font-semibold text-sm">{compatible.model_name}</p>
                    <span className="text-xs text-purple-300 font-bold">
                      {Math.round(compatElo)}
                    </span>
                  </div>
                  <div className="flex items-center gap-1 mb-1">
                    <div className="flex-1 bg-slate-700 rounded-full h-1">
                      <div
                        className="bg-yellow-400 h-1 rounded-full"
                        style={{ width: `${compatible.compatibility_score * 100}%` }}
                      />
                    </div>
                    <span className="text-xs text-yellow-400 font-semibold">
                      {(compatible.compatibility_score * 100).toFixed(0)}%
                    </span>
                  </div>
                  <p className="text-xs text-slate-400">
                    ELO Δ: {eloDiff.toFixed(0)} pts
                  </p>
                </div>
              )
            })}
          </div>
        </div>
      )}

      {/* Arena Selection & Run */}
      <div className="bg-slate-800/50 backdrop-blur rounded-xl p-6 border border-purple-500/20">
        <label className="block text-white font-semibold mb-3">Select Arena</label>
        <div className="grid grid-cols-2 gap-3 mb-4">
          {arenas?.map((arena) => (
            <button
              key={arena.arena_id}
              onClick={() => setSelectedArena(arena.arena_id)}
              className={`
                p-4 rounded-lg border-2 transition-all text-left
                ${selectedArena === arena.arena_id
                  ? 'border-purple-500 bg-purple-500/20'
                  : 'border-slate-600/50 bg-slate-700/30 hover:border-purple-400/50'
                }
              `}
            >
              <div className="flex items-center gap-2">
                <Trophy className="w-4 h-4 text-purple-400" />
                <span className="text-white font-semibold">{arena.name}</span>
              </div>
              <p className="text-slate-400 text-xs mt-1">{arena.match_count} matches</p>
            </button>
          ))}
        </div>

        <button
          onClick={runMatch}
          disabled={!canRunMatch}
          className={`
            w-full py-4 rounded-xl font-bold text-lg flex items-center justify-center gap-2
            transition-all duration-200
            ${canRunMatch
              ? 'bg-gradient-to-r from-purple-500 to-pink-500 text-white hover:shadow-lg hover:shadow-purple-500/50 hover:scale-[1.02]'
              : 'bg-slate-700/50 text-slate-500 cursor-not-allowed'
            }
          `}
        >
          {matchMutation.isPending ? (
            <>
              <div className="w-5 h-5 border-2 border-white border-t-transparent rounded-full animate-spin" />
              Running Match...
            </>
          ) : (
            <>
              <Play className="w-5 h-5" />
              Run Arena Match
            </>
          )}
        </button>

        {!canRunMatch && selectedModels.length > 0 && (
          <div className="mt-3 flex items-center gap-2 text-amber-400 text-sm">
            <AlertCircle className="w-4 h-4" />
            <span>
              {selectedModels.length < 2
                ? 'Add one more model to begin'
                : 'Select an arena to continue'
              }
            </span>
          </div>
        )}
      </div>
    </div>
  )
}

function ModelSlot({
  model,
  index,
  onRemove,
  isEmpty,
  onDrop
}: {
  model?: Model
  index: number
  onRemove: () => void
  isEmpty: boolean
  onDrop: (item: Model, targetIndex: number) => void
}) {
  const [{ isOver, canDrop }, drop] = useDrop(() => ({
    accept: 'MODEL',
    drop: (item: Model) => onDrop(item, index),
    collect: (monitor) => ({
      isOver: !!monitor.isOver(),
      canDrop: !!monitor.canDrop(),
    }),
  }))

  if (isEmpty || !model) {
    return (
      <div 
        ref={drop}
        className={`
          bg-slate-700/20 border-2 border-dashed rounded-xl p-6 min-h-[150px] flex flex-col items-center justify-center
          transition-all duration-200
          ${isOver && canDrop ? 'border-purple-400 bg-purple-500/10 scale-105' : 'border-slate-600/50'}
        `}
      >
        <div className="text-slate-500 text-center">
          <div className="w-12 h-12 mx-auto mb-2 rounded-full bg-slate-700/50 flex items-center justify-center">
            <span className="text-2xl font-bold">{index + 1}</span>
          </div>
          <p className="text-sm">Drop model here</p>
        </div>
      </div>
    )
  }

  return (
    <div className="bg-gradient-to-br from-purple-900/30 to-pink-900/30 border-2 border-purple-500/50 rounded-xl p-6 min-h-[150px] relative group">
      <button
        onClick={onRemove}
        className="absolute top-2 right-2 w-6 h-6 bg-red-500/80 hover:bg-red-500 rounded-full flex items-center justify-center opacity-0 group-hover:opacity-100 transition-opacity"
      >
        <span className="text-white text-sm">×</span>
      </button>
      
      <div className="flex items-start gap-3">
        <div className="w-10 h-10 rounded-full bg-purple-500/20 flex items-center justify-center flex-shrink-0">
          <span className="text-purple-300 font-bold">{index + 1}</span>
        </div>
        <div className="flex-1">
          <h3 className="text-white font-bold">{model.name}</h3>
          <p className="text-purple-300 text-sm">v{model.version}</p>
          {model.ontology && (
            <div className="mt-2 inline-block text-xs bg-purple-500/20 text-purple-200 px-2 py-1 rounded">
              {model.ontology.task_type}
            </div>
          )}
          {model.stats.total_matches > 0 && (
            <div className="mt-2 text-xs text-slate-300">
              Win Rate: {(model.stats.win_rate * 100).toFixed(1)}%
            </div>
          )}
        </div>
      </div>
    </div>
  )
}
