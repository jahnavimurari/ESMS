import React, { useState } from 'react';
import { X, CheckCircle, Save, Star, AlertCircle, Award } from 'lucide-react';
import { performanceService } from '../../services/performanceService';

export default function ManagerReviewModal({ isOpen, onClose, onSuccess, review, ratingsScale }) {
  const [formData, setFormData] = useState({
    rating: review?.manager_evaluation?.rating || 3,
    manager_feedback: review?.manager_evaluation?.manager_feedback || '',
    strengths: review?.manager_evaluation?.strengths || '',
    areas_for_improvement: review?.manager_evaluation?.areas_for_improvement || '',
    development_plan: review?.manager_evaluation?.development_plan || ''
  });
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  if (!isOpen || !review) return null;

  const isCompleted = review.status === 'COMPLETED';

  const handleChange = (e) => {
    setFormData({ ...formData, [e.target.name]: e.target.value });
  };

  const handleSaveEvaluation = async () => {
    setError(null);
    setLoading(true);
    try {
      const payload = {
        rating: parseInt(formData.rating, 10),
        manager_feedback: formData.manager_feedback.trim(),
        strengths: formData.strengths.trim(),
        areas_for_improvement: formData.areas_for_improvement.trim(),
        development_plan: formData.development_plan.trim()
      };
      const res = await performanceService.submitManagerReview(review.id, payload);
      if (res?.success) {
        onSuccess(res.data);
        onClose();
      }
    } catch (err) {
      setError(err?.response?.data?.error?.message || err.message || 'Failed to record manager evaluation.');
    } finally {
      setLoading(false);
    }
  };

  const handleFinalize = async () => {
    setError(null);
    setLoading(true);
    try {
      // First save evaluation
      const payload = {
        rating: parseInt(formData.rating, 10),
        manager_feedback: formData.manager_feedback.trim(),
        strengths: formData.strengths.trim(),
        areas_for_improvement: formData.areas_for_improvement.trim(),
        development_plan: formData.development_plan.trim()
      };
      await performanceService.submitManagerReview(review.id, payload);
      // Then complete
      const res = await performanceService.completeReview(review.id);
      if (res?.success) {
        onSuccess(res.data);
        onClose();
      }
    } catch (err) {
      setError(err?.response?.data?.error?.message || err.message || 'Failed to finalize review.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 backdrop-blur-sm p-4">
      <div className="bg-[var(--surface)] border border-[var(--border)] rounded-2xl w-full max-w-2xl max-h-[90vh] flex flex-col shadow-2xl overflow-hidden animate-in fade-in zoom-in-95 duration-200">
        <div className="flex items-center justify-between px-6 py-4 border-b border-[var(--border)]">
          <div className="flex items-center gap-2">
            <Award className="w-5 h-5 text-emerald-500" />
            <div>
              <h2 className="text-lg font-semibold text-[var(--text-primary)]">Manager Performance Evaluation</h2>
              <p className="text-xs text-[var(--text-secondary)]">{review.cycle_title} • Employee: {review.employee_name}</p>
            </div>
          </div>
          <button onClick={onClose} className="p-1 text-[var(--text-secondary)] hover:text-[var(--text-primary)] rounded-lg">
            <X className="w-5 h-5" />
          </button>
        </div>

        {error && (
          <div className="mx-6 mt-4 p-3 bg-red-500/10 border border-red-500/20 rounded-xl flex items-center gap-2 text-sm text-red-500">
            <AlertCircle className="w-4 h-4 shrink-0" />
            <span>{error}</span>
          </div>
        )}

        <div className="p-6 space-y-4 overflow-y-auto flex-1">
          {/* Employee Self-Assessment Overview */}
          {review.self_assessment?.self_rating && (
            <div className="p-4 bg-[var(--background)] border border-[var(--border)] rounded-xl space-y-2">
              <div className="flex items-center justify-between">
                <span className="text-xs font-semibold text-[var(--text-secondary)] uppercase">Employee Self Rating</span>
                <span className="text-xs font-bold text-indigo-400">
                  {review.self_assessment.self_rating} / 5 ({review.self_assessment.self_rating_label})
                </span>
              </div>
              {review.self_assessment.accomplishments && (
                <p className="text-xs text-[var(--text-secondary)]">
                  <strong className="text-[var(--text-primary)]">Accomplishments:</strong> {review.self_assessment.accomplishments}
                </p>
              )}
            </div>
          )}

          {/* 5-Point Rating Scale */}
          <div>
            <label className="block text-xs font-semibold text-[var(--text-secondary)] uppercase tracking-wider mb-2">
              Final Rating (1 to 5 Scale) *
            </label>
            <div className="grid grid-cols-5 gap-2">
              {[1, 2, 3, 4, 5].map((score) => {
                const isSelected = parseInt(formData.rating, 10) === score;
                const def = ratingsScale?.find(s => s.score === score);
                return (
                  <button
                    key={score}
                    type="button"
                    disabled={isCompleted}
                    onClick={() => setFormData({ ...formData, rating: score })}
                    className={`p-3 rounded-xl border text-center transition-all flex flex-col items-center justify-center gap-1 ${
                      isSelected
                        ? 'border-emerald-500 bg-emerald-500/10 text-emerald-500 font-bold'
                        : 'border-[var(--border)] bg-[var(--background)] text-[var(--text-secondary)] hover:border-emerald-400'
                    }`}
                  >
                    <div className="flex items-center gap-0.5">
                      <Star className={`w-4 h-4 ${isSelected ? 'fill-emerald-500' : ''}`} />
                      <span className="text-base">{score}</span>
                    </div>
                    <span className="text-[11px] leading-tight font-normal line-clamp-1">
                      {def?.label || `Score ${score}`}
                    </span>
                  </button>
                );
              })}
            </div>
          </div>

          <div>
            <label className="block text-xs font-semibold text-[var(--text-secondary)] uppercase tracking-wider mb-1">
              Manager Feedback & Evaluation *
            </label>
            <textarea
              name="manager_feedback"
              required
              rows="3"
              disabled={isCompleted}
              value={formData.manager_feedback}
              onChange={handleChange}
              placeholder="Provide constructive feedback, appraisal of performance, and overall impact..."
              className="w-full px-3 py-2 bg-[var(--background)] border border-[var(--border)] rounded-xl text-sm focus:outline-none focus:border-emerald-500 disabled:opacity-60"
            />
          </div>

          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="block text-xs font-semibold text-[var(--text-secondary)] uppercase tracking-wider mb-1">
                Observed Strengths
              </label>
              <textarea
                name="strengths"
                rows="2"
                disabled={isCompleted}
                value={formData.strengths}
                onChange={handleChange}
                placeholder="Core strengths and areas of excellence..."
                className="w-full px-3 py-2 bg-[var(--background)] border border-[var(--border)] rounded-xl text-sm focus:outline-none focus:border-emerald-500 disabled:opacity-60"
              />
            </div>
            <div>
              <label className="block text-xs font-semibold text-[var(--text-secondary)] uppercase tracking-wider mb-1">
                Areas for Improvement
              </label>
              <textarea
                name="areas_for_improvement"
                rows="2"
                disabled={isCompleted}
                value={formData.areas_for_improvement}
                onChange={handleChange}
                placeholder="Competencies and areas needing focus..."
                className="w-full px-3 py-2 bg-[var(--background)] border border-[var(--border)] rounded-xl text-sm focus:outline-none focus:border-emerald-500 disabled:opacity-60"
              />
            </div>
          </div>

          <div>
            <label className="block text-xs font-semibold text-[var(--text-secondary)] uppercase tracking-wider mb-1">
              Development & Career Plan
            </label>
            <textarea
              name="development_plan"
              rows="2"
              disabled={isCompleted}
              value={formData.development_plan}
              onChange={handleChange}
              placeholder="Recommended training, mentorship, or stretch projects..."
              className="w-full px-3 py-2 bg-[var(--background)] border border-[var(--border)] rounded-xl text-sm focus:outline-none focus:border-emerald-500 disabled:opacity-60"
            />
          </div>
        </div>

        <div className="flex items-center justify-between px-6 py-4 border-t border-[var(--border)]">
          <div className="text-xs text-[var(--text-secondary)]">
            Current Status: <span className="font-semibold text-emerald-400">{review.status}</span>
          </div>
          {!isCompleted && (
            <div className="flex items-center gap-3">
              <button
                type="button"
                onClick={handleSaveEvaluation}
                disabled={loading}
                className="px-4 py-2 border border-[var(--border)] rounded-xl text-sm font-medium hover:bg-[var(--surface-hover)] flex items-center gap-2"
              >
                <Save className="w-4 h-4" /> Save Evaluation
              </button>
              <button
                type="button"
                onClick={handleFinalize}
                disabled={loading}
                className="px-5 py-2 bg-emerald-600 hover:bg-emerald-700 text-white font-medium rounded-xl text-sm transition-colors flex items-center gap-2 shadow-lg shadow-emerald-600/20"
              >
                <CheckCircle className="w-4 h-4" /> {loading ? 'Finalizing...' : 'Complete & Finalize'}
              </button>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}

