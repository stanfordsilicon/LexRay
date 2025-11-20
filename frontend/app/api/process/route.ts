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
  
  // Add timeout for batch processing (90 seconds for Render free tier)
  const controller = new AbortController();
  const timeoutId = setTimeout(() => controller.abort(), 90000); // 90 second timeout
  
  try {
    const response = await fetch(`${backendUrl}/api/process`, {
      method: 'POST',
      body: formData,
      signal: controller.signal,
    });
    
    clearTimeout(timeoutId);
    
    if (!response.ok) {
      const errorText = await response.text();
      console.error('Backend API error:', response.status, errorText);
      throw new Error(`Backend API error: ${response.status} - ${errorText}`);
    }
    
    return await response.json();
  } catch (error) {
    clearTimeout(timeoutId);
    console.error('Backend API call failed:', error);
    if (error instanceof Error && error.name === 'AbortError') {
      return { 
        error: 'Request timed out. The batch processing is taking too long. Please try with a smaller file or check the backend logs.' 
      };
    }
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
      if ("error" in result && typeof result.error === "string" && result.error.length > 0) {
        return NextResponse.json({ error: "Invalid input. Please re-enter." }, { status: 400 });
      }
      return NextResponse.json(result);
    }

    // Fallback
    return NextResponse.json({ error: "Unsupported content type" }, { status: 400 });
  } catch (e: any) {
    return NextResponse.json({ error: "Invalid input. Please re-enter." }, { status: 400 });
  }
}


