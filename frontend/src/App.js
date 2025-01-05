import React, { useState } from 'react';
import { makeQuery, checkHealth } from './services/api';

function App() {
  const [queryResult, setQueryResult] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  const handleSubmit = async (event) => {
    event.preventDefault();
    setLoading(true);
    setError(null);

    try {
      const data = {
        type: 'procedure',
        patientInfo: {
          age: 45,
          weight: '70kg',
          medicalHistory: 'Hypertension',
          currentMedications: ['Lisinopril'],
          allergies: ['Penicillin'],
          vitals: {
            bp: '120/80',
            pulse: 72
          }
        }
      };

      const result = await makeQuery(data);
      setQueryResult(result);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="App">
      <header className="App-header">
        <h1>Medical Provider Assistant</h1>
      </header>
      <main>
        <button onClick={handleSubmit} disabled={loading}>
          {loading ? 'Processing...' : 'Make Query'}
        </button>
        
        {error && <div className="error">{error}</div>}
        
        {queryResult && (
          <div className="results">
            <h2>Results:</h2>
            <pre>{JSON.stringify(queryResult, null, 2)}</pre>
          </div>
        )}
      </main>
    </div>
  );
}

export default App; 