import { useQuery } from '@tanstack/react-query'
import { Activity, TrendingUp, Target, Trophy } from 'lucide-react'
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from 'recharts'
import { api } from '../lib/api'

export function ExperimentDashboard() {
  const { data: models, isLoading } = useQuery({
    queryKey: ['models'],
    queryFn: api.getModels,
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

  // Build leaderboard chart data from models
  const leaderboardData = (models || [])
    .map(m => ({
      name: m.name,
      rating: m.average_rating || 1500,
      wins: m.stats.wins || 0,
      losses: m.stats.losses || 0,
      win_rate: m.stats.win_rate || 0,
      matches: m.stats.total_matches || 0,
    }))
    .sort((a, b) => b.rating - a.rating)
    .slice(0, 10)

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
          icon={<Trophy className="w-6 h-6" />}
          label="Tournaments"
          value={stats?.total_tournaments || 0}
          color="green"
        />
      </div>

      {/* Charts */}
      <div className="grid grid-cols-2 gap-6">
        {/* ELO Leaderboard */}
        <div className="bg-slate-800/50 backdrop-blur rounded-xl p-6 border border-purple-500/20">
          <h3 className="text-white font-bold text-lg mb-4">ELO Ratings</h3>
          <ResponsiveContainer width="100%" height={250}>
            <BarChart data={leaderboardData} layout="vertical">
              <CartesianGrid strokeDasharray="3 3" stroke="#475569" />
              <XAxis type="number" stroke="#94a3b8" domain={[1400, 'auto']} />
              <YAxis type="category" dataKey="name" stroke="#94a3b8" width={100} />
              <Tooltip
                contentStyle={{ backgroundColor: '#1e293b', border: '1px solid #a855f7' }}
                labelStyle={{ color: '#fff' }}
              />
              <Bar dataKey="rating" fill="#a855f7" name="ELO Rating" />
            </BarChart>
          </ResponsiveContainer>
        </div>

        {/* Win/Loss */}
        <div className="bg-slate-800/50 backdrop-blur rounded-xl p-6 border border-purple-500/20">
          <h3 className="text-white font-bold text-lg mb-4">Win / Loss Record</h3>
          <ResponsiveContainer width="100%" height={250}>
            <BarChart data={leaderboardData}>
              <CartesianGrid strokeDasharray="3 3" stroke="#475569" />
              <XAxis dataKey="name" stroke="#94a3b8" />
              <YAxis stroke="#94a3b8" />
              <Tooltip
                contentStyle={{ backgroundColor: '#1e293b', border: '1px solid #a855f7' }}
                labelStyle={{ color: '#fff' }}
              />
              <Bar dataKey="wins" fill="#22c55e" name="Wins" />
              <Bar dataKey="losses" fill="#ef4444" name="Losses" />
            </BarChart>
          </ResponsiveContainer>
        </div>
      </div>

      {/* Model Leaderboard Table */}
      <div className="bg-slate-800/50 backdrop-blur rounded-xl p-6 border border-purple-500/20">
        <h3 className="text-white font-bold text-lg mb-4">Model Leaderboard</h3>
        <div className="overflow-x-auto">
          <table className="w-full">
            <thead>
              <tr className="border-b border-slate-700">
                <th className="text-left py-3 px-4 text-slate-400 font-semibold text-sm">#</th>
                <th className="text-left py-3 px-4 text-slate-400 font-semibold text-sm">Model</th>
                <th className="text-left py-3 px-4 text-slate-400 font-semibold text-sm">ELO Rating</th>
                <th className="text-left py-3 px-4 text-slate-400 font-semibold text-sm">Matches</th>
                <th className="text-left py-3 px-4 text-slate-400 font-semibold text-sm">Win Rate</th>
                <th className="text-left py-3 px-4 text-slate-400 font-semibold text-sm">W / L / D</th>
              </tr>
            </thead>
            <tbody>
              {leaderboardData.map((m, idx) => (
                <tr key={m.name} className="border-b border-slate-700/50 hover:bg-slate-700/30">
                  <td className="py-3 px-4 text-slate-400 text-sm">{idx + 1}</td>
                  <td className="py-3 px-4 text-white text-sm font-semibold">{m.name}</td>
                  <td className="py-3 px-4 text-purple-300 font-mono">{m.rating.toFixed(0)}</td>
                  <td className="py-3 px-4 text-slate-300">{m.matches}</td>
                  <td className="py-3 px-4">
                    <span className={`font-semibold ${m.win_rate >= 0.5 ? 'text-green-400' : 'text-red-400'}`}>
                      {(m.win_rate * 100).toFixed(1)}%
                    </span>
                  </td>
                  <td className="py-3 px-4 text-slate-300 text-sm">
                    <span className="text-green-400">{m.wins}</span>
                    {' / '}
                    <span className="text-red-400">{m.losses}</span>
                    {' / '}
                    <span className="text-slate-400">{m.matches - m.wins - m.losses}</span>
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
