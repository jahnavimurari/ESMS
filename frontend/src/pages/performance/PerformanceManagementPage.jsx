import React, { useState, useEffect } from 'react';
import { 
  Award, Plus, Filter, Search, Calendar, 
  AlertCircle, CheckCircle2, RotateCw, RefreshCw, 
  Star, UserCheck, ChevronLeft, ChevronRight, Eye, Edit, RotateCcw, CheckSquare, BarChart2
} from 'lucide-react';
import { performanceService } from '../../services/performanceService';
import { employeeService } from '../../services/employeeService';
import { useAuth } from '../../context/AuthContext';
import CreateCycleModal from '../../components/performance/CreateCycleModal';
import InitiateReviewModal from '../../components/performance/InitiateReviewModal';
import SelfAssessmentModal from '../../components/performance/SelfAssessmentModal';
import ManagerReviewModal from '../../components/performance/ManagerReviewModal';
import ReopenReviewModal from '../../components/performance/ReopenReviewModal';
import ReviewDetailsModal from '../../components/performance/ReviewDetailsModal';

export default function PerformanceManagementPage() {
  const { role, user } = useAuth();
  const isHRorAdmin = role === 'ADMIN' || role === 'HR';

  const [activeTab, setActiveTab] = useState('reviews');
  const [reviews, setReviews] = useState([]);
  const [cycles, setCycles] = useState([]);
  const [employees, setEmployees] = useState([]);
  const [summary, setSummary] = useState(null);
  const [ratingsScale, setRatingsScale] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [success, setSuccess] = useState(null);

  // Filters
  const [search, setSearch] = useState('');
  const [selectedStatus, setSelectedStatus] = useState('');
  const [selectedCycle, setSelectedCycle] = useState('');

  // Pagination
  const [page, setPage] = useState(1);
  const [pagination, setPagination] = useState({ total: 0, page: 1, per_page: 15, pages: 1 });

  // Modals
  const [isCreateCycleOpen, setIsCreateCycleOpen] = useState(false);
  const [isInitiateReviewOpen, setIsInitiateReviewOpen] = useState(false);
  const [isSelfAssessmentOpen, setIsSelfAssessmentOpen] = useState(false);
  const [isManagerReviewOpen, setIsManagerReviewOpen] = useState(false);
  const [isReopenOpen, setIsReopenOpen] = useState(false);
  const [isDetailsOpen, setIsDetailsOpen] = useState(false);
  const [selectedReview, setSelectedReview] = useState(null);

  const loadMetadata = async () => {
    try {
      const [scaleRes, summaryRes, cyclesRes] = await Promise.all([
        performanceService.getRatingsScale(),
        performanceService.getPerformanceSummary(),
        performanceService.getCycles({ per_page: 50 })
      ]);
      if (scaleRes?.data) setRatingsScale(scaleRes.data);
      if (summaryRes?.data) setSummary(summaryRes.data);
      if (cyclesRes?.data?.items) setCycles(cyclesRes.data.items);

      if (isHRorAdmin) {
        const empRes = await employeeService.getEmployees({ per_page: 100 });
        if (empRes?.data?.items) setEmployees(empRes.data.items);
      }
    } catch (err) {
      console.error('Failed to load performance metadata:', err);
    }
  };

  const fetchReviews = async () => {
    setLoading(true);
    setError(null);
    try {
      const params = {
        page,
        per_page: 15,
        search: search.trim() || undefined,
        status: selectedStatus || undefined,
        cycle_id: selectedCycle ? parseInt(selectedCycle, 10) : undefined,
      };

      const res = await performanceService.getReviews(params);
      if (res?.success) {
        setReviews(res.data.items || []);
        setPagination({
          total: res.data.total,
          page: res.data.page,
          per_page: res.data.per_page,
          pages: res.data.pages,
        });
      }
    } catch (err) {
      setError(err?.response?.data?.error?.message || 'Failed to fetch performance reviews.');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadMetadata();
  }, [isHRorAdmin]);

  useEffect(() => {
    fetchReviews();
  }, [page, search, selectedStatus, selectedCycle]);

  const handleToggleCycleStatus = async (cycleId, currentStatus) => {
    try {
      const newStatus = currentStatus === 'ACTIVE' ? 'CLOSED' : 'ACTIVE';
      await performanceService.updateCycleStatus(cycleId, newStatus);
      setSuccess(`Cycle status updated to ${newStatus}.`);
      loadMetadata();
      setTimeout(() => setSuccess(null), 3000);
    } catch (err) {
      setError(err?.response?.data?.error?.message || 'Failed to update cycle status.');
    }
  };

  const getStatusBadge = (status) => {
    const badges = {
      DRAFT: 'bg-zinc-500/10 text-zinc-400 border-zinc-500/20',
      SELF_ASSESSMENT: 'bg-indigo-500/10 text-indigo-400 border-indigo-500/20',
      MANAGER_REVIEW: 'bg-amber-500/10 text-amber-400 border-amber-500/20',
      COMPLETED: 'bg-emerald-500/10 text-emerald-400 border-emerald-500/20',
      CANCELLED: 'bg-red-500/10 text-red-400 border-red-500/20'
    };
    return (
      <span className={`px-2.5 py-1 text-xs font-semibold rounded-full border ${badges[status] || 'bg-zinc-500/10 text-zinc-400 border-zinc-500/20'}`}>
        {status?.replace('_', ' ')}
      </span>
    );
  };

  return (
    <div className="space-y-6">
      {/* Page Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold text-[var(--text-primary)] flex items-center gap-2">
            <Award className="w-7 h-7 text-indigo-500" />
            Performance Management
          </h1>
          <p className="text-sm text-[var(--text-secondary)] mt-1">
            Conduct multi-stage employee evaluations with standard 5-point rating scales and audit trails.
          </p>
        </div>

        {isHRorAdmin && (
          <div className="flex items-center gap-3">
            <button
              onClick={() => setIsCreateCycleOpen(true)}
              className="px-4 py-2 border border-[var(--border)] bg-[var(--surface)] hover:bg-[var(--surface-hover)] rounded-xl text-sm font-medium transition-colors flex items-center gap-2"
            >
              <Calendar className="w-4 h-4 text-indigo-400" /> New Cycle
            </button>
            <button
              onClick={() => setIsInitiateReviewOpen(true)}
              className="px-4 py-2 bg-indigo-600 hover:bg-indigo-700 text-white rounded-xl text-sm font-medium transition-colors flex items-center gap-2 shadow-lg shadow-indigo-600/20"
            >
              <Plus className="w-4 h-4" /> Initiate Review
            </button>
          </div>
        )}
      </div>

      {/* Notifications */}
      {error && (
        <div className="p-4 bg-red-500/10 border border-red-500/20 rounded-2xl flex items-center gap-3 text-sm text-red-500">
          <AlertCircle className="w-5 h-5 shrink-0" />
          <span>{error}</span>
        </div>
      )}
      {success && (
        <div className="p-4 bg-emerald-500/10 border border-emerald-500/20 rounded-2xl flex items-center gap-3 text-sm text-emerald-500">
          <CheckCircle2 className="w-5 h-5 shrink-0" />
          <span>{success}</span>
        </div>
      )}

      {/* Performance Summary Metrics */}
      {summary && (
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
          <div className="p-5 bg-[var(--surface)] border border-[var(--border)] rounded-2xl">
            <span className="text-xs font-semibold text-[var(--text-secondary)] uppercase tracking-wider block">Total Reviews</span>
            <div className="text-2xl font-bold text-[var(--text-primary)] mt-1">{summary.total_reviews}</div>
            <span className="text-xs text-[var(--text-secondary)] mt-1 block">Across {summary.total_cycles} cycles</span>
          </div>

          <div className="p-5 bg-[var(--surface)] border border-[var(--border)] rounded-2xl">
            <span className="text-xs font-semibold text-[var(--text-secondary)] uppercase tracking-wider block">Completed</span>
            <div className="text-2xl font-bold text-emerald-500 mt-1">{summary.status_breakdown?.completed || 0}</div>
            <span className="text-xs text-[var(--text-secondary)] mt-1 block">Fully finalized reviews</span>
          </div>

          <div className="p-5 bg-[var(--surface)] border border-[var(--border)] rounded-2xl">
            <span className="text-xs font-semibold text-[var(--text-secondary)] uppercase tracking-wider block">In Progress</span>
            <div className="text-2xl font-bold text-amber-500 mt-1">{summary.status_breakdown?.in_progress || 0}</div>
            <span className="text-xs text-[var(--text-secondary)] mt-1 block">Drafts & evaluations</span>
          </div>

          <div className="p-5 bg-[var(--surface)] border border-[var(--border)] rounded-2xl">
            <span className="text-xs font-semibold text-[var(--text-secondary)] uppercase tracking-wider block">Average Rating</span>
            <div className="flex items-center gap-2 mt-1">
              <span className="text-2xl font-bold text-[var(--text-primary)]">{summary.average_rating || '0.00'}</span>
              <div className="flex items-center text-amber-400">
                <Star className="w-5 h-5 fill-amber-400" />
              </div>
            </div>
            <span className="text-xs text-[var(--text-secondary)] mt-1 block">5-point scale</span>
          </div>
        </div>
      )}

      {/* Rating Distribution Card */}
      {summary?.ratings_distribution && (
        <div className="p-5 bg-[var(--surface)] border border-[var(--border)] rounded-2xl space-y-3">
          <div className="flex items-center justify-between">
            <span className="text-xs font-bold text-[var(--text-secondary)] uppercase tracking-wider flex items-center gap-2">
              <BarChart2 className="w-4 h-4 text-indigo-400" /> 5-Point Rating Distribution
            </span>
            <span className="text-xs text-[var(--text-secondary)]">Based on finalized reviews</span>
          </div>
          <div className="grid grid-cols-1 sm:grid-cols-5 gap-3 pt-1">
            {summary.ratings_distribution.map((dist) => (
              <div key={dist.score} className="p-3 bg-[var(--background)] border border-[var(--border)] rounded-xl space-y-1">
                <div className="flex items-center justify-between text-xs">
                  <span className="font-bold text-[var(--text-primary)] flex items-center gap-1">
                    <Star className="w-3.5 h-3.5 fill-amber-400 text-amber-400" /> {dist.score}
                  </span>
                  <span className="font-bold text-indigo-400">{dist.count}</span>
                </div>
                <div className="text-[11px] text-[var(--text-secondary)] truncate font-medium">{dist.label}</div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Navigation Tabs */}
      <div className="flex items-center gap-4 border-b border-[var(--border)] pb-3">
        <button
          onClick={() => setActiveTab('reviews')}
          className={`text-sm font-semibold transition-colors flex items-center gap-2 ${
            activeTab === 'reviews' ? 'text-indigo-400 border-b-2 border-indigo-500 pb-3 -mb-3.5' : 'text-[var(--text-secondary)] hover:text-[var(--text-primary)]'
          }`}
        >
          <Award className="w-4 h-4" /> Performance Reviews
        </button>
        {isHRorAdmin && (
          <button
            onClick={() => setActiveTab('cycles')}
            className={`text-sm font-semibold transition-colors flex items-center gap-2 ${
              activeTab === 'cycles' ? 'text-indigo-400 border-b-2 border-indigo-500 pb-3 -mb-3.5' : 'text-[var(--text-secondary)] hover:text-[var(--text-primary)]'
            }`}
          >
            <Calendar className="w-4 h-4" /> Review Cycles ({cycles.length})
          </button>
        )}
      </div>

      {activeTab === 'reviews' ? (
        <>
          {/* Filters Bar */}
          <div className="flex flex-col sm:flex-row items-center gap-3">
            <div className="relative flex-1 w-full">
              <Search className="w-4 h-4 absolute left-3 top-1/2 -translate-y-1/2 text-[var(--text-secondary)]" />
              <input
                type="text"
                placeholder="Search reviews by employee name, code, or period..."
                value={search}
                onChange={(e) => setSearch(e.target.value)}
                className="w-full pl-9 pr-4 py-2 bg-[var(--surface)] border border-[var(--border)] rounded-xl text-sm focus:outline-none focus:border-indigo-500"
              />
            </div>

            <select
              value={selectedStatus}
              onChange={(e) => setSelectedStatus(e.target.value)}
              className="w-full sm:w-48 px-3 py-2 bg-[var(--surface)] border border-[var(--border)] rounded-xl text-sm focus:outline-none focus:border-indigo-500"
            >
              <option value="">All Statuses</option>
              <option value="DRAFT">DRAFT</option>
              <option value="SELF_ASSESSMENT">SELF ASSESSMENT</option>
              <option value="MANAGER_REVIEW">MANAGER REVIEW</option>
              <option value="COMPLETED">COMPLETED</option>
              <option value="CANCELLED">CANCELLED</option>
            </select>

            <select
              value={selectedCycle}
              onChange={(e) => setSelectedCycle(e.target.value)}
              className="w-full sm:w-56 px-3 py-2 bg-[var(--surface)] border border-[var(--border)] rounded-xl text-sm focus:outline-none focus:border-indigo-500"
            >
              <option value="">All Cycles</option>
              {cycles.map((c) => (
                <option key={c.id} value={c.id}>{c.title}</option>
              ))}
            </select>
          </div>

          {/* Reviews Table */}
          <div className="bg-[var(--surface)] border border-[var(--border)] rounded-2xl overflow-hidden shadow-sm">
            <div className="overflow-x-auto">
              <table className="w-full text-left text-sm">
                <thead className="bg-[var(--background)] border-b border-[var(--border)] text-xs font-semibold text-[var(--text-secondary)] uppercase tracking-wider">
                  <tr>
                    <th className="px-6 py-4">Employee</th>
                    <th className="px-6 py-4">Cycle / Period</th>
                    <th className="px-6 py-4">Self Rating</th>
                    <th className="px-6 py-4">Final Rating</th>
                    <th className="px-6 py-4">Status</th>
                    <th className="px-6 py-4 text-right">Actions</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-[var(--border)]">
                  {loading ? (
                    <tr>
                      <td colSpan="6" className="px-6 py-12 text-center text-[var(--text-secondary)]">
                        <RotateCw className="w-6 h-6 animate-spin mx-auto mb-2 text-indigo-500" />
                        Loading performance reviews...
                      </td>
                    </tr>
                  ) : reviews.length === 0 ? (
                    <tr>
                      <td colSpan="6" className="px-6 py-12 text-center text-[var(--text-secondary)]">
                        No performance reviews found.
                      </td>
                    </tr>
                  ) : (
                    reviews.map((r) => (
                      <tr key={r.id} className="hover:bg-[var(--surface-hover)] transition-colors">
                        <td className="px-6 py-4">
                          <div className="font-semibold text-[var(--text-primary)]">{r.employee_name}</div>
                          <div className="text-xs text-[var(--text-secondary)]">{r.employee_code} • {r.department_name || 'General'}</div>
                        </td>
                        <td className="px-6 py-4">
                          <div className="text-[var(--text-primary)] font-medium">{r.cycle_title || r.review_period}</div>
                          {r.due_date && <div className="text-xs text-[var(--text-secondary)]">Due: {r.due_date}</div>}
                        </td>
                        <td className="px-6 py-4">
                          {r.self_assessment?.self_rating ? (
                            <span className="inline-flex items-center gap-1 font-semibold text-indigo-400">
                              <Star className="w-3.5 h-3.5 fill-indigo-400" /> {r.self_assessment.self_rating} / 5
                            </span>
                          ) : (
                            <span className="text-xs text-[var(--text-secondary)]">Not rated</span>
                          )}
                        </td>
                        <td className="px-6 py-4">
                          {r.manager_evaluation?.rating ? (
                            <span className="inline-flex items-center gap-1 font-semibold text-emerald-400">
                              <Star className="w-3.5 h-3.5 fill-emerald-400" /> {r.manager_evaluation.rating} / 5
                            </span>
                          ) : (
                            <span className="text-xs text-[var(--text-secondary)]">Pending</span>
                          )}
                        </td>
                        <td className="px-6 py-4">
                          {getStatusBadge(r.status)}
                        </td>
                        <td className="px-6 py-4 text-right">
                          <div className="flex items-center justify-end gap-2">
                            {/* View details */}
                            <button
                              onClick={() => { setSelectedReview(r); setIsDetailsOpen(true); }}
                              title="View Details"
                              className="p-1.5 hover:bg-[var(--background)] rounded-lg text-[var(--text-secondary)] hover:text-[var(--text-primary)] transition-colors"
                            >
                              <Eye className="w-4 h-4" />
                            </button>

                            {/* Self Assessment button (if employee or HR and status allows) */}
                            {(r.status === 'DRAFT' || r.status === 'SELF_ASSESSMENT') && (
                              <button
                                onClick={() => { setSelectedReview(r); setIsSelfAssessmentOpen(true); }}
                                title="Self-Assessment"
                                className="px-2.5 py-1 text-xs font-semibold bg-indigo-500/10 text-indigo-400 hover:bg-indigo-500/20 rounded-lg transition-colors"
                              >
                                Self-Assess
                              </button>
                            )}

                            {/* Manager Evaluation button (HR/Admin when status is MANAGER_REVIEW) */}
                            {isHRorAdmin && r.status === 'MANAGER_REVIEW' && (
                              <button
                                onClick={() => { setSelectedReview(r); setIsManagerReviewOpen(true); }}
                                title="Evaluate"
                                className="px-2.5 py-1 text-xs font-semibold bg-emerald-500/10 text-emerald-400 hover:bg-emerald-500/20 rounded-lg transition-colors"
                              >
                                Evaluate
                              </button>
                            )}

                            {/* Reopen button (HR/Admin when status is COMPLETED) */}
                            {isHRorAdmin && r.status === 'COMPLETED' && (
                              <button
                                onClick={() => { setSelectedReview(r); setIsReopenOpen(true); }}
                                title="Reopen Review"
                                className="p-1.5 hover:bg-amber-500/10 text-amber-400 rounded-lg transition-colors"
                              >
                                <RotateCcw className="w-4 h-4" />
                              </button>
                            )}
                          </div>
                        </td>
                      </tr>
                    ))
                  )}
                </tbody>
              </table>
            </div>

            {/* Pagination */}
            {pagination.pages > 1 && (
              <div className="flex items-center justify-between px-6 py-4 border-t border-[var(--border)]">
                <span className="text-xs text-[var(--text-secondary)]">
                  Showing page {pagination.page} of {pagination.pages} ({pagination.total} total reviews)
                </span>
                <div className="flex items-center gap-2">
                  <button
                    disabled={page <= 1}
                    onClick={() => setPage(p => p - 1)}
                    className="p-1.5 border border-[var(--border)] rounded-lg disabled:opacity-40 hover:bg-[var(--surface-hover)]"
                  >
                    <ChevronLeft className="w-4 h-4" />
                  </button>
                  <button
                    disabled={page >= pagination.pages}
                    onClick={() => setPage(p => p + 1)}
                    className="p-1.5 border border-[var(--border)] rounded-lg disabled:opacity-40 hover:bg-[var(--surface-hover)]"
                  >
                    <ChevronRight className="w-4 h-4" />
                  </button>
                </div>
              </div>
            )}
          </div>
        </>
      ) : (
        /* Cycles Tab */
        <div className="bg-[var(--surface)] border border-[var(--border)] rounded-2xl overflow-hidden shadow-sm">
          <div className="overflow-x-auto">
            <table className="w-full text-left text-sm">
              <thead className="bg-[var(--background)] border-b border-[var(--border)] text-xs font-semibold text-[var(--text-secondary)] uppercase tracking-wider">
                <tr>
                  <th className="px-6 py-4">Cycle Title</th>
                  <th className="px-6 py-4">Dates (Start - End)</th>
                  <th className="px-6 py-4">Due Date</th>
                  <th className="px-6 py-4">Completion Progress</th>
                  <th className="px-6 py-4">Status</th>
                  <th className="px-6 py-4 text-right">Actions</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-[var(--border)]">
                {cycles.length === 0 ? (
                  <tr>
                    <td colSpan="6" className="px-6 py-12 text-center text-[var(--text-secondary)]">
                      No performance cycles defined.
                    </td>
                  </tr>
                ) : (
                  cycles.map((c) => (
                    <tr key={c.id} className="hover:bg-[var(--surface-hover)] transition-colors">
                      <td className="px-6 py-4">
                        <div className="font-semibold text-[var(--text-primary)]">{c.title}</div>
                        {c.description && <div className="text-xs text-[var(--text-secondary)] line-clamp-1">{c.description}</div>}
                      </td>
                      <td className="px-6 py-4 text-xs text-[var(--text-secondary)]">
                        {c.start_date} to {c.end_date}
                      </td>
                      <td className="px-6 py-4 text-xs font-medium text-[var(--text-primary)]">
                        {c.due_date}
                      </td>
                      <td className="px-6 py-4">
                        <div className="flex items-center gap-2">
                          <div className="w-24 bg-[var(--background)] h-2 rounded-full overflow-hidden border border-[var(--border)]">
                            <div 
                              className="bg-indigo-500 h-full rounded-full transition-all duration-300"
                              style={{ width: `${c.metrics?.completion_rate || 0}%` }}
                            />
                          </div>
                          <span className="text-xs text-[var(--text-secondary)] font-medium">
                            {c.metrics?.completed || 0}/{c.metrics?.total_reviews || 0} ({c.metrics?.completion_rate || 0}%)
                          </span>
                        </div>
                      </td>
                      <td className="px-6 py-4">
                        <span className={`px-2.5 py-1 text-xs font-semibold rounded-full border ${
                          c.status === 'ACTIVE' 
                            ? 'bg-emerald-500/10 text-emerald-400 border-emerald-500/20' 
                            : 'bg-zinc-500/10 text-zinc-400 border-zinc-500/20'
                        }`}>
                          {c.status}
                        </span>
                      </td>
                      <td className="px-6 py-4 text-right">
                        <button
                          onClick={() => handleToggleCycleStatus(c.id, c.status)}
                          className="px-3 py-1.5 text-xs font-semibold rounded-lg border border-[var(--border)] hover:bg-[var(--background)] transition-colors"
                        >
                          {c.status === 'ACTIVE' ? 'Close Cycle' : 'Reactivate'}
                        </button>
                      </td>
                    </tr>
                  ))
                )}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {/* Modals */}
      <CreateCycleModal
        isOpen={isCreateCycleOpen}
        onClose={() => setIsCreateCycleOpen(false)}
        onSuccess={() => {
          loadMetadata();
          setSuccess('Cycle created successfully.');
        }}
      />

      <InitiateReviewModal
        isOpen={isInitiateReviewOpen}
        onClose={() => setIsInitiateReviewOpen(false)}
        cycles={cycles}
        employees={employees}
        onSuccess={() => {
          fetchReviews();
          loadMetadata();
          setSuccess('Performance review initiated.');
        }}
      />

      <SelfAssessmentModal
        isOpen={isSelfAssessmentOpen}
        onClose={() => setIsSelfAssessmentOpen(false)}
        review={selectedReview}
        ratingsScale={ratingsScale}
        onSuccess={() => {
          fetchReviews();
          loadMetadata();
          setSuccess('Self-assessment saved.');
        }}
      />

      <ManagerReviewModal
        isOpen={isManagerReviewOpen}
        onClose={() => setIsManagerReviewOpen(false)}
        review={selectedReview}
        ratingsScale={ratingsScale}
        onSuccess={() => {
          fetchReviews();
          loadMetadata();
          setSuccess('Manager evaluation recorded.');
        }}
      />

      <ReopenReviewModal
        isOpen={isReopenOpen}
        onClose={() => setIsReopenOpen(false)}
        review={selectedReview}
        onSuccess={() => {
          fetchReviews();
          loadMetadata();
          setSuccess('Review reopened successfully.');
        }}
      />

      <ReviewDetailsModal
        isOpen={isDetailsOpen}
        onClose={() => setIsDetailsOpen(false)}
        review={selectedReview}
      />
    </div>
  );
}

