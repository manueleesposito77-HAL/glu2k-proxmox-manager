import React, { useState, useEffect } from 'react';
import axios from 'axios';
import { Activity, Server, Database, HardDrive, Cpu, AlertCircle, Plus, X, Shield, ShieldOff, Loader2 } from 'lucide-react';

const API_BASE = "http://localhost:8000/api/v1";

const StatCard = ({ title, value, icon: Icon, color }) => (
  <div className="bg-slate-800 p-6 rounded-lg shadow-lg border border-slate-700">
    <div className="flex items-center justify-between">
      <div>
        <p className="text-slate-400 text-sm font-medium">{title}</p>
        <h3 className="text-2xl font-bold text-white mt-2">{value}</h3>
      </div>
      <div className={`p-3 rounded-full ${color} bg-opacity-20`}>
        <Icon className={`w-6 h-6 ${color.replace('bg-', 'text-')}`} />
      </div>
    </div>
  </div>
);

function App() {
  const [clusters, setClusters] = useState([]);
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [loading, setLoading] = useState(false);
  const [formData, setFormData] = useState({
    name: '', host: '', port: 8006, auth_user: '', auth_token: '', auth_type: 'token', verify_ssl: false
  });

  const fetchClusters = async () => {
    try {
      const res = await axios.get(`${API_BASE}/clusters/`);
      setClusters(res.data);
    } catch (err) {
      console.error("Error fetching clusters", err);
    }
  };

  useEffect(() => {
    fetchClusters();
  }, []);

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);
    try {
      await axios.post(`${API_BASE}/clusters/`, formData);
      setIsModalOpen(false);
      setFormData({ name: '', host: '', port: 8006, auth_user: '', auth_token: '', auth_type: 'token', verify_ssl: false });
      fetchClusters();
    } catch (err) {
      alert("Errore durante l'aggiunta del server. Verifica i dati.");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-slate-900 text-slate-100 font-sans">
      {/* Sidebar */}
      <aside className="fixed left-0 top-0 h-full w-64 bg-slate-800 border-r border-slate-700">
        <div className="p-6">
          <h1 className="text-xl font-bold text-blue-400 flex items-center gap-2">
            <Server className="w-6 h-6" /> NEXUS
          </h1>
        </div>
        <nav className="mt-6 px-4">
          <button className="w-full flex items-center gap-3 px-4 py-3 bg-slate-700 rounded-lg text-white mb-2">
            <Activity className="w-5 h-5" /> Dashboard
          </button>
          <div className="mt-8 mb-2 px-4 text-xs font-semibold text-slate-500 uppercase tracking-wider">
            Clusters
          </div>
          {clusters.map(c => (
            <div key={c.id} className="flex items-center gap-3 px-4 py-2 text-slate-300 text-sm hover:text-white cursor-pointer">
              <div className="w-2 h-2 rounded-full bg-green-500"></div> {c.name}
            </div>
          ))}
          <button 
            onClick={() => setIsModalOpen(true)}
            className="mt-4 w-full flex items-center justify-center gap-2 px-4 py-2 border border-dashed border-slate-600 rounded-lg text-slate-400 hover:text-white hover:border-slate-400 transition-all text-sm"
          >
            <Plus className="w-4 h-4" /> Add Server
          </button>
        </nav>
      </aside>

      {/* Main Content */}
      <main className="ml-64 p-8">
        <header className="flex justify-between items-center mb-8">
          <h2 className="text-3xl font-bold">Infrastruttura Globale</h2>
          <div className="flex items-center gap-4">
            <span className="flex items-center gap-2 text-green-400 bg-green-900/30 px-3 py-1 rounded-full text-sm">
              <span className="w-2 h-2 rounded-full bg-green-400 animate-pulse"></span>
              {clusters.length} Cluster Online
            </span>
          </div>
        </header>

        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
          <StatCard title="Total Clusters" value={clusters.length} icon={Server} color="bg-blue-500" />
          <StatCard title="Active Nodes" value="Calculated..." icon={Database} color="bg-green-500" />
          <StatCard title="Virtual Machines" value="Fetch..." icon={Cpu} color="bg-purple-500" />
          <StatCard title="System Alerts" value="0" icon={AlertCircle} color="bg-red-500" />
        </div>

        {/* Empty State if no clusters */}
        {clusters.length === 0 && (
          <div className="flex flex-col items-center justify-center p-12 bg-slate-800 rounded-xl border border-dashed border-slate-600 text-slate-400">
            <Server className="w-16 h-16 mb-4 opacity-20" />
            <p className="text-xl">Nessun server registrato</p>
            <button 
              onClick={() => setIsModalOpen(true)}
              className="mt-4 px-6 py-2 bg-blue-600 hover:bg-blue-500 text-white rounded-lg transition-colors"
            >
              Aggiungi il tuo primo Proxmox
            </button>
          </div>
        )}
      </main>

      {/* ADD SERVER MODAL */}
      {isModalOpen && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 backdrop-blur-sm">
          <div className="bg-slate-800 w-full max-w-lg rounded-xl shadow-2xl border border-slate-700 overflow-hidden animate-in fade-in zoom-in duration-200">
            <div className="flex justify-between items-center p-6 border-b border-slate-700 bg-slate-800/50">
              <h3 className="text-xl font-bold">Registra Server Proxmox</h3>
              <button onClick={() => setIsModalOpen(false)} className="text-slate-400 hover:text-white">
                <X className="w-6 h-6" />
              </button>
            </div>
            
            <form onSubmit={handleSubmit} className="p-6 space-y-4">
              <div className="grid grid-cols-2 gap-4">
                <div className="space-y-2">
                  <label className="text-sm font-medium text-slate-400">Nome Cluster</label>
                  <input required type="text" placeholder="Es. PVE-Prod" 
                    className="w-full bg-slate-900 border border-slate-700 rounded-lg px-4 py-2 focus:ring-2 focus:ring-blue-500 outline-none"
                    value={formData.name} onChange={e => setFormData({...formData, name: e.target.value})} />
                </div>
                <div className="space-y-2">
                  <label className="text-sm font-medium text-slate-400">IP / Hostname</label>
                  <input required type="text" placeholder="192.168.1.100" 
                    className="w-full bg-slate-900 border border-slate-700 rounded-lg px-4 py-2 focus:ring-2 focus:ring-blue-500 outline-none"
                    value={formData.host} onChange={e => setFormData({...formData, host: e.target.value})} />
                </div>
              </div>

              <div className="space-y-2">
                <label className="text-sm font-medium text-slate-400">Auth User (Token ID)</label>
                <input required type="text" placeholder="root@pam!MYTOKEN" 
                  className="w-full bg-slate-900 border border-slate-700 rounded-lg px-4 py-2 focus:ring-2 focus:ring-blue-500 outline-none"
                  value={formData.auth_user} onChange={e => setFormData({...formData, auth_user: e.target.value})} />
              </div>

              <div className="space-y-2">
                <label className="text-sm font-medium text-slate-400">Auth Token (Secret)</label>
                <input required type="password" placeholder="••••••••••••••••" 
                  className="w-full bg-slate-900 border border-slate-700 rounded-lg px-4 py-2 focus:ring-2 focus:ring-blue-500 outline-none"
                  value={formData.auth_token} onChange={e => setFormData({...formData, auth_token: e.target.value})} />
              </div>

              <div className="flex items-center gap-6 pt-2">
                <label className="flex items-center gap-2 cursor-pointer group">
                  <input type="checkbox" className="hidden" 
                    checked={formData.verify_ssl} onChange={e => setFormData({...formData, verify_ssl: e.target.checked})} />
                  <div className={`w-10 h-6 rounded-full transition-colors relative ${formData.verify_ssl ? 'bg-green-600' : 'bg-slate-700'}`}>
                    <div className={`absolute top-1 w-4 h-4 bg-white rounded-full transition-all ${formData.verify_ssl ? 'left-5' : 'left-1'}`}></div>
                  </div>
                  <span className="text-sm text-slate-400 group-hover:text-slate-200 flex items-center gap-1">
                    {formData.verify_ssl ? <Shield className="w-4 h-4 text-green-400" /> : <ShieldOff className="w-4 h-4" />} 
                    Verify SSL
                  </span>
                </label>
              </div>

              <div className="pt-4">
                <button 
                  disabled={loading}
                  type="submit" 
                  className="w-full bg-blue-600 hover:bg-blue-500 disabled:bg-blue-800 disabled:text-slate-400 text-white font-bold py-3 rounded-lg transition-all flex items-center justify-center gap-2"
                >
                  {loading ? <Loader2 className="w-5 h-5 animate-spin" /> : <Plus className="w-5 h-5" />}
                  Registra Server
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}

export default App;
