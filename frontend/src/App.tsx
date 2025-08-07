import reactLogo from 'assets/react.svg'
import PWABadge from './PWABadge.tsx'
import './App.css'

function App() {

  return (
    <>
      <div>
        <a href="https://vite.dev" target="_blank">
                    <img 
            src={reactLogo} 
            className="logo react" 
            alt="Boursa Vision logo" 
          />
        </a>
        <a href="https://react.dev" target="_blank">
          <img src={reactLogo} className="logo react" alt="React logo" />
        </a>
      </div>
      <h1>Boursa Vision</h1>
      <div className="card">
        <h2>Portfolio Management Platform</h2>
        <p>
          Gérez vos investissements avec intelligence et précision
        </p>
        <div style={{ display: 'flex', gap: '1rem', justifyContent: 'center', marginTop: '1rem' }}>
          <button style={{ padding: '0.5rem 1rem', backgroundColor: '#646cff', color: 'white', border: 'none', borderRadius: '4px' }}>
            Voir mes portfolios
          </button>
          <button style={{ padding: '0.5rem 1rem', backgroundColor: '#535bf2', color: 'white', border: 'none', borderRadius: '4px' }}>
            Données du marché
          </button>
        </div>
      </div>
      <p className="read-the-docs">
        Plateforme de gestion d'investissement - Boursa Vision
      </p>
      <PWABadge />
    </>
  )
}

export default App
