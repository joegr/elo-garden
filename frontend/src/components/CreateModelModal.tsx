import { useState } from 'react'
import { useMutation, useQueryClient } from '@tanstack/react-query'
import { X, Plus, Sparkles } from 'lucide-react'
import { api } from '../lib/api'

interface CreateModelModalProps {
  isOpen: boolean
  onClose: () => void
}

export function CreateModelModal({ isOpen, onClose }: CreateModelModalProps) {
  const queryClient = useQueryClient()
  const [formData, setFormData] = useState({
    name: '',
    version: '1.0',
    metadata: {},
    withOntology: false,
    taskType: 'text_generation',
    inputDataType: 'text',
    outputDataType: 'text',
    capabilities: '',
    tags: ''
  })

  const createModelMutation = useMutation({
    mutationFn: (data: any) => api.createModel(data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['models'] })
      onClose()
      resetForm()
    }
  })

  const resetForm = () => {
    setFormData({
      name: '',
      version: '1.0',
      metadata: {},
      withOntology: false,
      taskType: 'text_generation',
      inputDataType: 'text',
      outputDataType: 'text',
      capabilities: '',
      tags: ''
    })
  }

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault()
    
    const modelData: any = {
      name: formData.name,
      version: formData.version,
      metadata: formData.metadata
    }

    if (formData.withOntology) {
      modelData.ontology = {
        task_type: formData.taskType,
        input_schema: {
          data_type: formData.inputDataType,
          description: `Input for ${formData.name}`
        },
        output_schema: {
          data_type: formData.outputDataType,
          description: `Output from ${formData.name}`
        },
        capabilities: formData.capabilities ? formData.capabilities.split(',').map(c => c.trim()).filter(Boolean) : [],
        tags: formData.tags ? formData.tags.split(',').map(t => t.trim()).filter(Boolean) : []
      }
    }

    createModelMutation.mutate(modelData)
  }

  if (!isOpen) return null

  return (
    <div className="fixed inset-0 bg-black/80 backdrop-blur-sm flex items-center justify-center z-50 p-4">
      <div className="bg-slate-800 rounded-xl border border-purple-500/30 w-full max-w-2xl max-h-[90vh] overflow-y-auto">
        {/* Header */}
        <div className="sticky top-0 bg-slate-800 border-b border-slate-700 p-6 flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 bg-gradient-to-br from-purple-500 to-pink-500 rounded-lg flex items-center justify-center">
              <Plus className="w-6 h-6 text-white" />
            </div>
            <div>
              <h2 className="text-2xl font-bold text-white">Register New Model</h2>
              <p className="text-sm text-slate-400">Add a model to Garden with optional ontology</p>
            </div>
          </div>
          <button
            onClick={onClose}
            className="w-8 h-8 rounded-lg bg-slate-700 hover:bg-slate-600 flex items-center justify-center text-slate-400 hover:text-white transition-colors"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Form */}
        <form onSubmit={handleSubmit} className="p-6 space-y-6">
          {/* Basic Info */}
          <div className="space-y-4">
            <h3 className="text-lg font-semibold text-white">Basic Information</h3>
            
            <div>
              <label className="block text-sm font-medium text-slate-300 mb-2">
                Model Name *
              </label>
              <input
                type="text"
                required
                value={formData.name}
                onChange={(e) => setFormData({ ...formData, name: e.target.value })}
                className="w-full px-4 py-2 bg-slate-700 border border-slate-600 rounded-lg text-white placeholder-slate-400 focus:outline-none focus:ring-2 focus:ring-purple-500"
                placeholder="e.g., GPT-4, Claude-3, BERT-Large"
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-slate-300 mb-2">
                Version *
              </label>
              <input
                type="text"
                required
                value={formData.version}
                onChange={(e) => setFormData({ ...formData, version: e.target.value })}
                className="w-full px-4 py-2 bg-slate-700 border border-slate-600 rounded-lg text-white placeholder-slate-400 focus:outline-none focus:ring-2 focus:ring-purple-500"
                placeholder="e.g., 1.0, v2.1, 2024-03"
              />
            </div>
          </div>

          {/* Ontology Toggle */}
          <div className="border-t border-slate-700 pt-6">
            <label className="flex items-center gap-3 cursor-pointer">
              <input
                type="checkbox"
                checked={formData.withOntology}
                onChange={(e) => setFormData({ ...formData, withOntology: e.target.checked })}
                className="w-5 h-5 rounded bg-slate-700 border-slate-600 text-purple-500 focus:ring-2 focus:ring-purple-500"
              />
              <div className="flex items-center gap-2">
                <Sparkles className="w-5 h-5 text-yellow-400" />
                <span className="text-white font-medium">Add Ontology (Recommended)</span>
              </div>
            </label>
            <p className="text-sm text-slate-400 mt-2 ml-8">
              Enable ELO-based compatibility matching and smart opponent suggestions
            </p>
          </div>

          {/* Ontology Fields */}
          {formData.withOntology && (
            <div className="space-y-4 bg-slate-900/50 rounded-lg p-4 border border-yellow-500/20">
              <h3 className="text-lg font-semibold text-white flex items-center gap-2">
                <Sparkles className="w-5 h-5 text-yellow-400" />
                Ontology Configuration
              </h3>

              <div>
                <label className="block text-sm font-medium text-slate-300 mb-2">
                  Task Type
                </label>
                <select
                  value={formData.taskType}
                  onChange={(e) => setFormData({ ...formData, taskType: e.target.value })}
                  className="w-full px-4 py-2 bg-slate-700 border border-slate-600 rounded-lg text-white focus:outline-none focus:ring-2 focus:ring-purple-500"
                >
                  <option value="text_generation">Text Generation</option>
                  <option value="text_classification">Text Classification</option>
                  <option value="question_answering">Question Answering</option>
                  <option value="summarization">Summarization</option>
                  <option value="translation">Translation</option>
                  <option value="image_classification">Image Classification</option>
                  <option value="object_detection">Object Detection</option>
                  <option value="custom">Custom</option>
                </select>
              </div>

              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm font-medium text-slate-300 mb-2">
                    Input Data Type
                  </label>
                  <select
                    value={formData.inputDataType}
                    onChange={(e) => setFormData({ ...formData, inputDataType: e.target.value })}
                    className="w-full px-4 py-2 bg-slate-700 border border-slate-600 rounded-lg text-white focus:outline-none focus:ring-2 focus:ring-purple-500"
                  >
                    <option value="text">Text</option>
                    <option value="image">Image</option>
                    <option value="audio">Audio</option>
                    <option value="video">Video</option>
                    <option value="multimodal">Multimodal</option>
                    <option value="structured">Structured Data</option>
                  </select>
                </div>

                <div>
                  <label className="block text-sm font-medium text-slate-300 mb-2">
                    Output Data Type
                  </label>
                  <select
                    value={formData.outputDataType}
                    onChange={(e) => setFormData({ ...formData, outputDataType: e.target.value })}
                    className="w-full px-4 py-2 bg-slate-700 border border-slate-600 rounded-lg text-white focus:outline-none focus:ring-2 focus:ring-purple-500"
                  >
                    <option value="text">Text</option>
                    <option value="image">Image</option>
                    <option value="audio">Audio</option>
                    <option value="video">Video</option>
                    <option value="multimodal">Multimodal</option>
                    <option value="structured">Structured Data</option>
                  </select>
                </div>
              </div>

              <div>
                <label className="block text-sm font-medium text-slate-300 mb-2">
                  Capabilities (comma-separated)
                </label>
                <input
                  type="text"
                  value={formData.capabilities}
                  onChange={(e) => setFormData({ ...formData, capabilities: e.target.value })}
                  className="w-full px-4 py-2 bg-slate-700 border border-slate-600 rounded-lg text-white placeholder-slate-400 focus:outline-none focus:ring-2 focus:ring-purple-500"
                  placeholder="e.g., generation, completion, chat, reasoning"
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-slate-300 mb-2">
                  Tags (comma-separated)
                </label>
                <input
                  type="text"
                  value={formData.tags}
                  onChange={(e) => setFormData({ ...formData, tags: e.target.value })}
                  className="w-full px-4 py-2 bg-slate-700 border border-slate-600 rounded-lg text-white placeholder-slate-400 focus:outline-none focus:ring-2 focus:ring-purple-500"
                  placeholder="e.g., llm, transformer, open-source, proprietary"
                />
              </div>
            </div>
          )}

          {/* Actions */}
          <div className="flex gap-3 pt-4 border-t border-slate-700">
            <button
              type="button"
              onClick={onClose}
              className="flex-1 px-6 py-3 bg-slate-700 hover:bg-slate-600 text-white rounded-lg font-medium transition-colors"
            >
              Cancel
            </button>
            <button
              type="submit"
              disabled={createModelMutation.isPending}
              className="flex-1 px-6 py-3 bg-gradient-to-r from-purple-500 to-pink-500 hover:from-purple-600 hover:to-pink-600 text-white rounded-lg font-medium transition-all disabled:opacity-50 disabled:cursor-not-allowed"
            >
              {createModelMutation.isPending ? 'Creating...' : 'Create Model'}
            </button>
          </div>

          {createModelMutation.isError && (
            <div className="p-4 bg-red-500/10 border border-red-500/30 rounded-lg">
              <p className="text-red-400 text-sm">
                Error: {createModelMutation.error instanceof Error ? createModelMutation.error.message : 'Failed to create model'}
              </p>
            </div>
          )}
        </form>
      </div>
    </div>
  )
}
