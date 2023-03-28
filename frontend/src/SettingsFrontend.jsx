import axios from 'axios'
import styled from 'styled-components'

import { useState, useEffect, useMemo } from 'react'
import { FormLayout, FormRow, Panel, Section, Button, FileUpload } from '@ynput/ayon-react-components'
import { Dialog } from 'primereact/dialog'

import AppWrapper from './components/AppWrapper'
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

const ProcessDialog = ({files, fileIndex, fileProgress, overalProgress, errors, onHide}) => {

  const handleOnHide = () => {
    if (!message)
      return
    onHide()
  }

  const errorsComponent = useMemo(() => {
    return (
    <ul>
    {(errors || []).map((error) => (
      <li key={error}>{error}</li>
    ))}
    </ul>)
  }, [errors])


  const currentFileName = files[fileIndex]?.name

  return (
    <Dialog 
      visible 
      header="Project import"
      onHide={handleOnHide} 
      style={{minWidth: 400, mihHeight: 300}}
    >


      <p className={errors?.length ? 'error' : ''}>
        Importing {currentFileName} ({ fileIndex + 1 }/{files.length})
        <Progress value={fileProgress || 0} />
      </p>

      <p>
        <Progress value={overalProgress || 0} />
      </p>

      {errorsComponent}


    </Dialog>
  )
}


const ImportForm = () => {
  const [files, setFiles] = useState(null)
  const [processState, setProcessState] = useState(null)
  
  const abortController = new AbortController()
  const cancelToken = axios.CancelToken
  const cancelTokenSource = cancelToken.source()


  const handleProgress = (e) => {

    setProcessState((processState) => {
        const totalSize = files.reduce((acc, file) => acc + file.size, 0)
        const processedFiles = processState.fileIndex ? files.slice(0, processState.fileIndex) : []
        const processedFilesSize = processedFiles.reduce((acc, file) => acc + file.size, 0)
        const fileProgress = Math.round((e.loaded * 100) / e.total)
        const overalProgress = Math.round(((processedFilesSize + fileProgress) * 100) / totalSize)

        return {
          ...processState,
          fileProgress,
          overalProgress,
        }
    })
  }

  const onSubmit = async () => {
    setProcessState({
      files,
      fileIndex: 0,
      message: 0,
      overalProgress: 0,
      errors: [],
    })

    const url = `/api/addons/${context.addonName}/${context.addonVersion}/import`


    for (const file of files) {

      await axios
        .post(url, files[0], {
          signal: abortController.signal,
          cancelToken: cancelTokenSource.token,
          onUploadProgress: handleProgress,
          headers: {
            'Content-Type': 'application/octet-stream',
            'X-Ayon-Project-Name': file.name,
          },
        }) 

      setProcessState((processState) => {

        return {
          ...processState,
          fileIndex: processState.fileIndex + 1,
        }

      })


    } // for files
    setProcessState(null)
    setFiles(null)

  }
 
  return (
    <Section style={{maxWidth: 400}}>
      <Panel style={{alignItems: "center", gap: 16}}>
      <FileUpload files={files} setFiles={setFiles} validExtensions={["zip"]} mode='multiple'/>
      {processState && <ProcessDialog {...processState} onHide={()=>setProcessState(null)}/> }
      <FormLayout>
        <FormRow>
          <Button 
            label="Import" 
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
          Import a database dump from OpenPype 3. Deployment to Ayon will be handled by a background process
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
