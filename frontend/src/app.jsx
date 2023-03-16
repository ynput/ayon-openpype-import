import axios from 'axios'

import { useState, useEffect } from 'react'

import AppWrapper from './components/AppWrapper'
import SettingsFrontend from './SettingsFrontend'
import context from '/src/context'


const ProjectFrontend = () => {
  return (
    <AppWrapper>
      Executed frontend from the project scope, which does not make sense.
      This is just for testing and will never be executed.
    </AppWrapper>
  )
}

const App = () => {
  const [addonContext, setAddonContext] = useState(null)

  useEffect(() => {
    const handleMessage = (event) => {
      setAddonContext(event.data)
      const accessToken = event.data.accessToken
      axios.defaults.headers.common['Authorization'] = `Bearer ${accessToken}`
      context.addonName = event.data.addonName
      context.addonVersion = event.data.addonVersion
    }
    window.addEventListener("message", handleMessage, false)
    return () => {
      window.removeEventListener("message", handleMessage, false)
    }
  }, [])


  if (!addonContext) {
    return "Waiting for addon context..."
  }

  if (addonContext.scope === "project")
    return <ProjectFrontend/>
  else if (addonContext.scope === "settings")
    return <SettingsFrontend/>
  else
    return `Unknown scope: ${JSON.stringify(addonContext.scope || null)}`
}

export default App
