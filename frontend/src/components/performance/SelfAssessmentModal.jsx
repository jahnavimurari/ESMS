import React, { useState } from 'react';
import { X, Send, Save, Star, AlertCircle, Award } from 'lucide-react';
import { performanceService } from '../../services/performanceService';

export default function SelfAssessmentModal({ isOpen, onClose, onSuccess, review, ratingsScale }) {
  const [formData, setFormData] = useState({
    self_rating: review?.self_assessment?.self_rating || 3,
    accomplishments: review?.self_assessment?.accomplishments || '',
    challenges: review?.self_assessment?.challenges || '',
    skills_learned: review?.self_assessment?.skills_learned || '',
    goals_achievement: review?.self_assessment?.goals_achievement || ''
  });
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  if (!isOpen || !review) return null;

  const isLocked = review.status !== 'DRAFT' && review.status !== 'SELF_ASSESSMENT';

  const handleChange = (e) => {
    setFormData({ ...formData, [e.target.name]: e.target.value });
  };

  const handleSaveDraft = async () => {
    setError(null);
    setLoading(true);
    try {
      const payload = {
        self_rating: parseInt(formData.self_rating, 10),
        accomplishments: formData.accomplishments,
        challenges: formData.challenges,
        skills_learned: formData.skills_learned,
        goals_achievement: formData.goals_achievement
      };
      const res = await performanceService.updateSelfAssessment(review.id, payload);
      if (res?.success) {
        onSuccess(res.data);
        onClose();
      }
    } catch (err) {
      setError(err?.response?.data?.error?.message || err.message || 'Failed to save self-assessment draft.');
    } finally {
      setLoading(false);
    }
  };

  const handleSubmit = async () => {
    setError(null);
    setLoading(true);
    try {
      // First save current form data
      const payload = {
        self_rating: parseInt(formData.self_rating, 10),
        accomplishments: formData.accomplishments,
        challenges: formData.challenges,
        skills_learned: formData.skills_learned,
        goals_achievement: formData.goals_achievement
      };
      await performanceService.updateSelfAssessment(review.id, payload);
      // Then formally submit
      const res = await performanceService.submitSelfAssessment(review.id);
      if (res?.success) {
        onSuccess(res.data);
        onClose();
      }
    } catch (err) {
      setError(err?.response?.data?.error?.message || err.message || 'Failed to submit self-assessment.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 backdrop-blur-sm p-4">
      <div className="bg-[var(--surface)] border border-[var(--border)] rounded-2xl w-full max-w-2xl max-h-[90vh] flex flex-col shadow-2xl overflow-hidden animate-in fade-in zoom-in-95 duration-200">
        <div className="flex items-center justify-between px-6 py-4 border-b border-[var(--border)]">
          <div className="flex items-center gap-2">
            <Award className="w-5 h-5 text-indigo-500" />
            <div>
              <h2 className="text-lg font-semibold text-[var(--text-primary)]">Employee Self-Assessment</h2>
              <p className="text-xs text-[var(--text-secondary)]">{review.cycle_title} • {review.employee_name}</p>
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
          {/* Rating Scale Selection (1 to 5) */}
          <div>
            <label className="block text-xs font-semibold text-[var(--text-secondary)] uppercase tracking-wider mb-2">
              Overall Self Rating (1 to 5) *
            </label>
            <div className="grid grid-cols-5 gap-2">
              {[1, 2, 3, 4, 5].map((score) => {
                const isSelected = parseInt(formData.self_rating, 10) === score;
                const def = ratingsScale?.find(s => s.score === score);
                return (
                  <button
                    key={score}
                    type="button"
                    disabled={isLocked}
                    onClick={() => setFormData({ ...formData, self_rating: score })}
                    className={`p-3 rounded-xl border text-center transition-all flex flex-col items-center justify-center gap-1 ${
                      isSelected
                        ? 'border-indigo-500 bg-indigo-500/10 text-indigo-500 font-bold'
                        : 'border-[var(--border)] bg-[var(--background)] text-[var(--text-secondary)] hover:border-indigo-400'
                    }`}
                  >
                    <div className="flex items-center gap-0.5">
                      <Star className={`w-4 h-4 ${isSelected ? 'fill-indigo-500' : ''}`} />
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
              Key Accomplishments & Deliverables
            </label>
            <textarea
              name="accomplishments"
              rows="3"
              disabled={isLocked}
              value={formData.accomplishments}
              onChange={handleChange}
              placeholder="Highlight key milestones delivered, technical contributions, or positive outcomes achieved during this review period..."
              className="w-full px-3 py-2 bg-[var(--background)] border border-[var(--border)] rounded-xl text-sm focus:outline-none focus:border-indigo-500 disabled:opacity-60"
            />
          </div>

          <div>
            <label className="block text-xs font-semibold text-[var(--text-secondary)] uppercase tracking-wider mb-1">
              Challenges Faced & How You Overcame Them
            </label>
            <textarea
              name="challenges"
              rows="2"
              disabled={isLocked}
              value={formData.challenges}
              onChange={handleChange}
              placeholder="Describe blockers, constraints, or unexpected difficulties encountered and steps taken to mitigate..."
              className="w-full px-3 py-2 bg-[var(--background)] border border-[var(--border)] rounded-xl text-sm focus:outline-none focus:border-indigo-500 disabled:opacity-60"
            />
          </div>

          <div>
            <label className="block text-xs font-semibold text-[var(--text-secondary)] uppercase tracking-wider mb-1">
              Skills Acquired & Professional Growth
            </label>
            <textarea
              name="skills_learned"
              rows="2"
              disabled={isLocked}
              value={formData.skills_learned}
              onChange={handleChange}
              placeholder="List certifications, tools, architectural patterns, or methodologies learned..."
              className="w-full px-3 py-2 bg-[var(--background)] border border-[var(--border)] rounded-xl text-sm focus:outline-none focus:border-indigo-500 disabled:opacity-60"
            />
          </div>

          <div>
            <label className="block text-xs font-semibold text-[var(--text-secondary)] uppercase tracking-wider mb-1">
              Goals for Next Period
            </label>
            <textarea
              name="goals_achievement"
              rows="2"
              disabled={isLocked}
              value={formData.goals_achievement}
              onChange={handleChange}
              placeholder="Propose key targets and areas of growth for upcoming cycles..."
              className="w-full px-3 py-2 bg-[var(--background)] border border-[var(--border)] rounded-xl text-sm focus:outline-none focus:border-indigo-500 disabled:opacity-60"
            />
          </div>
        </div>

        <div className="flex items-center justify-between px-6 py-4 border-t border-[var(--border)]">
          <div className="text-xs text-[var(--text-secondary)]">
            Status: <span className="font-semibold text-indigo-400">{review.status}</span>
          </div>
          {!isLocked && (
            <div className="flex items-center gap-3">
              <button
                type="button"
                onClick={handleSaveDraft}
                disabled={loading}
                className="px-4 py-2 border border-[var(--border)] rounded-xl text-sm font-medium hover:bg-[var(--surface-hover)] flex items-center gap-2"
              >
                <Save className="w-4 h-4" /> Save Draft
              </button>
              <button
                type="button"
                onClick={handleSubmit}
                disabled={loading}
                className="px-5 py-2 bg-indigo-600 hover:bg-indigo-700 text-white font-medium rounded-xl text-sm transition-colors flex items-center gap-2 shadow-lg shadow-indigo-600/20"
              >
                <Send className="w-4 h-4" /> {loading ? 'Submitting...' : 'Submit to Manager'}
              </button>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}

