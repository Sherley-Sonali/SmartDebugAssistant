import React, { useState, useEffect } from 'react';
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer, PieChart, Pie, Cell } from 'recharts';

const COLORS = ['#0088FE', '#00C49F', '#FFBB28', '#FF8042', '#8884d8', '#82ca9d', '#ffc658', '#8dd1e1', '#a4de6c', '#d0ed57'];

const ErrorDashboard = () => {
  const [globalData, setGlobalData] = useState({ total_errors: 0, top_errors: [], time_period: 'all' });
  const [userData, setUserData] = useState({ total_errors: 0, top_errors: [], time_period: 'all' });
  const [resources, setResources] = useState([]);
  const [loading, setLoading] = useState(true);
  const [userId, setUserId] = useState('current-user');
  const [timePeriod, setTimePeriod] = useState('week');

  // Mock API call - in a real app, this would fetch from your FastAPI backend
  useEffect(() => {
    // Simulate loading data
    setTimeout(() => {
      const mockGlobalData = {
        total_errors: 1526,
        top_errors: [
          { error_type: 'SyntaxError', count: 432, percentage: 28.31 },
          { error_type: 'NameError', count: 287, percentage: 18.81 },
          { error_type: 'TypeError', count: 215, percentage: 14.09 },
          { error_type: 'IndexError', count: 176, percentage: 11.53 },
          { error_type: 'ImportError', count: 123, percentage: 8.06 }
        ],
        time_period: 'week'
      };
      
      const mockUserData = {
        total_errors: 47,
        top_errors: [
          { error_type: 'NameError', count: 18, percentage: 38.30 },
          { error_type: 'SyntaxError', count: 12, percentage: 25.53 },
          { error_type: 'IndexError', count: 9, percentage: 19.15 },
          { error_type: 'KeyError', count: 5, percentage: 10.64 },
          { error_type: 'ValueError', count: 3, percentage: 6.38 }
        ],
        time_period: 'week'
      };
      
      const mockResources = [
        {
          error_type: 'NameError',
          resource: {
            title: 'Understanding Variable Scope in Python',
            url: 'https://realpython.com/python-scope-legb-rule/'
          }
        },
        {
          error_type: 'SyntaxError',
          resource: {
            title: 'Common Python Syntax Errors',
            url: 'https://realpython.com/invalid-syntax-python/'
          }
        },
        {
          error_type: 'IndexError',
          resource: {
            title: 'Working with Indices in Python',
            url: 'https://docs.python.org/3/tutorial/introduction.html#lists'
          }
        }
      ];
      
      setGlobalData(mockGlobalData);
      setUserData(mockUserData);
      setResources(mockResources);
      setLoading(false);
    }, 1000);
  }, [timePeriod]);

  const handleTimePeriodChange = (e) => {
    setTimePeriod(e.target.value);
    setLoading(true);
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="text-lg font-medium">Loading dashboard data...</div>
      </div>
    );
  }

  return (
    <div className="bg-white rounded-lg shadow p-6">
      <div className="flex justify-between items-center mb-6">
        <h2 className="text-2xl font-bold text-gray-800">Error Analytics Dashboard</h2>
        <div className="flex items-center">
          <label htmlFor="time-period" className="mr-2 text-gray-700">Time Period:</label>
          <select 
            id="time-period"
            value={timePeriod}
            onChange={handleTimePeriodChange}
            className="border rounded p-1 text-gray-700"
          >
            <option value="day">Last 24 Hours</option>
            <option value="week">Last 7 Days</option>
            <option value="month">Last 30 Days</option>
            <option value="all">All Time</option>
          </select>
        </div>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        {/* Global Error Distribution */}
        <div className="bg-gray-50 p-4 rounded-lg shadow-sm">
          <h3 className="text-lg font-medium text-gray-800 mb-4">Global Error Distribution</h3>
          <div className="h-64">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart
                data={globalData.top_errors}
                margin={{ top: 5, right: 30, left: 20, bottom: 60 }}
              >
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis dataKey="error_type" angle={-45} textAnchor="end" />
                <YAxis />
                <Tooltip formatter={(value) => [`${value} errors`, 'Count']} />
                <Legend />
                <Bar dataKey="count" fill="#0088FE" name="Error Count" />
              </BarChart>
            </ResponsiveContainer>
          </div>
          <div className="text-sm text-gray-600 mt-2">
            Total errors: {globalData.total_errors}
          </div>
        </div>

        {/* User Error Distribution */}
        <div className="bg-gray-50 p-4 rounded-lg shadow-sm">
          <h3 className="text-lg font-medium text-gray-800 mb-4">Your Error Distribution</h3>
          <div className="h-64">
            <ResponsiveContainer width="100%" height="100%">
              <PieChart>
                <Pie
                  data={userData.top_errors}
                  cx="50%"
                  cy="50%"
                  labelLine={true}
                  label={({ name, percent }) => `${name}: ${(percent * 100).toFixed(0)}%`}
                  outerRadius={80}
                  fill="#8884d8"
                  dataKey="count"
                  nameKey="error_type"
                >
                  {userData.top_errors.map((entry, index) => (
                    <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                  ))}
                </Pie>
                <Tooltip formatter={(value) => [`${value} errors`, 'Count']} />
              </PieChart>
            </ResponsiveContainer>
          </div>
          <div className="text-sm text-gray-600 mt-2">
            Your total errors: {userData.total_errors}
          </div>
        </div>
      </div>

      {/* Recommended Resources */}
      <div className="mt-8">
        <h3 className="text-lg font-medium text-gray-800 mb-4">Recommended Resources</h3>
        <div className="bg-gray-50 p-4 rounded-lg shadow-sm">
          <ul className="divide-y divide-gray-200">
            {resources.map((item, index) => (
              <li key={index} className="py-3">
                <div className="flex items-start">
                  <div className="bg-blue-100 text-blue-800 px-2 py-1 rounded text-sm font-medium mr-3">
                    {item.error_type}
                  </div>
                  <div>
                    <a 
                      href={item.resource.url} 
                      target="_blank"
                      rel="noopener noreferrer"
                      className="text-blue-600 hover:underline font-medium"
                    >
                      {item.resource.title}
                    </a>
                    <p className="text-sm text-gray-600 mt-1">
                      Recommended based on your error patterns
                    </p>
                  </div>
                </div>
              </li>
            ))}
          </ul>
        </div>
      </div>
    </div>
  );
};

export default ErrorDashboard;