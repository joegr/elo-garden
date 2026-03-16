export interface Model {
  model_id: string
  name: string
  version: string
  metadata: Record<string, any>
  ratings: Record<string, number>
  stats: {
    total_matches: number
    wins: number
    losses: number
    draws: number
    win_rate: number
  }
  ontology?: {
    task_type: string
    input_schema: any
    output_schema: any
    capabilities: string[]
    tags: string[]
  }
  average_rating?: number
  highest_rating?: number
}

export interface Arena {
  arena_id: string
  name: string
  description: string | null
  match_count: number
}

export interface Match {
  match_id: string
  model_a_id: string
  model_b_id: string
  arena_id: string
  winner_id: string | null
  scores: Record<string, number>
  rating_changes: Record<string, number>
}

export interface MLflowRun {
  run_id: string
  run_name: string
  experiment_id: string
  status: string
  start_time: number
  end_time: number | null
  metrics: Record<string, number>
  params: Record<string, string>
  tags: Record<string, string>
}
