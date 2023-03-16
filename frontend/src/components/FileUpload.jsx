import { useState, useRef, useMemo } from 'react'
import styled from 'styled-components'


const UploadForm = styled.form`
  height: 200px;
  width: 300px;
  text-align: center;
  position: relative;

  input {
    display: none;
  }

  label {
    height: 100%;
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
    gap: 1rem;
    border-width: 2px;
    border-radius: 1rem;
    border-style: dashed;
    border-color: #6b7685;
    background-color: tranaparent;

    &.drag-active {
      background-color: rgba(0,0,0, 0.1);
    }
  }

  span {
    font-size: 1.2rem;
  }

  small {
    color: #e53e3e !important;
    font-size: 0.8rem;
  }

  button {
    cursor: pointer;
    background-color: transparent;
    border: none;
    color: #3182ce;
    font-weight: 600;
    font-size: 1rem;
    
    &:hover {
      text-decoration: underline;
    }
  }

  #drag-file-element {
    position: absolute;
    width: 100%;
    height: 100%;
    border-radius: 1rem;
    top: 0px;
    right: 0px;
    bottom: 0px;
    left: 0px;
  }

  
`



const FileUpload = ({files, setFiles, mode='single', validExtensions=null}) => {
  // Valid modes: single, multiple, sequence

  const [dragActive, setDragActive] = useState(false)
  const [errorMessage, setErrorMessage] = useState(null)
  const inputRef = useRef(null)
  const multiple = mode === 'multiple' || mode === 'sequence'
  
  // handles the drag events
  const handleDrag = (e) => {
    e.preventDefault()
    e.stopPropagation()
    if (e.type === "dragenter" || e.type === "dragover") {
      setDragActive(true)
    } else if (e.type === "dragleave") {
      setDragActive(false)
    }
  }

  const handleFiles = (files) => {
    const acceptedFiles = []
  
    for (const file of files) {
      if (validExtensions){
        const extension = file.name.split('.').pop()
        if (!validExtensions.includes(extension)){
          setErrorMessage(`Invalid file type: ${extension}`)
          return
        }
      }

      if (mode === 'sequence'){
        // TODO: Handle sequence validation
      }

      acceptedFiles.push(file)
      if(!multiple){
        break
      }
    }
    setErrorMessage(null)
    setFiles(acceptedFiles)
  }
  
  // triggers when file is dropped
  const handleDrop = (e) =>  {
    e.preventDefault()
    e.stopPropagation()
    setDragActive(false)
    if (e.dataTransfer.files && e.dataTransfer.files[0]) {
      handleFiles(e.dataTransfer.files);
    }
  };
  
  // triggers when file is selected with click
  const handleChange = (e) => {
    e.preventDefault()
    if (e.target.files && e.target.files[0]) {
      handleFiles(e.target.files);
    }
  };
  
  // triggers the input when the button is clicked
  const onButtonClick = () => {
    inputRef.current.click()
  };

  const formContents = useMemo(() => {
    if (files?.length){
      return (
        <>
          <span>{files.length} files selected</span>
          <button onClick={() => setFiles([])}>clear</button>
        </>
      )
    } else {
      return (
        <>
          <span>Drag and drop your file here or</span>
          <button className="upload-button" onClick={onButtonClick}>upload a file</button>
          <small>{errorMessage}</small>
        </>
      )
    }

  }, [files, errorMessage])

  
  return (
    <UploadForm onDragEnter={handleDrag} onSubmit={(e) => e.preventDefault()}>
      <input 
        ref={inputRef} 
        type="file" 
        id="input-file-upload" 
        multiple={multiple}
        onChange={handleChange} 
      />
      
      <label 
        id="label-file-upload" 
        htmlFor="input-file-upload" 
        className={dragActive ? "drag-active" : "" }
      >
        {formContents}
      </label>

      {dragActive && (
        <div 
          id="drag-file-element" 
          onDragEnter={handleDrag} 
          onDragLeave={handleDrag} 
          onDragOver={handleDrag} 
          onDrop={handleDrop}
        />
      )}
    </UploadForm>
  );
}


export default FileUpload

