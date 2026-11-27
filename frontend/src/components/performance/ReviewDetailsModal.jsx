import React, { useState, useEffect } from 'react';
import { X, Award, Star, History, Calendar, User, ShieldCheck } from 'lucide-react';
import { performanceService } from '../../services/performanceService';

export default function ReviewDetailsModal({ isOpen, onClose, review }) {
  const [history, setHistory] = useState([]);
  const [loadingHistory, setLoadingHistory] = useState(false);

  useEffect(() => {
    if (isOpen && review?.id) {
      setLoadingHistory(true);
      performanceService.getReviewHistory(review.id)
        .then((res) => {
          if (res?.success) setHistory(res.data);
        })
        .catch(() => {})
        .finally(() => setLoadingHistory(false));
    }
  }, [isOpen, review]);

  if (!isOpen || !review) return null;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 backdrop-blur-sm p-4">
      <div className="bg-[var(--surface)] border border-[var(--border)] rounded-2xl w-full max-w-3xl max-h-[90vh] flex flex-col shadow-2xl overflow-hidden animate-in fade-in zoom-in-95 duration-200">
        <div className="flex items-center justify-between px-6 py-4 border-b border-[var(--border)]">
          <div className="flex items-center gap-2">
            <Award className="w-5 h-5 text-indigo-500" />
            <div>
              <h2 className="text-lg font-semibold text-[var(--text-primary)]">Performance Review Overview</h2>
              <p className="text-xs text-[var(--text-secondary)]">{review.cycle_title} • Period: {review.review_period}</p>
            </div>
          </div>
          <button onClick={onClose} className="p-1 text-[var(--text-secondary)] hover:text-[var(--text-primary)] rounded-lg">
            <X className="w-5 h-5" />
          </button>
        </div>

        <div className="p-6 space-y-6 overflow-y-auto flex-1">
          {/* Top metadata summary */}
          <div className="grid grid-cols-4 gap-4 p-4 bg-[var(--background)] border border-[var(--border)] rounded-xl text-xs">
            <div>
              <span className="text-[var(--text-secondary)] block">Employee</span>
              <span className="font-semibold text-[var(--text-primary)] text-sm">{review.employee_name}</span>
              <span className="text-[var(--text-secondary)] block text-[11px]">{review.employee_code}</span>
            </div>
            <div>
              <span className="text-[var(--text-secondary)] block">Department</span>
              <span className="font-semibold text-[var(--text-primary)] text-sm">{review.department_name || 'General'}</span>
            </div>
            <div>
              <span className="text-[var(--text-secondary)] block">Status</span>
              <span className="inline-block px-2 py-0.5 mt-0.5 rounded-full text-[11px] font-bold bg-indigo-500/10 text-indigo-400">
                {review.status}
              </span>
            </div>
            <div>
              <span className="text-[var(--text-secondary)] block">Final Rating</span>
              <div className="flex items-center gap-1 mt-0.5">
                <Star className="w-4 h-4 text-amber-400 fill-amber-400" />
                <span className="font-bold text-sm text-[var(--text-primary)]">
                  {review.manager_evaluation?.rating ? `${review.manager_evaluation.rating} / 5` : 'Pending'}
                </span>
              </div>
            </div>
          </div>

          {/* Manager Evaluation Card */}
          <div className="p-4 border border-[var(--border)] rounded-xl space-y-3">
            <div className="flex items-center justify-between border-b border-[var(--border)] pb-2">
              <span className="text-xs font-bold uppercase tracking-wider text-emerald-400 flex items-center gap-1.5">
                <ShieldCheck className="w-4 h-4" /> Manager Evaluation
              </span>
              {review.manager_evaluation?.rating && (
                <span className="text-xs font-bold text-emerald-400">
                  {review.manager_evaluation.rating_label}
                </span>
              )}
            </div>
            {review.manager_evaluation?.manager_feedback ? (
              <div className="space-y-2 text-xs">
                <p><strong>Feedback:</strong> {review.manager_evaluation.manager_feedback}</p>
                {review.manager_evaluation.strengths && (
                  <p><strong>Strengths:</strong> {review.manager_evaluation.strengths}</p>
                )}
                {review.manager_evaluation.areas_for_improvement && (
                  <p><strong>Areas for Improvement:</strong> {review.manager_evaluation.areas_for_improvement}</p>
                )}
                {review.manager_evaluation.development_plan && (
                  <p><strong>Development Plan:</strong> {review.manager_evaluation.development_plan}</p>
                )}
              </div>
            ) : (
              <p className="text-xs text-[var(--text-secondary)] italic">Manager evaluation has not been submitted yet.</p>
            )}
          </div>

          {/* Employee Self-Assessment Card */}
          <div className="p-4 border border-[var(--border)] rounded-xl space-y-3">
            <div className="flex items-center justify-between border-b border-[var(--border)] pb-2">
              <span className="text-xs font-bold uppercase tracking-wider text-indigo-400 flex items-center gap-1.5">
                <User className="w-4 h-4" /> Employee Self-Assessment
              </span>
              {review.self_assessment?.self_rating && (
                <span className="text-xs font-bold text-indigo-400">
                  Self-Rating: {review.self_assessment.self_rating} / 5 ({review.self_assessment.self_rating_label})
                </span>
              )}
            </div>
            {review.self_assessment?.accomplishments ? (
              <div className="space-y-2 text-xs">
                <p><strong>Accomplishments:</strong> {review.self_assessment.accomplishments}</p>
                {review.self_assessment.challenges && (
                  <p><strong>Challenges:</strong> {review.self_assessment.challenges}</p>
                )}
                {review.self_assessment.skills_learned && (
                  <p><strong>Skills Learned:</strong> {review.self_assessment.skills_learned}</p>
                )}
                {review.self_assessment.goals_achievement && (
                  <p><strong>Goals:</strong> {review.self_assessment.goals_achievement}</p>
                )}
              </div>
            ) : (
              <p className="text-xs text-[var(--text-secondary)] italic">Self-assessment details not yet drafted or submitted.</p>
            )}
          </div>

          {/* Audit Trail & History */}
          <div className="p-4 border border-[var(--border)] rounded-xl space-y-3">
            <div className="flex items-center gap-1.5 border-b border-[var(--border)] pb-2">
              <History className="w-4 h-4 text-purple-400" />
              <span className="text-xs font-bold uppercase tracking-wider text-[var(--text-primary)]">
                Compliance Audit Trail
              </span>
            </div>
            {loadingHistory ? (
              <p className="text-xs text-[var(--text-secondary)]">Loading audit trail...</p>
            ) : history.length > 0 ? (
              <div className="space-y-2 max-h-40 overflow-y-auto">
                {history.map((log) => (
                  <div key={log.id} className="p-2.5 bg-[var(--background)] border border-[var(--border)] rounded-lg text-xs space-y-1">
                    <div className="flex items-center justify-between text-[11px]">
                      <span className="font-bold text-indigo-400">{log.action}</span>
                      <span className="text-[var(--text-secondary)]">{new Date(log.timestamp).toLocaleString()}</span>
                    </div>
                    {log.new_state?.reason && (
                      <p className="text-amber-400 text-[11px]">Reason: {log.new_state.reason}</p>
                    )}
                  </div>
                ))}
              </div>
            ) : (
              <p className="text-xs text-[var(--text-secondary)] italic">No audit records found.</p>
            )}
          </div>
        </div>

        <div className="flex items-center justify-end px-6 py-4 border-t border-[var(--border)]">
          <button
            onClick={onClose}
            className="px-5 py-2 bg-[var(--surface-hover)] border border-[var(--border)] rounded-xl text-sm font-medium hover:bg-[var(--border)]"
          >
            Close
          </button>
        </div>
      </div>
    </div>
  );
}

