import { useState } from 'react'
import styled from 'styled-components'
import { FormLayout, FormRow, InputText, Button } from '@ynput/ayon-react-components'

import AppWrapper from './components/AppWrapper'
import UploadFile from './components/FileUpload'
import AnatomyPresetDropdown from './components/AnatomyPresetDropdown'


const ImportFormLayout = styled.div`
  display: flex;
  flex-direction: column;
  justify-content: flex-start;
  align-items: center;
  max-width: 800px;
  gap: 2rem;
`

const ImportForm = () => {
  const [files, setFiles] = useState(null)
  const [error, setError] = useState(null)
  const [anatomyPreset, setAnatomyPreset] = useState(null)

 
  return (
    <ImportFormLayout>
      <UploadFile files={files} setFiles={setFiles} validExtensions={["zip"]}/>
      <FormLayout>
        <FormRow label="Project name">
          <InputText placeholder="(inherit)"/>
        </FormRow>
        <FormRow label="Anatomy preset">
          <AnatomyPresetDropdown value={anatomyPreset} onChange={setAnatomyPreset}/>
        </FormRow>

        <FormRow>
          <Button label="Enqueue" icon="library_add" onClick={() => console.log("Enqueue")} disabled={!files?.length}/>
        </FormRow>
      </FormLayout>
    </ImportFormLayout>
  )


}



const SettingsFrontend = () => {

  return (
    <AppWrapper>
      <ImportForm/>
      <div style={{flex: 1}}>
        here will be table with enqueued files
      </div>
    </AppWrapper>
  )
}


export default SettingsFrontend
