import axios from 'axios'
import type { Model, Arena, Match, MLflowRun } from '../types'

const API_BASE = 'http://localhost:8000'

const client = axios.create({
  baseURL: API_BASE,
  headers: {
    'Content-Type': 'application/json',
  },
})

export const api = {
  // Models
  getModels: async (): Promise<Model[]> => {
    const { data } = await client.get('/models')
    return data
  },

  getModel: async (modelId: string): Promise<Model> => {
    const { data } = await client.get(`/models/${modelId}`)
    return data
  },

  createModel: async (model: any): Promise<Model> => {
    const { data } = await client.post('/models', model)
    return data
  },

  getCompatibleModels: async (modelId: string, minScore: number = 0.5) => {
    const { data } = await client.post(`/models/${modelId}/compatible`, { min_score: minScore })
    return data
  },

  // Arenas
  getArenas: async (): Promise<Arena[]> => {
    const { data } = await client.get('/arenas')
    return data
  },

  createArena: async (arena: any): Promise<Arena> => {
    const { data } = await client.post('/arenas', arena)
    return data
  },

  // Matches
  createMatch: async (match: { model_a_id: string; model_b_id: string; arena_id: string }): Promise<Match> => {
    const { data} = await client.post('/matches', match)
    return data
  },

  // MLflow Integration
  getRuns: async (): Promise<MLflowRun[]> => {
    const { data } = await client.get('/mlflow/runs')
    return data
  },

  getExperiments: async () => {
    const { data } = await client.get('/mlflow/experiments')
    return data
  },

  // Stats
  getStats: async () => {
    const { data } = await client.get('/stats')
    return data
  },
}
