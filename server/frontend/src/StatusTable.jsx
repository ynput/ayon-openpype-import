import axios from 'axios'
import styled from 'styled-components'

import {useState, useEffect, useContext} from 'react'

import { Section, TablePanel, Button } from '@ynput/ayon-react-components'
import { DataTable } from 'primereact/datatable'
import { Column } from 'primereact/column'
import InlineSpinner from './components/InlineSpinner'
import { AddonContext } from '@ynput/ayon-react-addon-provider'


const CellIcon = ({icon}) => (
  <span className={`material-symbols-outlined`} >
    {icon}
  </span>
)

const statusBodyTemplate = (rowData) => {
  if (rowData.status === 'finished') return <CellIcon icon="check" />
  if (rowData.status === 'aborted') return <CellIcon icon="times" />
  if (rowData.status === 'failed') return <CellIcon icon="error" />
  if (rowData.status === 'in_progress') return <InlineSpinner />
  if (rowData.status === 'pending') return <CellIcon icon="timer" />
  if (rowData.status === 'restarted') return <CellIcon icon="history" />
}

const DateTimeContainer = styled.div`
  display: flex;
  flex-direction: row;
  gap: 8px;
  align-items: center;
  > span:first-child {
    color: var(--color-text-dim);
  }
`

const isoToTime = (isoTime) => {
  if (!isoTime) return ['-', '-']
  const date = new Date(isoTime)
  const year = date.getFullYear()
  const month = String(date.getMonth() + 1).padStart(2, '0')
  const day = String(date.getDate()).padStart(2, '0')
  const hours = String(date.getHours()).padStart(2, '0')
  const minutes = String(date.getMinutes()).padStart(2, '0')
  const seconds = String(date.getSeconds()).padStart(2, '0')
  return [`${day}-${month}-${year}`, `${hours}:${minutes}:${seconds}`]
}

const formatTimestamp = (rowData) => {
  if (!rowData?.updatedAt) return ''
  const [dd, tt] = isoToTime(rowData.updatedAt)
  return (
    <DateTimeContainer>
      <span>{dd}</span>
      <span>{tt}</span>
    </DateTimeContainer>
  )
}

const StatusTable = () => {
  const [events, setEvents] = useState([])
  const addonName = useContext(AddonContext).addonName
  const addonVersion = useContext(AddonContext).addonVersion
  const url = `/api/addons/${addonName}/${addonVersion}/list`
  const loadEvents = () => {
    axios
    .get(url)
    .then((response) => {
      const events = response.data
      setEvents(events)
    })
    .catch((error) => {
      console.log(error)
    })
    .finally(() => {
      setTimeout(loadEvents, 2000)
    })

  }

  useEffect(() => {
    loadEvents() 
  }, [])

  const restartEvent = (processId) => () => {
    axios
      .patch(`/api/events/${processId}`, {status: 'restarted'})
      .then(() => loadEvents())
      .catch((error) => {console.log(error)})
  }

  const restartButtonTemplate = (rowData) => {
    if (!rowData.processId) return null
    if (!['finished', 'failed', 'aborted'].includes(rowData.status)) return null

    return (
      <Button link onClick={restartEvent(rowData.processId)} label="Restart"/>
    )
  }


  return (
    <Section style={{flexGrow: 1}}>
      <TablePanel>
          <DataTable
            scrollable="true"
            scrollHeight="flex"
            dataKey="id"
            value={events}
            selectionMode="single"
            columnResizeMode="fit"
          >
            <Column field="id" style={{ width: 25}} body={statusBodyTemplate}/>
            <Column field="description" header="Description" style={{width: 450}}/>
            <Column field="project" header="Project" style={{width: 200}}/>
            <Column field="user" header="User" style={{width: 200}}/>
            <Column field="updatedAt" header="Created at" style={{width: 150}} body={formatTimestamp}/>
            <Column body={restartButtonTemplate} style={{width: 50}}/>
          </DataTable>
      </TablePanel>
    </Section>
  )

}


export default StatusTable
