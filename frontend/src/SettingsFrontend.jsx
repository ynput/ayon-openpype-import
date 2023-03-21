import axios from 'axios'
import styled from 'styled-components'

import { useState, useEffect } from 'react'
import { FormLayout, FormRow, InputText, Button } from '@ynput/ayon-react-components'
import { Dialog } from 'primereact/dialog'

import AppWrapper from './components/AppWrapper'
import UploadFile from './components/FileUpload'
import AnatomyPresetDropdown from './components/AnatomyPresetDropdown'
import StatusTable from './StatusTable'
import context from './context'


const ImportFormLayout = styled.div`
  display: flex;
  flex-direction: column;
  justify-content: flex-start;
  align-items: center;
  max-width: 800px;
  gap: 2rem;
`


const BaseProgress = styled.div`
  width: 100%;
  border: 0;
  border-radius: 3px;
  background: #252525;
  height: 10px;

  div {
    height: 100%;
    background: #3182ce;
  }
`

const Progress = ({ value, ...props }) => {
  return (
    <BaseProgress {...props}>
      <div style={{ width: `${value}%` }} />
    </BaseProgress>
  )
}

const formatFileSize = (bytes) => {
  if (bytes < 1024) return `${bytes} B`
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(2)} KB`
  if (bytes < 1024 * 1024 * 1024)
    return `${(bytes / 1024 / 1024).toFixed(2)} MB`
  return `${(bytes / 1024 / 1024 / 1024).toFixed(2)} GB`
}

const ProcessDialog = ({projectName, progress, message, isError, onHide}) => {

  const handleOnHide = () => {
    if (!message)
      return
    onHide()
  }

  return (
    <Dialog visible onHide={handleOnHide}>
      <h2>Importing project</h2>

      <p className={isError ? 'error' : ''}>
        {message || `Importing project ${projectName}...`}
      </p>

      <Progress value={progress || 0} />
    </Dialog>
  )
}


const ImportForm = () => {
  const [files, setFiles] = useState(null)
  const [projectName, setProjectName] = useState('')
  const [anatomyPreset, setAnatomyPreset] = useState('_')
  const [processState, setProcessState] = useState(null)
  
  const abortController = new AbortController()
  const cancelToken = axios.CancelToken
  const cancelTokenSource = cancelToken.source()


  useEffect(() => {
    if (!projectName){
      const fileName = files?.[0]?.name
      if (fileName)
        setProjectName(fileName.split('.').slice(0, -1).join('.'))
    }
  }, [files])

  const handleProgress = (e) => {
    setProcessState(() => ({
      ...processState,
      progress: Math.round((e.loaded * 100) / e.total),
    }))
  }

  const onSubmit = async () => {
    setProcessState({
      projectName,
      progress:0,
      message: null,
      isError: false,
    })

    const url = `/api/addons/${context.addonName}/${context.addonVersion}/import`
    await axios
      .post(url, files[0], {
        signal: abortController.signal,
        cancelToken: cancelTokenSource.token,
        onUploadProgress: handleProgress,
        headers: {
          'Content-Type': 'application/octet-stream',
          'X-Ayon-Project-Name': projectName,
          'X-Ayon-Anatomy-Preset': anatomyPreset,
        },
      }) 
      .then(() => {
        setProcessState({
          projectName,
          progress: 100,
          message: 'Project imported successfully',
          isError: false,
        })
      })
      .catch((err) => {
        console.error(err)
        setProcessState({
          projectName,
          progress: 100,
          message: 'Project import failed',
          isError: true,
        })
      })
  }
 
  return (
    <ImportFormLayout>
      <UploadFile files={files} setFiles={setFiles} validExtensions={["zip"]}/>
      {processState && <ProcessDialog {...processState} onHide={()=>setProcessState(null)}/> }
      <FormLayout>
        <FormRow label="Anatomy preset">
          <AnatomyPresetDropdown 
            value={anatomyPreset} 
            onChange={setAnatomyPreset}
          />
        </FormRow>
        <FormRow>
          <Button 
            label="Enqueue" 
            icon="library_add" 
            onClick={onSubmit}
            disabled={!files?.length}
          />
        </FormRow>
      </FormLayout>
      {context.addonName} {context.addonVersion}
    </ImportFormLayout>
  )


}



const SettingsFrontend = () => {

  return (
    <AppWrapper>
      <ImportForm/>
      <StatusTable />
    </AppWrapper>
  )
}


export default SettingsFrontend
