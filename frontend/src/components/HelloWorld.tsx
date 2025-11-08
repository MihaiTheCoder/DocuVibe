import React, { useEffect, useState } from 'react';

interface HealthResponse {
  message: string;
  timestamp: string;
  status: string;
}

export const HelloWorld: React.FC = () => {
  const [data, setData] = useState<HealthResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    fetch(`${import.meta.env.VITE_API_URL}/`)
      .then(res => res.json())
      .then(data => {
        setData(data);
        setLoading(false);
      })
      .catch(err => {
        setError(err.message);
        setLoading(false);
      });
  }, []);

  if (loading) return <div>Loading...</div>;
  if (error) return <div>Error: {error}</div>;

  return (
    <div className="p-8">
      <h1 className="text-3xl font-bold mb-4">VibeDocs - Hello World</h1>
      {data && (
        <div className="bg-gray-100 p-4 rounded">
          <p className="mb-2">Message: {data.message}</p>
          <p className="mb-2">Status: {data.status}</p>
          <p>Timestamp: {data.timestamp}</p>
        </div>
      )}
    </div>
  );
};
