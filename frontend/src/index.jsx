import React from 'react'
import ReactDOM from 'react-dom/client'
import { AddonProvider } from '@ynput/ayon-react-addon-provider'
import '@ynput/ayon-react-components/dist/style.css'
import App from './App'


ReactDOM.createRoot(document.getElementById('root')).render(
  <React.StrictMode>
    <AddonProvider style={{flexDirection: 'row'}}>
      <App />
    </AddonProvider>
  </React.StrictMode>,
)
