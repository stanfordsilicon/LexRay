import { NextResponse } from "next/server";

// Get the backend URL from environment variables
const getBackendUrl = () => {
  // In production, use the deployed backend URL
  if (process.env.NODE_ENV === 'production') {
    return process.env.BACKEND_URL || 'https://lexray.onrender.com';
  }
  // In development, use local backend
  return process.env.BACKEND_URL || 'http://localhost:8000';
};

// GET /api/languages → returns list of languages from backend API
export async function GET() {
  try {
    const backendUrl = getBackendUrl();
    
    const response = await fetch(`${backendUrl}/api/languages`, {
      method: 'GET',
      headers: {
        'Content-Type': 'application/json',
      },
    });
    
    if (!response.ok) {
      throw new Error(`Backend API error: ${response.status}`);
    }
    
    const data = await response.json();
    return NextResponse.json(data);
  } catch (error) {
    console.error('Backend API call failed:', error);
    return NextResponse.json(
      { languages: [], error: "Could not fetch languages from backend" },
      { status: 200 }
    );
  }
}


