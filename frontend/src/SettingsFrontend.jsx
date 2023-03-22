import axios from 'axios'
import styled from 'styled-components'

import { useState, useEffect } from 'react'
import { FormLayout, FormRow, Panel, Section, Button } from '@ynput/ayon-react-components'
import { Dialog } from 'primereact/dialog'

import AppWrapper from './components/AppWrapper'
import UploadFile from './components/FileUpload'
import AnatomyPresetDropdown from './components/AnatomyPresetDropdown'
import StatusTable from './StatusTable'
import context from './context'


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
    <Dialog visible onHide={handleOnHide} style={{minWidth: 400, mihHeight: 300}}>
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
        setProcessState(null)
        setFiles(null)
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
    <Section style={{maxWidth: 400}}>
      <Panel style={{alignItems: "center", gap: 16}}>
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
      </Panel>

      <Panel style={{ textAlign: "left", flexGrow: 1}}>
        <h2>{context.addonName} {context.addonVersion}</h2>
        <p>
          Upload a database dump from OpenPype 3. Project will be handled by a background process.
        </p>
        <p>
          Database dump must be a zip file containing a JSON file <strong>project.json</strong> and optionally
          a <strong>thumbnails</strong> folder with project thumbnails.
        </p>
        <p>
          At the beginning, name of the file will be used as a project name.
          As soon the dabase is parsed, the project name will be taken from the database.
        </p>
      </Panel>
    </Section>
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
