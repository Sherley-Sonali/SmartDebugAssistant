import React, { useState } from 'react';
import CodeHighlight from '@uiw/react-prismjs';
import 'prismjs/themes/prism.css';
import '../../node_modules/prismjs/themes/prism-tomorrow.css';

const ErrorAnalyzer = () => {
  const [errorInput, setErrorInput] = useState('');
  const [codeContext, setCodeContext] = useState('');
  const [analysis, setAnalysis] = useState(null);
  const [loading, setLoading] = useState(false);
  const [language, setLanguage] = useState('python');
  const [projectId, setProjectId] = useState(''); // Optional project ID for tracking

  const analyzeError = async () => {
    setLoading(true);
    try {
      const response = await fetch('http://localhost:8000/analyze_error', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          error_message: errorInput,
          code_context: codeContext,
          language: language,
          project_id: projectId || undefined
        }),
      });
      
      if (!response.ok) {
        throw new Error('Error analyzing code');
      }
      
      const data = await response.json();
      setAnalysis(data);
      console.log('API Response:', data); // For debugging
    } catch (error) {
      console.error('Error:', error);
      alert('Failed to analyze error. Please try again.');
    }
    setLoading(false);
  };

  return (
    <div className="container mx-auto p-4 max-w-4xl">
      <div className="bg-white shadow-md rounded-lg p-6 mb-8">
        <h1 className="text-2xl font-bold mb-6 text-center text-blue-600">SmartDebug Assistant</h1>
        <h2 className="text-lg mb-4 text-center text-gray-600">Context-Aware Error Resolution</h2>
        
        <div className="space-y-6">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Error Message *
            </label>
            <textarea
              className="w-full p-3 border border-gray-300 rounded-md h-32 focus:outline-none focus:ring-2 focus:ring-blue-500"
              value={errorInput}
              onChange={(e) => setErrorInput(e.target.value)}
              placeholder="Paste your error message here..."
              required
            />
          </div>
          
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Code Context (Optional)
            </label>
            <textarea
              className="w-full p-3 border border-gray-300 rounded-md h-32 font-mono focus:outline-none focus:ring-2 focus:ring-blue-500"
              value={codeContext}
              onChange={(e) => setCodeContext(e.target.value)}
              placeholder="Paste the relevant code snippet here..."
            />
          </div>
          
          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Language
              </label>
              <select
                className="w-full p-3 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                value={language}
                onChange={(e) => setLanguage(e.target.value)}
              >
                <option value="python">Python</option>
                <option value="javascript">JavaScript</option>
                <option value="java">Java</option>
                <option value="csharp">C#</option>
              </select>
            </div>
            
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Project ID (Optional)
              </label>
              <input
                type="text"
                className="w-full p-3 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                value={projectId}
                onChange={(e) => setProjectId(e.target.value)}
                placeholder="For tracking error patterns"
              />
            </div>
          </div>
          
          <button
            className="w-full px-4 py-3 bg-blue-600 text-white rounded-md hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-blue-500 transition"
            onClick={analyzeError}
            disabled={loading || !errorInput.trim()}
          >
            {loading ? 'Analyzing...' : 'Analyze Error'}
          </button>
        </div>
      </div>

      {analysis && (
        <div className="bg-white shadow-md rounded-lg p-6">
          <h2 className="text-xl font-bold mb-6 text-center">Analysis Results</h2>
          
          <div className="space-y-8">
            <div>
              <h3 className="text-lg font-semibold mb-2">Error Type</h3>
              <p className="px-3 py-2 bg-red-100 text-red-800 rounded-md inline-block font-medium">{analysis.error_type}</p>
            </div>
            
            <div>
              <h3 className="text-lg font-semibold mb-2">Solutions</h3>
              {analysis.solutions.map((solution, index) => (
                <div key={index} className="mt-4 p-4 bg-gray-50 rounded-md border-l-4 border-green-500">
                  <p className="font-medium text-green-700 mb-2">Fix: {solution.fix}</p>
                  <p className="mb-3 text-gray-700">Explanation: {solution.explanation}</p>
                  <div className="rounded-md overflow-hidden">
                    <pre className="language-python">
                      <code>{solution.code_example}</code>
                    </pre>
                  </div>

                  <p className="mt-2 text-sm text-gray-500 flex items-center">
                    <span className="mr-1">Confidence:</span>
                    <div className="w-24 h-2 bg-gray-200 rounded-full overflow-hidden">
                      <div 
                        className="h-full bg-green-500"
                        style={{ width: `${solution.confidence * 100}%` }}
                      ></div>
                    </div>
                    <span className="ml-2">{(solution.confidence * 100).toFixed(0)}%</span>
                  </p>
                </div>
              ))}
            </div>

            {/* NEW: Learning Resources Section from Gemini */}
            {analysis.learning_resources && analysis.learning_resources.length > 0 && (
              <div>
                <h3 className="text-lg font-semibold mb-3">Learning Resources</h3>
                <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                  {analysis.learning_resources.map((resource, index) => (
                    <div key={index} className="p-4 bg-blue-50 rounded-md border border-blue-200">
                      <div className="text-xs uppercase tracking-wider text-blue-600 mb-1">
                        {resource.resource_type}
                      </div>
                      <h4 className="font-medium text-lg mb-2">{resource.title}</h4>
                      <p className="text-sm text-gray-700 mb-3">{resource.description}</p>
                      {resource.url && (
                        <a 
                          href={resource.url} 
                          target="_blank" 
                          rel="noopener noreferrer"
                          className="text-blue-600 hover:text-blue-800 text-sm font-medium"
                        >
                          Visit Resource →
                        </a>
                      )}
                    </div>
                  ))}
                </div>
              </div>
            )}

            {/* NEW: Error Statistics Section from Gemini */}
            {analysis.statistics && (
              <div>
                <h3 className="text-lg font-semibold mb-3">Error Statistics</h3>
                <div className="p-4 bg-gray-50 rounded-md border border-gray-200">
                  {analysis.statistics.frequency !== null && (
                    <div className="mb-3">
                      <span className="font-medium">Frequency:</span> 
                      <span className="ml-2">{analysis.statistics.frequency} occurrence(s) in this project</span>
                    </div>
                  )}
                  
                  {analysis.statistics.last_occurrence && (
                    <div className="mb-3">
                      <span className="font-medium">Last Occurrence:</span>
                      <span className="ml-2">{new Date(analysis.statistics.last_occurrence).toLocaleString()}</span>
                    </div>
                  )}
                  
                  {analysis.statistics.common_contexts && analysis.statistics.common_contexts.length > 0 && (
                    <div className="mb-3">
                      <span className="font-medium block mb-1">Common Contexts:</span>
                      <ul className="list-disc pl-5 text-sm text-gray-700">
                        {analysis.statistics.common_contexts.map((context, index) => (
                          <li key={index}>{context}</li>
                        ))}
                      </ul>
                    </div>
                  )}
                  
                  {analysis.statistics.related_errors && analysis.statistics.related_errors.length > 0 && (
                    <div>
                      <span className="font-medium block mb-1">Related Errors:</span>
                      <div className="flex flex-wrap gap-2">
                        {analysis.statistics.related_errors.map((error, index) => (
                          <span 
                            key={index}
                            className="px-2 py-1 bg-red-50 text-red-700 rounded-md text-sm border border-red-200"
                          >
                            {error}
                          </span>
                        ))}
                      </div>
                    </div>
                  )}
                </div>
              </div>
            )}

            <div>
              <h3 className="text-lg font-semibold mb-2">Related Concepts</h3>
              <div className="flex flex-wrap gap-2">
                {analysis.concepts.map((concept, index) => (
                  <span 
                    key={index}
                    className="px-3 py-1 bg-blue-100 text-blue-800 rounded-full text-sm"
                  >
                    {concept}
                  </span>
                ))}
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default ErrorAnalyzer;