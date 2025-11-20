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
    
    const jsonData = await response.json();
    console.log("Backend response received:", { 
      success: jsonData.success, 
      hasCsvContent: !!jsonData.csv_content,
      csvContentLength: jsonData.csv_content?.length || 0
    });
    return jsonData;
  } catch (error) {
    clearTimeout(timeoutId);
    console.error('Backend API call failed:', error);
    if (error instanceof Error && error.name === 'AbortError') {
      return { 
        error: 'Request timed out. The batch processing is taking too long. Please try with a smaller file or check the backend logs.',
        success: false
      };
    }
    return { 
      error: `Backend API unavailable: ${error instanceof Error ? error.message : 'Unknown error'}`,
      success: false
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
      
      // Log the result for debugging
      console.log("Backend API result:", JSON.stringify(result).substring(0, 200));
      
      // Only return error if there's actually an error field and no success
      if ("error" in result && typeof result.error === "string" && result.error.length > 0 && !result.success) {
        console.error("Backend returned error:", result.error);
        return NextResponse.json({ error: result.error || "Invalid input. Please re-enter." }, { status: 400 });
      }
      
      // If we have success or csv_content, return the result
      if (result.success || result.csv_content) {
        return NextResponse.json(result);
      }
      
      // Fallback error
      console.error("Unexpected result format:", result);
      return NextResponse.json({ error: "Invalid response from backend" }, { status: 500 });
    }

    // Fallback
    return NextResponse.json({ error: "Unsupported content type" }, { status: 400 });
  } catch (e: any) {
    console.error("Error in POST handler:", e);
    return NextResponse.json({ error: e?.message || "Invalid input. Please re-enter." }, { status: 400 });
  }
}


