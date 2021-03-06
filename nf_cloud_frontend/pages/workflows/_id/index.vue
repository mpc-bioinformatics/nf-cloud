<template>
    <div>
        <div v-if="workflow && !workflow_not_found">
            <div class="d-flex justify-content-between align-items-center">
                <h1>Workflow "{{ workflow.name }}"</h1>
                <button @click="startWorkflow" :disabled="workflow.is_scheduled" class="btn btn-success btn-sm">
                    Start workflow
                    <i class="fas fa-play"></i>
                </button>
            </div>
            <table class="table">
                <tbody>
                    <tr>
                        <th>ID</th>
                        <td>{{  workflow.id }}</td>
                    </tr>
                    <tr>
                        <th>Name</th>
                        <td>{{  workflow.name }}</td>
                    </tr>
                </tbody>
            </table>
            <div class="d-flex justify-content-end">
                <button @click="deleteWorkflow" type="button" class="btn btn-danger">
                    <i class="fas fa-trash"></i>
                    delete
                </button>
            </div>
            <div v-if="workflow.is_scheduled">
                <h2>Progress</h2>
                <div class="progress">
                    <div class="progress-bar bg-success" role="progressbar" :style="progress_bar_style"></div>
                </div>
            </div>
            <h2>Nextflow Workflow</h2>
            <div class="dropdown mb-3">
                <button :class="{show: show_nextflow_workflow_dropdown}" :aria_expanded="show_nextflow_workflow_dropdown" @click="toggleNextflowWorkflowDropdown" class="btn btn-primary" type="button" id="nextflow-workflow-dropdown" data-bs-toggle="dropdown">
                    <span v-if="workflow.nextflow_workflow">{{workflow.nextflow_workflow}}</span>
                    <span v-else>Select a workflow...</span>
                    <i :class="{'fa-caret-down': !show_nextflow_workflow_dropdown, 'fa-caret-up': show_nextflow_workflow_dropdown}" class="fas ms-2"></i>
                </button>
                <ul :class="{show: show_nextflow_workflow_dropdown}" class="dropdown-menu" aria-labelledby="nextflow-workflow-dropdown">
                    <li v-for="nf_workflow in nextflow_workflows" :key="nf_workflow" :value="nf_workflow">
                        <button @click="setNextflowWorkflow(nf_workflow); toggleNextflowWorkflowDropdown();" type="button" class="btn btn-link text-decoration-none text-body">
                            {{nf_workflow}}
                        </button>
                    </li>
                </ul>
                
            </div>
            <h2 class="mb-0">Nextflow parameters</h2>
            <template v-for="(argument_value, argument_name) in workflow.nextflow_arguments">
                <div :key="argument_name">
                    <PathSelector 
                        v-if="argument_value.type == 'path'" 
                        :label="argument_name" 
                        :description="argument_value.desc"
                        :initial_value="workflow.nextflow_arguments[argument_name].value"
                        :parent_event_bus="local_event_bus"
                        :value_change_event="argument_changed_event"
                        :workflow_id="workflow.id"
                        :with_selectable_files="argument_value.selectable_files"
                        :with_selectable_folders="argument_value.selectable_folders"
                    ></PathSelector>
                    <MultiplePathSelector 
                        v-if="argument_value.type == 'paths'" 
                        :label="argument_name"
                        :description="argument_value.desc"
                        :initial_value="workflow.nextflow_arguments[argument_name].value"
                        :parent_event_bus="local_event_bus"
                        :value_change_event="argument_changed_event" 
                        :available_files="workflow.files"
                        :workflow_id="workflow.id"
                        :with_selectable_files="argument_value.selectable_files"
                        :with_selectable_folders="argument_value.selectable_folders"
                    ></MultiplePathSelector>
                    <TextInput v-if="argument_value.type == 'text'" :label="argument_name" :description="argument_value.desc" :initial_value="workflow.nextflow_arguments[argument_name].value" :parent_event_bus="local_event_bus" :value_change_event="argument_changed_event" :is_multiline="workflow.nextflow_arguments[argument_name].is_multiline"></TextInput>
                    <NumberInput v-if="argument_value.type == 'number'" :label="argument_name" :description="argument_value.desc" :initial_value="workflow.nextflow_arguments[argument_name].value" :parent_event_bus="local_event_bus" :value_change_event="argument_changed_event"></NumberInput>
                    <FileGlob v-if="argument_value.type == 'file-glob'" :label="argument_name" :description="argument_value.desc" :initial_value="workflow.nextflow_arguments[argument_name].value" :parent_event_bus="local_event_bus" :value_change_event="argument_changed_event"></FileGlob>
                </div>
            </template>
            <button @click="updateWorkflow" type="button" class="btn btn-primary mb-3">
                <i class="fas fa-save me-2"></i>
                save
            </button>
            <h2>Files</h2>
            <EditableFileBrowser 
                :workflow_id="workflow.id"
                :parent_event_bus="local_event_bus"
                :reload_event="this.reload_workflow_files_event"
            ></EditableFileBrowser>
        </div>
        <div v-if="!workflow && workflow_not_found">
            Workflow not found
        </div>
    </div>
</template>

<script>
import Vue from "vue"
import socket from '~/plugins/socket.io.js'

const RELOAD_WORKFLOW_FILES_EVENT = "RELOAD_WORKFLOW_FILES"

/**
 * Event name for argument changes.
 */
const ARGUMENT_CHANGED_EVENT = "ARGUMENT_CHANGED"

export default {
    data(){
        return {
            workflow: null,
            upload_queue: [],
            is_uploading: false,
            workflow_not_found: false,
            nextflow_workflows: [],
            show_nextflow_workflow_dropdown: false,
            /**
             * Event bus for communication with child components.
             */
            local_event_bus: new Vue(),
            logs: []
        }
    },
    mounted(){
        this.loadWorkflow()
        this.getNextflowWorkflows()
        this.bindNextflowArgumentChangeEvent()
    },
    deactivated(){
        this.disconnectFromWorkflowSocketIoRoom()
    },
    methods: {
        loadWorkflow(){
            this.disconnectFromWorkflowSocketIoRoom()
            return fetch(`${this.$config.nf_cloud_backend_base_url}/api/workflows/${this.$route.params.id}`)
            .then(response => {
                if(response.ok) {
                    response.json().then(response_data => {
                        this.workflow = response_data.workflow
                        this.bindNextflowArgumentChangeEvent()
                        this.connectToWorkflowSocketIoRoom()
                    })
                } else if(response.status == 404) {
                    this.workflow_not_found = true
                } else {
                    this.handleUnknownResponse(response)
                }
            })
        },
        deleteWorkflow(){
            return fetch(`${this.$config.nf_cloud_backend_base_url}/api/workflows/${this.$route.params.id}/delete`, {
                method: "POST"
            }).then(response => {
                if(response.ok || response.status == 404) {
                    this.$router.push({name: "workflows"})
                } else {
                    this.handleUnknownResponse(response)
                }
            })
        },
        startWorkflow(){
            fetch(`${this.$config.nf_cloud_backend_base_url}/api/workflows/${this.$route.params.id}/schedule`, {
                method:'POST',
            }).then(response => {
                if(response.ok) {
                    return response.json().then(response_data => {
                        this.workflow.is_scheduled = response_data.is_scheduled
                    })
                } else {
                    this.handleUnknownResponse(response)
                }
            })
        },
        updateWorkflow(){
            fetch(`${this.$config.nf_cloud_backend_base_url}/api/workflows/${this.$route.params.id}/update`, {
                method:'POST',
                headers: {
                    "Content-Type": "application/json"
                },
                body: JSON.stringify({
                    nextflow_arguments: this.workflow.nextflow_arguments,
                    nextflow_workflow: this.workflow.nextflow_workflow,
                })
            }).then(response => {
                if(!response.ok) {
                    this.handleUnknownResponse(response)
                }
            })
        },
        getNextflowWorkflows(){
            fetch(`${this.$config.nf_cloud_backend_base_url}/api/nextflow-workflows`, {
            }).then(response => {
                if(response.ok) {
                    response.json().then(data => {
                        this.nextflow_workflows = data.nextflow_workflows
                    })
                } else {
                    this.handleUnknownResponse(response)
                }
            })
        },
        toggleNextflowWorkflowDropdown(){
            this.show_nextflow_workflow_dropdown = !this.show_nextflow_workflow_dropdown
        },
        setNextflowWorkflow(nextflow_workflow){
            this.workflow.nextflow_workflow = nextflow_workflow
            this.getDynamicNextflowArguments()
        },
        /**
         * Sets a nee value to the nextflow argument
         * 
         * @param {string} argument_name
         * @param {any} argument_value
         */
        setNextflowArgument(argument_name, argument_value){
            this.workflow.nextflow_arguments[argument_name].value = argument_value
        },
        /**
         * Binds the argument change event to the local event bus.
         */
        bindNextflowArgumentChangeEvent(){
            this.local_event_bus.$on(
                this.argument_changed_event, 
                (argument_name, new_value) => {this.setNextflowArgument(argument_name, new_value)}
            )
        },
        /**
         * Fetches the dynamic nextflow arguments from the NFCloud
         * and assigns it to the workflow.
         */
        getDynamicNextflowArguments(){
            fetch(`${this.$config.nf_cloud_backend_base_url}/api/nextflow-workflows/${this.workflow.nextflow_workflow}/arguments`, {
            }).then(response => {
                if(response.ok) {
                    response.json().then(data => {
                        this.workflow.nextflow_arguments = data.arguments
                    })
                } else {
                    this.handleUnknownResponse(response)
                }
            })
        },
        /**
         * Connect to workflow room
         */
        connectToWorkflowSocketIoRoom(){
            socket.emit("join", {"room": `workflow${this.workflow.id}`})
            socket.on("new-nextflow-log", (new_log) => {
                this.workflow.nextflow_log = new_log
                this.logs.push(new_log)
            })
            socket.on("finished-workflow", () => {
                this.workflow.is_scheduled = false
                this.workflow.submitted_processes = 0
                this.workflow.completed_processes = 0
                this.local_event_bus.$emit(this.reload_workflow_files_event)
            })
            socket.on("new-progress", data => {
                console.error(data)
                this.workflow.submitted_processes = data.submitted_processes
                this.workflow.completed_processes = data.completed_processes
            })
        },
        /**
         * Disconnect from workflow room
         */
        disconnectFromWorkflowSocketIoRoom(){
            if(this.workflow != null) socket.emit("leave", {"room": `workflow${this.workflow.id}`});
        }
    },
    computed: {
        /**
         * Returns the argument change event so it is usable in the template.
         * 
         * @returns {string}
         */
        argument_changed_event(){
            return ARGUMENT_CHANGED_EVENT
        },
        /**
         * Returns value for style attribute of progress bar.
         * @return {string}
         */
        progress_bar_style(){
            var progress = this.workflow.completed_processes / this.workflow.submitted_processes * 100
            return `width: ${progress}%`
        },
        /**
         * Provide access to RELOAD_WORKFLOW_FILES_EVENT in vue instance.
         * @return {string}
         */
        reload_workflow_files_event(){
            return RELOAD_WORKFLOW_FILES_EVENT
        }
    }
}
</script>

