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

async function callBackendAPI(formData: FormData) {
  const backendUrl = getBackendUrl();
  
  try {
    const response = await fetch(`${backendUrl}/api/process`, {
      method: 'POST',
      body: formData,
    });
    
    if (!response.ok) {
      throw new Error(`Backend API error: ${response.status}`);
    }
    
    return await response.json();
  } catch (error) {
    console.error('Backend API call failed:', error);
    return { 
      error: `Backend API unavailable: ${error instanceof Error ? error.message : 'Unknown error'}` 
    };
  }
}

export async function POST(req: Request) {
  try {
    const contentType = req.headers.get("content-type") || "";

    if (contentType.includes("multipart/form-data")) {
      const form = await req.formData();
      
      // Forward the request to the backend API
      const result = await callBackendAPI(form);
      return NextResponse.json(result);
    }

    // Fallback
    return NextResponse.json({ error: "Unsupported content type" }, { status: 400 });
  } catch (e: any) {
    return NextResponse.json({ error: e?.message || String(e) }, { status: 500 });
  }
}


