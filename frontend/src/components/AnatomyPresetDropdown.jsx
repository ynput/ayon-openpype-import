import axios from 'axios'

import { useState, useEffect } from 'react'
import { Dropdown } from 'primereact/dropdown'


const DEFAULT = {
  name: "_",
  title: "Default"
}

const AnatomyPresetDropdown = ({ value, onChange }) => {
  const [loading, setLoading] = useState(true)
  const [presetList, setPresetList] = useState([DEFAULT])


  useEffect(() => {
    axios
      .get('/api/anatomy/presets')
      .then((response) => {
        let result = [DEFAULT]
        for (const pst of response.data.presets){
          let title = pst.name
          if (pst.primary)
            title += " (PRIMARY)"
          result.push({name: pst.name, title})
        }
        setPresetList(result)
      })
      .catch((error) => {
        console.log(error)
      })
      .finally(() => {
        setLoading(false)
      })
  }, [])


  return (
    <Dropdown
      disabled={loading}
      value={value || "_"}
      onChange={(e) => onChange(e.value)}
      options={presetList}
      optionValue="name"
      optionLabel="title"
      tooltip="Preset"
      tooltipOptions={{ position: 'bottom' }}
      style={{ minWidth: 200 }}
    />
  )
}

export default AnatomyPresetDropdown
