import axios from 'axios'

import {useState, useEffect} from 'react'

import { Section, TablePanel } from '@ynput/ayon-react-components'
import { DataTable } from 'primereact/datatable'
import { Column } from 'primereact/column'
import InlineSpinner from './components/InlineSpinner'

const StatusTable = () => {
  const [events, setEvents] = useState([])

  const loadEvents = () => {
    // run graphql query to get all events
    axios.post('/graphql', {
      query: `
        query {
          events(topics: ["openpype_import.*"] last: 100) {
            edges {
              node {
                id
                topic
                createdAt
                updatedAt
                description
                project
                user
                summary
                status
              }
            }
          }
        }
      `

    })
    .then((response) => {
      const events = response.data.data.events.edges.map((edge) => {
          return {
            id: edge.node.id,
            topic: edge.node.topic,
            description: edge.node.description,
            status: edge.node.status,
            project: edge.node.project,
            user: edge.node.user,
            createdAt: edge.node.createdAt,
            updatedAt: edge.node.updatedAt,
            ...JSON.parse(edge.node.summary),
          }
        })
      setEvents(events)
    })
    .catch((error) => {
      console.log(error)
    })
    .finally(() => {
      setTimeout(loadEvents, 1000)
    })

  }

  useEffect(() => {
    loadEvents() 
  }, [])

  const statusBodyTemplate = (rowData) => {

    let content = null
    if (['in_progress', 'pending', 'restarted'].includes(rowData.status)) 
      content = <InlineSpinner />
    else if (['failed', 'aborted'].includes(rowData.status))
      content =  <i class="pi pi-cross"></i>
    else
      content = <i class="pi pi-check"></i>

    return (
      <div style={{marginLeft: 8}}>
        {content}
      </div>
    )
  }

  return (
    <Section style={{flexGrow: 1}}>
      <TablePanel>
          <DataTable
            scrollable="true"
            scrollHeight="flex"
            dataKey="name"
            value={events}
            selectionMode="single"
            resizableColumns
          >
            <Column field="id" style={{ width: 30}} body={statusBodyTemplate}/>
            <Column field="description" header="Description" />
            <Column field="project" header="Project" style={{width: 200}}/>
            <Column field="user" header="User" style={{width: 200}}/>
            <Column field="createdAt" header="Created at" style={{width: 300}}/>
          </DataTable>
      </TablePanel>
    </Section>
  )

}


export default StatusTable
