import { useQuery } from '@tanstack/react-query'
import { Activity, TrendingUp, Target, Clock } from 'lucide-react'
import { LineChart, Line, BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from 'recharts'
import { api } from '../lib/api'

export function ExperimentDashboard() {
  const { data: runs, isLoading } = useQuery({
    queryKey: ['runs'],
    queryFn: api.getRuns,
    refetchInterval: 3000
  })

  const { data: stats } = useQuery({
    queryKey: ['stats'],
    queryFn: api.getStats
  })

  if (isLoading) {
    return (
      <div className="flex items-center justify-center h-96">
        <div className="w-12 h-12 border-4 border-purple-500 border-t-transparent rounded-full animate-spin" />
      </div>
    )
  }

  // Process runs for visualization
  const recentRuns = runs?.slice(0, 10).reverse() || []
  const chartData = recentRuns.map((run, idx) => ({
    name: `Run ${idx + 1}`,
    model_a_score: run.metrics.model_a_score || 0,
    model_b_score: run.metrics.model_b_score || 0,
    model_a_rating: run.metrics.model_a_rating_after || 1500,
    model_b_rating: run.metrics.model_b_rating_after || 1500,
  }))

  return (
    <div className="space-y-6">
      {/* Stats Cards */}
      <div className="grid grid-cols-4 gap-4">
        <StatCard
          icon={<Activity className="w-6 h-6" />}
          label="Total Matches"
          value={stats?.total_matches || 0}
          color="purple"
        />
        <StatCard
          icon={<Target className="w-6 h-6" />}
          label="Active Models"
          value={stats?.total_models || 0}
          color="pink"
        />
        <StatCard
          icon={<TrendingUp className="w-6 h-6" />}
          label="Arenas"
          value={stats?.total_arenas || 0}
          color="blue"
        />
        <StatCard
          icon={<Clock className="w-6 h-6" />}
          label="Recent Runs"
          value={runs?.length || 0}
          color="green"
        />
      </div>

      {/* Charts */}
      <div className="grid grid-cols-2 gap-6">
        {/* Match Scores */}
        <div className="bg-slate-800/50 backdrop-blur rounded-xl p-6 border border-purple-500/20">
          <h3 className="text-white font-bold text-lg mb-4">Recent Match Scores</h3>
          <ResponsiveContainer width="100%" height={250}>
            <BarChart data={chartData}>
              <CartesianGrid strokeDasharray="3 3" stroke="#475569" />
              <XAxis dataKey="name" stroke="#94a3b8" />
              <YAxis stroke="#94a3b8" />
              <Tooltip
                contentStyle={{ backgroundColor: '#1e293b', border: '1px solid #a855f7' }}
                labelStyle={{ color: '#fff' }}
              />
              <Bar dataKey="model_a_score" fill="#a855f7" name="Model A" />
              <Bar dataKey="model_b_score" fill="#ec4899" name="Model B" />
            </BarChart>
          </ResponsiveContainer>
        </div>

        {/* Rating Evolution */}
        <div className="bg-slate-800/50 backdrop-blur rounded-xl p-6 border border-purple-500/20">
          <h3 className="text-white font-bold text-lg mb-4">ELO Rating Evolution</h3>
          <ResponsiveContainer width="100%" height={250}>
            <LineChart data={chartData}>
              <CartesianGrid strokeDasharray="3 3" stroke="#475569" />
              <XAxis dataKey="name" stroke="#94a3b8" />
              <YAxis stroke="#94a3b8" domain={[1400, 1600]} />
              <Tooltip
                contentStyle={{ backgroundColor: '#1e293b', border: '1px solid #a855f7' }}
                labelStyle={{ color: '#fff' }}
              />
              <Line
                type="monotone"
                dataKey="model_a_rating"
                stroke="#a855f7"
                strokeWidth={2}
                name="Model A"
              />
              <Line
                type="monotone"
                dataKey="model_b_rating"
                stroke="#ec4899"
                strokeWidth={2}
                name="Model B"
              />
            </LineChart>
          </ResponsiveContainer>
        </div>
      </div>

      {/* Recent Runs Table */}
      <div className="bg-slate-800/50 backdrop-blur rounded-xl p-6 border border-purple-500/20">
        <h3 className="text-white font-bold text-lg mb-4">Recent Experiment Runs</h3>
        <div className="overflow-x-auto">
          <table className="w-full">
            <thead>
              <tr className="border-b border-slate-700">
                <th className="text-left py-3 px-4 text-slate-400 font-semibold text-sm">Run</th>
                <th className="text-left py-3 px-4 text-slate-400 font-semibold text-sm">Status</th>
                <th className="text-left py-3 px-4 text-slate-400 font-semibold text-sm">Model A Score</th>
                <th className="text-left py-3 px-4 text-slate-400 font-semibold text-sm">Model B Score</th>
                <th className="text-left py-3 px-4 text-slate-400 font-semibold text-sm">Winner</th>
                <th className="text-left py-3 px-4 text-slate-400 font-semibold text-sm">Time</th>
              </tr>
            </thead>
            <tbody>
              {runs?.slice(0, 10).map((run) => (
                <tr key={run.run_id} className="border-b border-slate-700/50 hover:bg-slate-700/30">
                  <td className="py-3 px-4 text-white text-sm font-mono">{run.run_name}</td>
                  <td className="py-3 px-4">
                    <span className={`px-2 py-1 rounded text-xs font-semibold ${
                      run.status === 'FINISHED' ? 'bg-green-500/20 text-green-400' :
                      run.status === 'RUNNING' ? 'bg-yellow-500/20 text-yellow-400' :
                      'bg-red-500/20 text-red-400'
                    }`}>
                      {run.status}
                    </span>
                  </td>
                  <td className="py-3 px-4 text-purple-300">
                    {run.metrics.model_a_score?.toFixed(3) || 'N/A'}
                  </td>
                  <td className="py-3 px-4 text-pink-300">
                    {run.metrics.model_b_score?.toFixed(3) || 'N/A'}
                  </td>
                  <td className="py-3 px-4">
                    <span className="text-green-400 font-semibold">
                      {run.tags.winner === 'draw' ? 'Draw' : run.tags.winner || 'N/A'}
                    </span>
                  </td>
                  <td className="py-3 px-4 text-slate-400 text-sm">
                    {new Date(run.start_time).toLocaleTimeString()}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  )
}

function StatCard({
  icon,
  label,
  value,
  color
}: {
  icon: React.ReactNode
  label: string
  value: number
  color: 'purple' | 'pink' | 'blue' | 'green'
}) {
  const colors = {
    purple: 'from-purple-500 to-purple-600',
    pink: 'from-pink-500 to-pink-600',
    blue: 'from-blue-500 to-blue-600',
    green: 'from-green-500 to-green-600',
  }

  return (
    <div className="bg-slate-800/50 backdrop-blur rounded-xl p-6 border border-purple-500/20">
      <div className={`w-12 h-12 rounded-lg bg-gradient-to-br ${colors[color]} flex items-center justify-center text-white mb-3`}>
        {icon}
      </div>
      <p className="text-slate-400 text-sm mb-1">{label}</p>
      <p className="text-white text-3xl font-bold">{value}</p>
    </div>
  )
}
