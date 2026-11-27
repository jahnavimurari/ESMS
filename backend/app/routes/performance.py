from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, current_user
from marshmallow import ValidationError
from app.middleware.auth_guard import hr_required, admin_required
from app.schemas.performance_schema import (
    performance_cycle_create_schema,
    performance_cycle_update_schema,
    performance_cycle_status_schema,
    performance_review_create_schema,
    self_assessment_update_schema,
    manager_review_schema,
    review_reopen_schema,
)
from app.services.performance_service import PerformanceService

performance_bp = Blueprint("performance", __name__, url_prefix="/api/performance")

# ------------------------------------------------------------------------------
# Performance Cycle Endpoints
# ------------------------------------------------------------------------------
@performance_bp.route("/cycles", methods=["POST"])
@hr_required
def create_cycle():
    """HR or Admin creates a new performance cycle."""
    data = request.get_json(silent=True) or {}
    try:
        validated = performance_cycle_create_schema.load(data)
    except ValidationError as err:
        return jsonify({
            "success": False,
            "error": {"code": "VALIDATION_ERROR", "message": "Invalid cycle data.", "details": err.messages}
        }), 400

    try:
        cycle = PerformanceService.create_cycle(
            creator_user_id=current_user.id,
            data=validated,
            ip_address=request.remote_addr
        )
        return jsonify({
            "success": True,
            "message": "Performance cycle created successfully.",
            "data": cycle
        }), 201
    except ValueError as err:
        return jsonify({
            "success": False,
            "error": {"code": "BAD_REQUEST", "message": str(err)}
        }), 400


@performance_bp.route("/cycles", methods=["GET"])
@jwt_required()
def list_cycles():
    """Lists performance cycles (accessible to all authenticated users)."""
    status = request.args.get("status")
    page = request.args.get("page", 1, type=int)
    per_page = request.args.get("per_page", 20, type=int)

    result = PerformanceService.list_cycles(status=status, page=page, per_page=per_page)
    return jsonify({"success": True, "data": result}), 200


@performance_bp.route("/cycles/<int:cycle_id>", methods=["GET"])
@jwt_required()
def get_cycle(cycle_id):
    """Retrieves single performance cycle details."""
    try:
        cycle = PerformanceService.get_cycle_by_id(cycle_id)
        return jsonify({"success": True, "data": cycle}), 200
    except ValueError as err:
        return jsonify({
            "success": False,
            "error": {"code": "NOT_FOUND", "message": str(err)}
        }), 404


@performance_bp.route("/cycles/<int:cycle_id>", methods=["PUT"])
@hr_required
def update_cycle(cycle_id):
    """HR or Admin updates an existing performance cycle."""
    data = request.get_json(silent=True) or {}
    try:
        validated = performance_cycle_update_schema.load(data)
    except ValidationError as err:
        return jsonify({
            "success": False,
            "error": {"code": "VALIDATION_ERROR", "message": "Invalid update data.", "details": err.messages}
        }), 400

    try:
        cycle = PerformanceService.update_cycle(
            cycle_id=cycle_id,
            data=validated,
            user_id=current_user.id,
            ip_address=request.remote_addr
        )
        return jsonify({
            "success": True,
            "message": "Performance cycle updated successfully.",
            "data": cycle
        }), 200
    except ValueError as err:
        return jsonify({
            "success": False,
            "error": {"code": "BAD_REQUEST", "message": str(err)}
        }), 400


@performance_bp.route("/cycles/<int:cycle_id>/status", methods=["PATCH"])
@hr_required
def update_cycle_status(cycle_id):
    """HR or Admin activates or closes a cycle."""
    data = request.get_json(silent=True) or {}
    try:
        validated = performance_cycle_status_schema.load(data)
    except ValidationError as err:
        return jsonify({
            "success": False,
            "error": {"code": "VALIDATION_ERROR", "message": "Invalid status data.", "details": err.messages}
        }), 400

    try:
        cycle = PerformanceService.update_cycle_status(
            cycle_id=cycle_id,
            status=validated["status"],
            user_id=current_user.id,
            ip_address=request.remote_addr
        )
        return jsonify({
            "success": True,
            "message": f"Cycle status changed to {validated['status']}.",
            "data": cycle
        }), 200
    except ValueError as err:
        return jsonify({
            "success": False,
            "error": {"code": "BAD_REQUEST", "message": str(err)}
        }), 400


# ------------------------------------------------------------------------------
# Performance Review Endpoints
# ------------------------------------------------------------------------------
@performance_bp.route("/reviews", methods=["POST"])
@hr_required
def create_review():
    """HR or Admin initiates a review for an employee in an active cycle."""
    data = request.get_json(silent=True) or {}
    try:
        validated = performance_review_create_schema.load(data)
    except ValidationError as err:
        return jsonify({
            "success": False,
            "error": {"code": "VALIDATION_ERROR", "message": "Invalid review data.", "details": err.messages}
        }), 400

    try:
        review = PerformanceService.create_review(
            creator_user_id=current_user.id,
            data=validated,
            ip_address=request.remote_addr
        )
        return jsonify({
            "success": True,
            "message": "Performance review initiated successfully.",
            "data": review
        }), 201
    except ValueError as err:
        return jsonify({
            "success": False,
            "error": {"code": "BAD_REQUEST", "message": str(err)}
        }), 400


@performance_bp.route("/reviews", methods=["GET"])
@jwt_required()
def list_reviews():
    """Lists reviews. Employees see only their own; HR/Admin see all with filters."""
    filters = {
        "cycle_id": request.args.get("cycle_id", type=int),
        "employee_id": request.args.get("employee_id"),
        "reviewer_id": request.args.get("reviewer_id"),
        "status": request.args.get("status"),
        "department_id": request.args.get("department_id", type=int),
        "search": request.args.get("search"),
    }
    page = request.args.get("page", 1, type=int)
    per_page = request.args.get("per_page", 20, type=int)

    result = PerformanceService.list_reviews(
        user=current_user,
        role=current_user.role,
        filters=filters,
        page=page,
        per_page=per_page
    )
    return jsonify({"success": True, "data": result}), 200


@performance_bp.route("/reviews/<int:review_id>", methods=["GET"])
@jwt_required()
def get_review(review_id):
    """Retrieves single performance review details (strict RBAC)."""
    try:
        review = PerformanceService.get_review_by_id(review_id, current_user, current_user.role)
        return jsonify({"success": True, "data": review}), 200
    except ValueError as err:
        return jsonify({"success": False, "error": {"code": "NOT_FOUND", "message": str(err)}}), 404
    except PermissionError as err:
        return jsonify({"success": False, "error": {"code": "FORBIDDEN", "message": str(err)}}), 403


@performance_bp.route("/reviews/<int:review_id>/self-assessment", methods=["PATCH"])
@jwt_required()
def update_self_assessment(review_id):
    """Employee drafts or updates their self-assessment fields."""
    data = request.get_json(silent=True) or {}
    try:
        validated = self_assessment_update_schema.load(data)
    except ValidationError as err:
        return jsonify({
            "success": False,
            "error": {"code": "VALIDATION_ERROR", "message": "Invalid self-assessment data.", "details": err.messages}
        }), 400

    try:
        review = PerformanceService.update_self_assessment(
            review_id=review_id,
            user=current_user,
            role=current_user.role,
            data=validated,
            ip_address=request.remote_addr
        )
        return jsonify({
            "success": True,
            "message": "Self-assessment saved successfully.",
            "data": review
        }), 200
    except ValueError as err:
        return jsonify({"success": False, "error": {"code": "BAD_REQUEST", "message": str(err)}}), 400
    except PermissionError as err:
        return jsonify({"success": False, "error": {"code": "FORBIDDEN", "message": str(err)}}), 403


@performance_bp.route("/reviews/<int:review_id>/submit", methods=["PATCH"])
@jwt_required()
def submit_self_assessment(review_id):
    """Employee formally submits self-assessment, advancing status to MANAGER_REVIEW."""
    try:
        review = PerformanceService.submit_self_assessment(
            review_id=review_id,
            user=current_user,
            role=current_user.role,
            ip_address=request.remote_addr
        )
        return jsonify({
            "success": True,
            "message": "Self-assessment submitted successfully. Sent for manager evaluation.",
            "data": review
        }), 200
    except ValueError as err:
        return jsonify({"success": False, "error": {"code": "BAD_REQUEST", "message": str(err)}}), 400
    except PermissionError as err:
        return jsonify({"success": False, "error": {"code": "FORBIDDEN", "message": str(err)}}), 403


@performance_bp.route("/reviews/<int:review_id>/manager-review", methods=["PATCH"])
@jwt_required()
def submit_manager_review(review_id):
    """Reviewer / HR / Admin submits manager rating and feedback."""
    data = request.get_json(silent=True) or {}
    try:
        validated = manager_review_schema.load(data)
    except ValidationError as err:
        return jsonify({
            "success": False,
            "error": {"code": "VALIDATION_ERROR", "message": "Invalid evaluation data.", "details": err.messages}
        }), 400

    try:
        review = PerformanceService.submit_manager_review(
            review_id=review_id,
            reviewer_user=current_user,
            role=current_user.role,
            data=validated,
            ip_address=request.remote_addr
        )
        return jsonify({
            "success": True,
            "message": "Manager evaluation recorded successfully.",
            "data": review
        }), 200
    except ValueError as err:
        return jsonify({"success": False, "error": {"code": "BAD_REQUEST", "message": str(err)}}), 400
    except PermissionError as err:
        return jsonify({"success": False, "error": {"code": "FORBIDDEN", "message": str(err)}}), 403


@performance_bp.route("/reviews/<int:review_id>/complete", methods=["PATCH"])
@jwt_required()
def complete_review(review_id):
    """Reviewer / HR / Admin finalizes review into COMPLETED status."""
    try:
        review = PerformanceService.complete_review(
            review_id=review_id,
            user=current_user,
            role=current_user.role,
            ip_address=request.remote_addr
        )
        return jsonify({
            "success": True,
            "message": "Performance review completed and finalized.",
            "data": review
        }), 200
    except ValueError as err:
        return jsonify({"success": False, "error": {"code": "BAD_REQUEST", "message": str(err)}}), 400
    except PermissionError as err:
        return jsonify({"success": False, "error": {"code": "FORBIDDEN", "message": str(err)}}), 403


@performance_bp.route("/reviews/<int:review_id>/reopen", methods=["PATCH"])
@hr_required
def reopen_review(review_id):
    """HR or Admin reopens a COMPLETED review with justification reason."""
    data = request.get_json(silent=True) or {}
    try:
        validated = review_reopen_schema.load(data)
    except ValidationError as err:
        return jsonify({
            "success": False,
            "error": {"code": "VALIDATION_ERROR", "message": "Invalid reopen request.", "details": err.messages}
        }), 400

    try:
        review = PerformanceService.reopen_review(
            review_id=review_id,
            user=current_user,
            role=current_user.role,
            reason=validated["reason"],
            ip_address=request.remote_addr
        )
        return jsonify({
            "success": True,
            "message": "Performance review has been reopened for adjustment.",
            "data": review
        }), 200
    except ValueError as err:
        return jsonify({"success": False, "error": {"code": "BAD_REQUEST", "message": str(err)}}), 400
    except PermissionError as err:
        return jsonify({"success": False, "error": {"code": "FORBIDDEN", "message": str(err)}}), 403


# ------------------------------------------------------------------------------
# Summary, Analytics & Scale Reference
# ------------------------------------------------------------------------------
@performance_bp.route("/summary", methods=["GET"])
@jwt_required()
def get_performance_summary():
    """Returns organizational performance distribution and completion statistics."""
    summary = PerformanceService.get_summary()
    return jsonify({"success": True, "data": summary}), 200


@performance_bp.route("/reviews/<int:review_id>/history", methods=["GET"])
@jwt_required()
def get_review_history(review_id):
    """Retrieves audit trail of events for this review."""
    try:
        history = PerformanceService.get_review_history(review_id)
        return jsonify({"success": True, "data": history}), 200
    except ValueError as err:
        return jsonify({"success": False, "error": {"code": "NOT_FOUND", "message": str(err)}}), 404


@performance_bp.route("/ratings-scale", methods=["GET"])
@jwt_required()
def get_ratings_scale():
    """Returns official 5-point rating scale reference."""
    scale = PerformanceService.get_rating_scale()
    return jsonify({"success": True, "data": scale}), 200

