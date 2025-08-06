import Versions from './components/Versions'
import electronLogo from './assets/electron.svg'
import { IconGithubLogo } from '@douyinfe/semi-icons'
import { IconElectron } from './components/IconElectron'

function App(): React.JSX.Element {
  const ipcHandle = (): void => window.electron.ipcRenderer.send('ping')

  return (
    <div
      style={{
        height: '100vh',
        backgroundColor: 'var(--semi-color-bg-0)',
        display: 'flex',
        flexDirection: 'column',
      }}
    >
      <div
        style={{
          display: 'flex',
          alignItems: 'center',
          padding: '0 24px',
          backgroundColor: 'var(--semi-color-bg-1)',
          borderBottom: '1px solid var(--semi-color-border)',
        }}
      >
        <div
          style={{
            display: 'flex',
            alignItems: 'center',
            gap: '16px',
          }}
        >
          <img width={32} height={32} src={electronLogo} alt="logo" />
          <h4 style={{ color: 'var(--semi-color-primary)', margin: 0 }}>ZSim Electron App</h4>
        </div>
      </div>

      <div
        style={{
          display: 'flex',
          flexDirection: 'column',
          alignItems: 'center',
          justifyContent: 'center',
          padding: '48px',
          flex: 1,
        }}
      >
        <div
          style={{
            display: 'flex',
            flexDirection: 'column',
            alignItems: 'center',
            gap: '24px',
          }}
        >
          <h2>Welcome to Electron + React + Semi UI</h2>
          <p style={{ fontSize: '18px', color: 'var(--semi-color-text-2)' }}>
            Build an Electron app with{' '}
            <span style={{ color: 'var(--semi-color-primary)', fontWeight: 'bold' }}>React</span>{' '}
            and{' '}
            <span style={{ color: 'var(--semi-color-primary)', fontWeight: 'bold' }}>
              TypeScript
            </span>
          </p>
          <p style={{ color: 'var(--semi-color-text-3)' }}>
            Please try pressing <code>F12</code> to open the devTool
          </p>

          <div
            style={{
              width: 400,
              marginTop: 24,
              padding: '24px',
              border: '1px solid var(--semi-color-border)',
              borderRadius: 'var(--semi-border-radius-medium)',
            }}
          >
            <h3 style={{ marginTop: 0, marginBottom: '24px' }}>Quick Actions</h3>
            <div
              style={{
                display: 'flex',
                flexDirection: 'column',
                alignItems: 'center',
                gap: '16px',
              }}
            >
              <button
                style={{
                  backgroundColor: 'var(--semi-color-primary)',
                  color: 'white',
                  border: 'none',
                  padding: '10px 20px',
                  borderRadius: 'var(--semi-border-radius-medium)',
                  cursor: 'pointer',
                  display: 'flex',
                  alignItems: 'center',
                  gap: '8px',
                  fontSize: '14px',
                }}
                onClick={() => window.open('https://electron-vite.org/', '_blank')}
              >
                <IconGithubLogo />
                Documentation
              </button>
              <button
                style={{
                  backgroundColor: 'var(--semi-color-bg-2)',
                  color: 'var(--semi-color-text-1)',
                  border: '1px solid var(--semi-color-border)',
                  padding: '10px 20px',
                  borderRadius: 'var(--semi-border-radius-medium)',
                  cursor: 'pointer',
                  display: 'flex',
                  alignItems: 'center',
                  gap: '8px',
                  fontSize: '14px',
                }}
                onClick={ipcHandle}
              >
                <IconElectron />
                Send IPC
              </button>
            </div>
          </div>

          <Versions />
        </div>
      </div>

      <div
        style={{
          textAlign: 'center',
          padding: '16px',
          backgroundColor: 'var(--semi-color-bg-1)',
          borderTop: '1px solid var(--semi-color-border)',
        }}
      >
        <p style={{ color: 'var(--semi-color-text-3)', margin: 0 }}>Powered by electron-vite</p>
      </div>
    </div>
  )
}

export default App
