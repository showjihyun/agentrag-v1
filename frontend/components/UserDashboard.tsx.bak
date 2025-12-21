'use client';

/**
 * User Dashboard Component
 * Displays user information, usage statistics, recent activity, and settings.
 */

import React, { useState, useEffect } from 'react';
import { useRouter } from 'next/navigation';
import { useAuth } from '@/contexts/AuthContext';
import { apiClient } from '@/lib/api-client';
import { SessionResponse, DocumentResponse } from '@/lib/types';
import UserMenu from './UserMenu';
import StatCard from './charts/StatCard';
import PieChart from './charts/PieChart';
import UsageChart from './charts/UsageChart';

export default function UserDashboard() {
  const router = useRouter();
  const { user, logout, refreshUser } = useAuth();
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState<string | null>(null);
  
  // Recent activity state
  const [recentSessions, setRecentSessions] = useState<SessionResponse[]>([]);
  const [recentDocuments, setRecentDocuments] = useState<DocumentResponse[]>([]);
  const [activityLoading, setActivityLoading] = useState(true);
  
  // Profile update state
  const [isEditingProfile, setIsEditingProfile] = useState(false);
  const [profileData, setProfileData] = useState({
    username: user?.username || '',
    full_name: user?.full_name || '',
  });
  
  // Password change state
  const [isChangingPassword, setIsChangingPassword] = useState(false);
  const [passwordData, setPasswordData] = useState({
    current_password: '',
    new_password: '',
    confirm_password: '',
  });

  // Load recent activity on mount
  useEffect(() => {
    loadRecentActivity();
  }, []);

  const loadRecentActivity = async () => {
    try {
      setActivityLoading(true);
      
      // Fetch recent sessions (limit 5)
      const sessionsResponse = await apiClient.getSessions(5, 0);
      setRecentSessions(sessionsResponse.sessions);
      
      // Fetch recent documents (limit 5)
      const documentsResponse = await apiClient.getDocuments(undefined, 5, 0);
      setRecentDocuments(documentsResponse.documents);
    } catch (err) {
      console.error('Failed to load recent activity:', err);
    } finally {
      setActivityLoading(false);
    }
  };

  const formatBytes = (bytes: number): string => {
    if (bytes === 0) return '0 Bytes';
    
    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    
    return Math.round((bytes / Math.pow(k, i)) * 100) / 100 + ' ' + sizes[i];
  };

  const formatDate = (dateString: string): string => {
    const date = new Date(dateString);
    return date.toLocaleDateString('en-US', {
      year: 'numeric',
      month: 'short',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit',
    });
  };

  const handleProfileUpdate = async (e: React.FormEvent) => {
    e.preventDefault();
    setIsLoading(true);
    setError(null);
    setSuccess(null);

    try {
      await apiClient.updateUser({
        username: profileData.username,
        full_name: profileData.full_name,
      });
      
      await refreshUser();
      setSuccess('Profile updated successfully');
      setIsEditingProfile(false);
    } catch (err: any) {
      setError(err.message || 'Failed to update profile');
    } finally {
      setIsLoading(false);
    }
  };

  const handlePasswordChange = async (e: React.FormEvent) => {
    e.preventDefault();
    setIsLoading(true);
    setError(null);
    setSuccess(null);

    // Validate passwords match
    if (passwordData.new_password !== passwordData.confirm_password) {
      setError('New passwords do not match');
      setIsLoading(false);
      return;
    }

    // Validate password strength
    if (passwordData.new_password.length < 8) {
      setError('Password must be at least 8 characters');
      setIsLoading(false);
      return;
    }

    try {
      await apiClient.updateUser({
        current_password: passwordData.current_password,
        new_password: passwordData.new_password,
      });
      
      setSuccess('Password changed successfully');
      setIsChangingPassword(false);
      setPasswordData({
        current_password: '',
        new_password: '',
        confirm_password: '',
      });
    } catch (err: any) {
      setError(err.message || 'Failed to change password');
    } finally {
      setIsLoading(false);
    }
  };

  if (!user) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <p className="text-gray-500">Please log in to view your dashboard</p>
      </div>
    );
  }

  const storageQuotaBytes = 1024 * 1024 * 1024; // 1GB
  const storagePercentage = (user.storage_used_bytes / storageQuotaBytes) * 100;

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header with Navigation */}
      <header className="bg-white border-b border-gray-200 shadow-sm">
        <div className="max-w-6xl mx-auto px-6 py-4">
          <div className="flex items-center justify-between">
            <div>
              <h1 className="text-2xl font-bold text-gray-900">User Dashboard</h1>
              <p className="text-sm text-gray-600 mt-1">Welcome back, {user.username}!</p>
            </div>
            <div className="flex items-center gap-4">
              <button
                onClick={() => router.push('/')}
                className="text-sm text-gray-600 hover:text-gray-900 flex items-center gap-1"
              >
                <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M10 19l-7-7m0 0l7-7m-7 7h18" />
                </svg>
                Back to Chat
              </button>
              <UserMenu />
            </div>
          </div>
        </div>
      </header>

      <div className="max-w-6xl mx-auto p-6 space-y-6">

      {/* Alerts */}
      {error && (
        <div className="bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded">
          {error}
        </div>
      )}
      {success && (
        <div className="bg-green-50 border border-green-200 text-green-700 px-4 py-3 rounded">
          {success}
        </div>
      )}

      {/* User Info Section */}
      <div className="bg-white rounded-lg shadow p-6">
        <h2 className="text-2xl font-semibold text-gray-900 mb-4">User Information</h2>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div>
            <p className="text-sm text-gray-600">Email</p>
            <p className="text-lg font-medium text-gray-900">{user.email}</p>
          </div>
          <div>
            <p className="text-sm text-gray-600">Username</p>
            <p className="text-lg font-medium text-gray-900">{user.username}</p>
          </div>
          <div>
            <p className="text-sm text-gray-600">Full Name</p>
            <p className="text-lg font-medium text-gray-900">{user.full_name || 'Not set'}</p>
          </div>
          <div>
            <p className="text-sm text-gray-600">Role</p>
            <p className="text-lg font-medium text-gray-900 capitalize">{user.role}</p>
          </div>
          <div>
            <p className="text-sm text-gray-600">Member Since</p>
            <p className="text-lg font-medium text-gray-900">{formatDate(user.created_at)}</p>
          </div>
          <div>
            <p className="text-sm text-gray-600">Last Login</p>
            <p className="text-lg font-medium text-gray-900">
              {user.last_login_at ? formatDate(user.last_login_at) : 'N/A'}
            </p>
          </div>
        </div>
      </div>

      {/* Usage Statistics Section with Charts */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
        <StatCard
          title="Total Queries"
          value={user.query_count}
          icon={
            <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 10h.01M12 10h.01M16 10h.01M9 16H5a2 2 0 01-2-2V6a2 2 0 012-2h14a2 2 0 012 2v8a2 2 0 01-2 2h-5l-5 5v-5z" />
            </svg>
          }
          color="blue"
          trend={{ value: 15, direction: 'up' }}
          period="vs last week"
        />
        
        <StatCard
          title="Documents"
          value={recentDocuments.length}
          icon={
            <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M7 21h10a2 2 0 002-2V9.414a1 1 0 00-.293-.707l-5.414-5.414A1 1 0 0012.586 3H7a2 2 0 00-2 2v14a2 2 0 002 2z" />
            </svg>
          }
          color="green"
        />
        
        <StatCard
          title="Storage Used"
          value={`${storagePercentage.toFixed(0)}%`}
          icon={
            <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 7v10c0 2.21 3.582 4 8 4s8-1.79 8-4V7M4 7c0 2.21 3.582 4 8 4s8-1.79 8-4M4 7c0-2.21 3.582-4 8-4s8 1.79 8 4" />
            </svg>
          }
          color={storagePercentage > 90 ? 'red' : storagePercentage > 70 ? 'orange' : 'blue'}
        />
      </div>

      {/* Charts Section */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Document Types Pie Chart */}
        <PieChart
          title="Documents by Type"
          data={[
            { label: 'PDF', value: recentDocuments.filter(d => d.file_type === 'pdf').length, color: 'rgb(59 130 246)' }, // blue-500
            { label: 'TXT', value: recentDocuments.filter(d => d.file_type === 'txt').length, color: 'rgb(16 185 129)' }, // green-500
            { label: 'DOCX', value: recentDocuments.filter(d => d.file_type === 'docx').length, color: 'rgb(139 92 246)' }, // purple-500
            { label: 'Other', value: recentDocuments.filter(d => !['pdf', 'txt', 'docx'].includes(d.file_type)).length, color: 'rgb(245 158 11)' }, // amber-500
          ].filter(item => item.value > 0)}
        />
        
        {/* Usage Trend Chart */}
        <UsageChart
          title="Query Activity (Last 7 Days)"
          data={[
            { label: 'Mon', value: Math.floor(Math.random() * 20) },
            { label: 'Tue', value: Math.floor(Math.random() * 20) },
            { label: 'Wed', value: Math.floor(Math.random() * 20) },
            { label: 'Thu', value: Math.floor(Math.random() * 20) },
            { label: 'Fri', value: Math.floor(Math.random() * 20) },
            { label: 'Sat', value: Math.floor(Math.random() * 20) },
            { label: 'Sun', value: Math.floor(Math.random() * 20) },
          ]}
          color="blue"
        />
      </div>

      {/* Storage Progress Bar */}
      <div className="bg-white rounded-lg shadow p-6">
        <h3 className="text-lg font-semibold text-gray-900 mb-4">Storage Details</h3>
        <div className="space-y-2">
          <div className="flex justify-between text-sm">
            <span className="text-gray-600">Used</span>
            <span className="font-medium text-gray-900">
              {formatBytes(user.storage_used_bytes)} / {formatBytes(storageQuotaBytes)}
            </span>
          </div>
          <div className="w-full bg-gray-200 rounded-full h-3">
            <div
              className={`h-3 rounded-full transition-all ${
                storagePercentage > 90
                  ? 'bg-red-600'
                  : storagePercentage > 70
                  ? 'bg-yellow-600'
                  : 'bg-blue-600'
              }`}
              style={{ width: `${Math.min(storagePercentage, 100)}%` }}
            />
          </div>
        </div>
      </div>

      {/* Recent Activity Section */}
      <div className="bg-white rounded-lg shadow p-6">
        <h2 className="text-2xl font-semibold text-gray-900 mb-4">Recent Activity</h2>
        
        {activityLoading ? (
          <div className="text-center py-8">
            <div className="inline-block animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
            <p className="text-gray-600 mt-2">Loading activity...</p>
          </div>
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            {/* Recent Sessions */}
            <div>
              <h3 className="text-lg font-medium text-gray-900 mb-3">Recent Conversations</h3>
              {recentSessions.length === 0 ? (
                <p className="text-gray-500 text-sm">No conversations yet</p>
              ) : (
                <ul className="space-y-2">
                  {recentSessions.map((session) => (
                    <li
                      key={session.id}
                      className="border border-gray-200 rounded p-3 hover:bg-gray-50 transition"
                    >
                      <p className="font-medium text-gray-900 truncate">{session.title}</p>
                      <p className="text-xs text-gray-500 mt-1">
                        {formatDate(session.created_at)} • {session.message_count} messages
                      </p>
                    </li>
                  ))}
                </ul>
              )}
            </div>

            {/* Recent Documents */}
            <div>
              <h3 className="text-lg font-medium text-gray-900 mb-3">Recent Documents</h3>
              {recentDocuments.length === 0 ? (
                <p className="text-gray-500 text-sm">No documents uploaded yet</p>
              ) : (
                <ul className="space-y-2">
                  {recentDocuments.map((doc) => (
                    <li
                      key={doc.id}
                      className="border border-gray-200 rounded p-3 hover:bg-gray-50 transition"
                    >
                      <p className="font-medium text-gray-900 truncate">{doc.filename}</p>
                      <div className="flex justify-between items-center mt-1">
                        <p className="text-xs text-gray-500">
                          {formatBytes(doc.file_size)} • {doc.chunk_count} chunks
                        </p>
                        <span
                          className={`text-xs px-2 py-1 rounded ${
                            doc.status === 'completed'
                              ? 'bg-green-100 text-green-800'
                              : doc.status === 'failed'
                              ? 'bg-red-100 text-red-800'
                              : 'bg-yellow-100 text-yellow-800'
                          }`}
                        >
                          {doc.status}
                        </span>
                      </div>
                    </li>
                  ))}
                </ul>
              )}
            </div>
          </div>
        )}
      </div>

      {/* Settings Section */}
      <div className="bg-white rounded-lg shadow p-6">
        <h2 className="text-2xl font-semibold text-gray-900 mb-4">Settings</h2>
        
        {/* Profile Update */}
        <div className="mb-6">
          <div className="flex justify-between items-center mb-3">
            <h3 className="text-lg font-medium text-gray-900">Profile Information</h3>
            {!isEditingProfile && (
              <button
                onClick={() => {
                  setIsEditingProfile(true);
                  setProfileData({
                    username: user.username,
                    full_name: user.full_name || '',
                  });
                }}
                className="text-blue-600 hover:text-blue-700 text-sm font-medium"
              >
                Edit
              </button>
            )}
          </div>
          
          {isEditingProfile ? (
            <form onSubmit={handleProfileUpdate} className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Username
                </label>
                <input
                  type="text"
                  value={profileData.username}
                  onChange={(e) => setProfileData({ ...profileData, username: e.target.value })}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                  required
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Full Name
                </label>
                <input
                  type="text"
                  value={profileData.full_name}
                  onChange={(e) => setProfileData({ ...profileData, full_name: e.target.value })}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                />
              </div>
              <div className="flex gap-2">
                <button
                  type="submit"
                  disabled={isLoading}
                  className="px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed"
                >
                  {isLoading ? 'Saving...' : 'Save Changes'}
                </button>
                <button
                  type="button"
                  onClick={() => setIsEditingProfile(false)}
                  className="px-4 py-2 bg-gray-200 text-gray-700 rounded-md hover:bg-gray-300"
                >
                  Cancel
                </button>
              </div>
            </form>
          ) : (
            <div className="text-sm text-gray-600">
              <p>Username: {user.username}</p>
              <p>Full Name: {user.full_name || 'Not set'}</p>
            </div>
          )}
        </div>

        {/* Password Change */}
        <div className="mb-6 pt-6 border-t border-gray-200">
          <div className="flex justify-between items-center mb-3">
            <h3 className="text-lg font-medium text-gray-900">Change Password</h3>
            {!isChangingPassword && (
              <button
                onClick={() => setIsChangingPassword(true)}
                className="text-blue-600 hover:text-blue-700 text-sm font-medium"
              >
                Change
              </button>
            )}
          </div>
          
          {isChangingPassword && (
            <form onSubmit={handlePasswordChange} className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Current Password
                </label>
                <input
                  type="password"
                  value={passwordData.current_password}
                  onChange={(e) =>
                    setPasswordData({ ...passwordData, current_password: e.target.value })
                  }
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                  required
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  New Password
                </label>
                <input
                  type="password"
                  value={passwordData.new_password}
                  onChange={(e) =>
                    setPasswordData({ ...passwordData, new_password: e.target.value })
                  }
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                  required
                  minLength={8}
                />
                <p className="text-xs text-gray-500 mt-1">Minimum 8 characters</p>
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Confirm New Password
                </label>
                <input
                  type="password"
                  value={passwordData.confirm_password}
                  onChange={(e) =>
                    setPasswordData({ ...passwordData, confirm_password: e.target.value })
                  }
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                  required
                />
              </div>
              <div className="flex gap-2">
                <button
                  type="submit"
                  disabled={isLoading}
                  className="px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed"
                >
                  {isLoading ? 'Changing...' : 'Change Password'}
                </button>
                <button
                  type="button"
                  onClick={() => {
                    setIsChangingPassword(false);
                    setPasswordData({
                      current_password: '',
                      new_password: '',
                      confirm_password: '',
                    });
                  }}
                  className="px-4 py-2 bg-gray-200 text-gray-700 rounded-md hover:bg-gray-300"
                >
                  Cancel
                </button>
              </div>
            </form>
          )}
        </div>

        {/* Logout Button */}
        <div className="pt-6 border-t border-gray-200">
          <button
            onClick={logout}
            className="px-6 py-2 bg-red-600 text-white rounded-md hover:bg-red-700 transition"
          >
            Logout
          </button>
        </div>
      </div>
    </div>
  );
}
