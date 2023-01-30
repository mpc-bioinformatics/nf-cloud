# external imports
from ast import List
from collections import defaultdict
from typing import Any, Dict, Optional
from flask import Flask, jsonify, request
import json

# internal imports
from nf_cloud_backend import app
from nf_cloud_backend.models.workflow import Workflow


class WorkflowsControllers:
    """
    Handles requests regarding the defined nextflow workflows
    """

    @staticmethod
    @app.route("/api/workflows", endpoint="workflow_index")
    def index():
        """
        Returns
        -------
        JSON with key `workflows`, which contains a list of workflow names.
        """
        offset = request.args.get("offset", None)
        limit = request.args.get("limit", None)
        return jsonify({
            "workflows": [
                workflow.to_dict()
                for workflow in Workflow.select().offset(offset).limit(limit)
            ]
        })

    @staticmethod
    @app.route("/api/workflows/published", endpoint="workflow_index_published")
    def index_published():
        """
        Returns
        -------
        JSON with key `workflows`, which contains a list of workflow names.
        """
        offset = request.args.get("offset", None)
        limit = request.args.get("limit", None)
        return jsonify({
            "workflows": [
                workflow.to_dict()
                for workflow in Workflow.select().where(Workflow.is_published == True).offset(offset).limit(limit)
            ]
        })

    @staticmethod
    @app.route("/api/workflows/create", methods=["POST"], endpoint="workflow_create")
    def create():
        """
        Endpoint for creating a workflow.
        Returns
        -------
        Response
            200 - on success
            422 - on errors
        Raises
        ------
        RuntimeError
            Workflow cannot be inserted.
        """
        errors: Dict[str, List[Any]] = defaultdict(list)
        error_status_code: int = 422

        data: Dict[str, Any] = request.json
        name: Optional[str] = data.get("name", None)
        if name is not None:
            if len(name) < 1:
                errors["name"].append("Input too short")
            if len(name) > 512:
                errors["name"].append("Input too long")
        else:
            errors["name"].append("Input is missing")

        if len(errors) > 0:
            return jsonify({
                "errors": errors
            }), error_status_code

        workflow: Workflow = Workflow.create(name=name, description=data.get("description", None))
        return jsonify(workflow.to_dict())

    @staticmethod
    @app.route("/api/workflows/<int:workflow_id>", endpoint="workflow_show")
    def show(workflow_id: int):
        """
        Endpoint for creating a workflow.
        Returns
        -------
        Response
            200 - on success
            422 - on errors
        Raises
        ------
        RuntimeError
            Workflow cannot be inserted.
        """
        workflow: Workflow = Workflow.get(Workflow.id == workflow_id)
        return jsonify(workflow.to_dict())

    @staticmethod
    @app.route("/api/workflows/<int:workflow_id>/update", methods=["POST"], endpoint="workflow_update")
    def update(workflow_id: int):
        """
        Endpoint for updating a workflow.
        Returns
        -------
        Response
            200 - on success
            422 - on errors
        Raises
        ------
        RuntimeError
            Workflow cannot be inserted.
        """
        data: Dict[str, Any] = request.json
        definition: Optional[str] = data.get("definition", None)
        description: Optional[str] = data.get("description", None)
        is_published: Optional[bool] = data.get("is_published", None)
        app.logger.error(definition)

        workflow: Workflow = Workflow.get(Workflow.id == workflow_id)
        workflow.definition = definition
        workflow.description = description
        workflow.is_published = is_published

        try:
                json_obj = json.loads(workflow.definition)
                print("JSON is valid")
        except ValueError as e:
                print("JSON is invalid. Reason:")
                print(e)
        workflow.save()

        return "", 200

    @staticmethod
    @app.route("/api/workflows/<int:workflow_id>/delete", methods=["POST"], endpoint="workflow_delete")
    def delete(workflow_id: int):
        """
        Endpoint for deleteing a workflow.
        Returns
        -------
        Response
            200 - on success
            422 - on errors
        Raises
        ------
        RuntimeError
            Workflow cannot be delete.
        """

        workflow: Workflow = Workflow.get(Workflow.id == workflow_id)
        workflow.delete_instance()

        return "", 200