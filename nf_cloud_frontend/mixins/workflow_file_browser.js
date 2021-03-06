import Vue from "vue"

export default {
    /**
     * Implements logic for navigating through the workflow work directory.
     */
    props: {
        workflow_id: {
            type: Number,
            required: true
        },
        /**
         * Event bus for communication with parent
         */
        parent_event_bus: {
            type: Vue,
            required: true
        },
        /**
         * Event for reloading folder content.
         */
        reload_event: {
            type: String,
            required: false,
            default: "RELOAD"
        }
    },
    data(){
        return {
            current_directory: "",
            current_directory_folders: [],
            current_directory_files: []
        }
    },
    mounted(){
        this.getFolderContent()
        this.parent_event_bus.$on(this.reload_event, () => { this.getFolderContent() })
    },
    activated(){
        this.getFolderContent()
    },
    methods: {
        moveFolderUp(){
            var position_last_path_segment = this.current_directory.lastIndexOf("/")
            this.current_directory = this.current_directory.slice(0, position_last_path_segment)
        },
        moveIntoFolder(path){
            this.current_directory = `${this.current_directory}/${path}`
        },
        getFolderContent(){
            var url_encoded_path = encodeURIComponent(this.current_directory)
            fetch(`${this.$config.nf_cloud_backend_base_url}/api/workflows/${this.workflow_id}/files?dir=${url_encoded_path}`)
            .then(response => {
                if(response.ok) {
                    return response.json().then(response_data => {
                        this.current_directory_folders = response_data.folders.map(folder => `${folder}/`)
                        this.current_directory_files = response_data.files
                    })
                } else if(response.status == 404) {
                    /**
                     * If folder was not found, move back into parent directory
                     */
                    this.moveFolderUp()
                } else {
                    this.handleUnknownResponse(response)
                }
            })
        },
        /**
         * Concatenates the given path with the current path
         * 
         * @param {String} path 
         * @returns {String}
         */
        getFullPath(path){
            return `${this.current_directory}${path}`
        }
    },
    watch: {
        current_directory(){
            this.getFolderContent()
        }
    }
}